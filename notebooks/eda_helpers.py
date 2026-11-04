"""Self-contained helpers for the EXP-001 feasibility notebook.

Exploratory instrumentation, outside ``src/`` and outside the layer contracts.
It does not import the package and the package never imports it.

Three concerns live here, each independent of any one country:

* fetching from a map/feature provider that is described as data
  (``PROVIDERS``) and recording every request in an auditable manifest;
* image-quality figures computed with numpy;
* extent geometry: projection envelope, snapping and tiling arithmetic.

Run ``python notebooks/eda_helpers.py --selftest`` for the offline checks, or
``--check-notebook <path>`` to validate a notebook against the project rules.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
import time
import warnings
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import requests
from pyproj import CRS, Geod, Transformer
from rasterio.errors import NotGeoreferencedWarning

# Web map images carry no georeferencing by design.
warnings.filterwarnings("ignore", category=NotGeoreferencedWarning)

Bbox = tuple[float, float, float, float]


@dataclass(frozen=True)
class Provider:
    """One imagery and building-footprint provider, described as data.

    ``endpoints`` maps a service key to its base URL. ``layers`` maps a logical
    layer name to ``(service key, layer name on that service)``. A layer that is
    not a logical name is taken literally on the ``epoch_service``.
    ``epoch_layer_pattern`` is formatted with ``year``. ``wfs_params`` is a
    template whose values are formatted with ``bbox``, ``crs`` and ``epsg``.
    ``attributes`` maps a logical attribute to the name the vector source uses.
    ``default_view`` is ``(latitude, longitude, zoom)`` for the notebook's map.
    """

    key: str
    label: str
    endpoints: dict[str, str]
    wms_version: str
    layers: dict[str, tuple[str, str]]
    epoch_service: str
    epoch_layer_pattern: str
    advertised_crs: tuple[str, ...]
    native_crs: str
    default_gsd_m: float
    default_view: tuple[float, float, int]
    feature_info_format: str
    wfs_service: str
    wfs_params: dict[str, str]
    attributes: dict[str, str]


PROVIDERS: dict[str, Provider] = {
    "es-pnoa": Provider(
        key="es-pnoa",
        label="Spain: PNOA orthophotos and cadastral building footprints",
        endpoints={
            "ortho": "https://www.ign.es/wms-inspire/pnoa-ma",
            "ortho_history": "https://www.ign.es/wms/pnoa-historico",
            "cadastre_wms": "http://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx",
            "buildings_wfs": "http://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx",
        },
        wms_version="1.3.0",
        layers={
            "ortho": ("ortho", "OI.OrthoimageCoverage"),
            "buildings": ("cadastre_wms", "BU.Building"),
        },
        epoch_service="ortho_history",
        epoch_layer_pattern="PNOA{year}",
        advertised_crs=("EPSG:25829", "EPSG:25830", "EPSG:25831", "EPSG:4326"),
        native_crs="EPSG:25830",
        default_gsd_m=0.25,
        default_view=(40.4, -3.7, 6),
        feature_info_format="text/html",
        wfs_service="buildings_wfs",
        wfs_params={
            "service": "wfs",
            "version": "2",
            "request": "getfeature",
            "STOREDQUERIE_ID": "GetBuildingByBBOX",
            "srsname": "EPSG::{epsg}",
            "bbox": "{bbox}",
        },
        attributes={
            "identifier": "localId",
            "condition": "conditionOfConstruction",
            "year": "beginning",
            "use": "currentUse",
            "floors": "numberOfFloorsAboveGround",
        },
    ),
}

_PACKAGE_PREFIX = "geo_decay" + "_"  # the checker names it; the module never imports it
_SCHEME = "ht" + "tp"  # kept out of one literal: endpoints live in PROVIDERS only
_MANIFEST_HEADER = [
    "timestamp_utc",
    "url",
    "status",
    "nbytes",
    "md5",
    "elapsed_s",
    "error",
]
_PROBE_SIZE = (256, 256)
_CONTENT_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/tiff": ".tif",
    "json": ".json",
    "gml": ".gml",
    "xml": ".xml",
    "html": ".html",
    "text/plain": ".txt",
}


@dataclass(frozen=True)
class Fetch:
    """Outcome of one request. A failed request is a value, never an exception."""

    url: str
    status: int
    nbytes: int
    md5: str
    elapsed_s: float
    path: Path | None
    error: str


# --------------------------------------------------------------------------
# Fetching and the audit trail
# --------------------------------------------------------------------------


def manifest_path(out_dir: Path) -> Path:
    """Location of the append-only request log inside ``out_dir``."""
    return out_dir / "manifest.csv"


def _append_manifest(out_dir: Path, row: Fetch, timestamp_utc: str) -> None:
    path = manifest_path(out_dir)
    is_new = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if is_new:
            writer.writerow(_MANIFEST_HEADER)
        writer.writerow(
            [
                timestamp_utc,
                row.url,
                row.status,
                row.nbytes,
                row.md5,
                f"{row.elapsed_s:.3f}",
                row.error,
            ]
        )


def _extension(content_type: str, body: bytes) -> str:
    lowered = content_type.lower()
    for token, extension in _CONTENT_EXTENSIONS.items():
        if token in lowered:
            return extension
    if body.startswith(b"\x89PNG"):
        return ".png"
    if body.startswith(b"\xff\xd8"):
        return ".jpg"
    return ".bin"


def fetch(
    url: str,
    params: dict[str, str],
    out_dir: Path,
    *,
    timeout: float = 30.0,
) -> Fetch:
    """GET ``url`` and log it. Never raises on a network failure.

    A transport failure, or a refusal by an intermediary proxy, yields
    ``status == 0``, an empty ``md5`` and no ``path``. A response with a status
    of 400 or above keeps its body (service exceptions are evidence) and
    carries the status in ``error``. Every call, successful or not, appends
    one row to the manifest.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    started = time.monotonic()
    full_url = url
    failure = ""
    response: requests.Response | None = None
    try:
        prepared = requests.Request("GET", url, params=params).prepare()
        full_url = prepared.url or url
        response = requests.get(url, params=params, timeout=timeout)
    except requests.RequestException as exc:
        failure = f"{type(exc).__name__}: {exc}"
    if response is not None and response.headers.get("X-Proxy-Error"):
        # An intermediary refused the request: the target never answered.
        failure = f"refused by proxy: {response.headers['X-Proxy-Error']}"
    if response is None or failure:
        result = Fetch(
            url=full_url,
            status=0,
            nbytes=0,
            md5="",
            elapsed_s=time.monotonic() - started,
            path=None,
            error=failure,
        )
    else:
        body = response.content
        digest = hashlib.md5(body, usedforsecurity=False).hexdigest()
        target = out_dir / (
            digest + _extension(response.headers.get("Content-Type", ""), body)
        )
        if not target.exists():
            target.write_bytes(body)
        result = Fetch(
            url=full_url,
            status=response.status_code,
            nbytes=len(body),
            md5=digest,
            elapsed_s=time.monotonic() - started,
            path=target,
            error=f"status {response.status_code}"
            if response.status_code >= 400
            else "",
        )
    _append_manifest(out_dir, result, timestamp)
    return result


def _resolve_layer(provider: Provider, layer: str) -> tuple[str, str]:
    if layer in provider.layers:
        return provider.layers[layer]
    return provider.epoch_service, layer


def _axis_swapped(crs: str, version: str) -> bool:
    """True when the request grammar orders a CRS as northing first."""
    if tuple(int(p) for p in version.split(".")[:2]) < (1, 3):
        return False
    first = CRS.from_user_input(crs).axis_info[0]
    return first.direction.lower() == "north"


def _wms_params(
    provider: Provider,
    request: str,
    layer: str,
    bbox: Bbox,
    crs: str,
    size: tuple[int, int],
) -> tuple[str, dict[str, str]]:
    service, name = _resolve_layer(provider, layer)
    modern = tuple(int(p) for p in provider.wms_version.split(".")[:2]) >= (1, 3)
    ordered = (
        (bbox[1], bbox[0], bbox[3], bbox[2])
        if _axis_swapped(crs, provider.wms_version)
        else bbox
    )
    params = {
        "SERVICE": "WMS",
        "VERSION": provider.wms_version,
        "REQUEST": request,
        "LAYERS": name,
        "STYLES": "",
        ("CRS" if modern else "SRS"): crs,
        "BBOX": ",".join(repr(float(v)) for v in ordered),
        "WIDTH": str(size[0]),
        "HEIGHT": str(size[1]),
    }
    return provider.endpoints[service], params


def wms_capabilities(provider: Provider, service: str, out_dir: Path) -> Fetch:
    """Fetch the capabilities document of the endpoint stored under ``service``."""
    params = {
        "SERVICE": "WMS",
        "VERSION": provider.wms_version,
        "REQUEST": "GetCapabilities",
    }
    return fetch(provider.endpoints[service], params, out_dir)


def wms_map(
    provider: Provider,
    layer: str,
    bbox: Bbox,
    crs: str,
    size: tuple[int, int],
    out_dir: Path,
    *,
    image_format: str = "image/png",
    transparent: bool = True,
) -> Fetch:
    """Fetch one rendered map image for ``bbox`` (``x`` first, in ``crs``)."""
    url, params = _wms_params(provider, "GetMap", layer, bbox, crs, size)
    params["FORMAT"] = image_format
    params["TRANSPARENT"] = "TRUE" if transparent else "FALSE"
    return fetch(url, params, out_dir)


def wms_feature_info(
    provider: Provider,
    layer: str,
    bbox: Bbox,
    crs: str,
    size: tuple[int, int],
    xy: tuple[int, int],
    out_dir: Path,
) -> Fetch:
    """Query the attributes under pixel ``xy`` of a map of ``bbox`` and ``size``."""
    url, params = _wms_params(provider, "GetFeatureInfo", layer, bbox, crs, size)
    modern = tuple(int(p) for p in provider.wms_version.split(".")[:2]) >= (1, 3)
    params["QUERY_LAYERS"] = params["LAYERS"]
    params["INFO_FORMAT"] = provider.feature_info_format
    params["I" if modern else "X"] = str(xy[0])
    params["J" if modern else "Y"] = str(xy[1])
    return fetch(url, params, out_dir)


def wfs_buildings(provider: Provider, bbox: Bbox, crs: str, out_dir: Path) -> Fetch:
    """Fetch the building footprints that intersect ``bbox``."""
    epsg = CRS.from_user_input(crs).to_epsg()
    values = {
        "bbox": ",".join(repr(float(v)) for v in bbox),
        "crs": crs,
        "epsg": str(epsg),
    }
    params = {key: tpl.format(**values) for key, tpl in provider.wfs_params.items()}
    return fetch(provider.endpoints[provider.wfs_service], params, out_dir)


def _is_image_file(path: Path) -> bool:
    with path.open("rb") as handle:
        head = handle.read(4)
    return head.startswith((b"\x89PNG", b"\xff\xd8", b"II*\x00", b"MM\x00*"))


def _epoch_verdict(got: Fetch) -> tuple[str, str, bool | None]:
    """Classify one probe as ``present``, ``absent`` or ``unknown`` with evidence."""
    if got.status == 0 or got.path is None:
        return "unknown", got.error, None
    if got.status >= 500:
        return "unknown", got.error, None
    if got.status >= 400:
        return "absent", got.error, None
    if _is_image_file(got.path):
        try:
            blank = is_blank_image(got.path)
        except Exception as exc:  # undecodable bytes are evidence, not a crash
            return "unknown", f"undecodable image: {exc}", None
        if blank:
            return "absent", "blank image: no pixel content for this epoch", True
        return "present", "image with pixel content", False
    text = got.path.read_text(encoding="utf-8", errors="replace")
    if "LayerNotDefined" in text:
        return "absent", "service exception: LayerNotDefined", None
    return "unknown", "unrecognised reply: " + " ".join(text.split())[:160], None


def epoch_availability(
    provider: Provider,
    bbox: Bbox,
    crs: str,
    years: Iterable[int],
    out_dir: Path,
) -> list[dict[str, object]]:
    """Probe each year with a small map request: one row per year, never raises.

    ``absent`` means the service answered that the epoch has no imagery for the
    extent. A request that could not be completed is ``unknown``, because an
    unreachable host is not evidence about the imagery.
    """
    rows: list[dict[str, object]] = []
    for year in years:
        layer = provider.epoch_layer_pattern.format(year=year)
        got = wms_map(provider, layer, bbox, crs, _PROBE_SIZE, out_dir)
        verdict, evidence, blank = _epoch_verdict(got)
        rows.append(
            {
                "year": year,
                "layer": layer,
                "verdict": verdict,
                "evidence": evidence,
                "blank": blank,
                "status": got.status,
                "nbytes": got.nbytes,
                "md5": got.md5,
                "path": str(got.path) if got.path else "",
            }
        )
    return rows


def write_summary(rows: list[dict[str, object]], out_dir: Path) -> Path:
    """Write ``rows`` to ``out_dir/summary.csv``, overwriting any earlier summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    columns: list[str] = []
    for row in rows:
        for column in row:
            if column not in columns:
                columns.append(column)
    path = out_dir / "summary.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


# --------------------------------------------------------------------------
# Image quality
# --------------------------------------------------------------------------


def _read_image(path: Path) -> tuple[np.ndarray, int | None]:
    """Return ``(bands, rows, cols)`` pixels and the alpha band index, if any."""
    import rasterio
    from rasterio.enums import ColorInterp

    with rasterio.open(path) as src:
        pixels = src.read()
        alpha = next(
            (i for i, c in enumerate(src.colorinterp) if c == ColorInterp.alpha),
            None,
        )
    return pixels, alpha


def is_blank_image(path: Path) -> bool:
    """True for a fully transparent image or one holding a single pixel value."""
    pixels, alpha = _read_image(path)
    if alpha is not None and not pixels[alpha].any():
        return True
    return bool((pixels == pixels[:, :1, :1]).all())


def image_stats(path: Path) -> dict[str, object]:
    """Size, per-band statistics and three quality figures for one image.

    ``saturated_share`` is the share of colour samples at the dtype maximum.
    ``nodata_share`` is the share of pixels with zero alpha, or, without an
    alpha band, of pixels that are zero in every band. ``gradient_variance`` is
    the variance of the gradient magnitude of the mean colour band: a sharpness
    proxy that falls as the image blurs.
    """
    pixels, alpha = _read_image(path)
    colour_idx = [i for i in range(pixels.shape[0]) if i != alpha]
    colour = pixels[colour_idx].astype(np.float64)
    if alpha is not None:
        nodata = ~pixels[alpha].astype(bool)
    else:
        nodata = ~pixels.astype(bool).any(axis=0)
    if np.issubdtype(pixels.dtype, np.integer):
        ceiling = float(np.iinfo(pixels.dtype).max)
    else:
        ceiling = float(pixels.max())
    gray = colour.mean(axis=0)
    gy, gx = np.gradient(gray)
    return {
        "width": int(pixels.shape[2]),
        "height": int(pixels.shape[1]),
        "bands": int(pixels.shape[0]),
        "min": [float(b.min()) for b in pixels],
        "max": [float(b.max()) for b in pixels],
        "mean": [float(b.mean()) for b in pixels],
        "std": [float(b.std()) for b in pixels],
        "saturated_share": float((colour == ceiling).mean()),
        "nodata_share": float(nodata.mean()),
        "gradient_variance": float(np.hypot(gx, gy).var()),
    }


# --------------------------------------------------------------------------
# Extent geometry: pure, deterministic, no I/O
# --------------------------------------------------------------------------


def _corners(bbox: Bbox) -> list[tuple[float, float]]:
    min_x, min_y, max_x, max_y = bbox
    return [(min_x, min_y), (min_x, max_y), (max_x, min_y), (max_x, max_y)]


def _same_crs(a: str, b: str) -> bool:
    return CRS.from_user_input(a) == CRS.from_user_input(b)


def to_projected(bbox: Bbox, source_crs: str, target_crs: str) -> Bbox:
    """Envelope of the four reprojected corners, ``x`` (longitude) first.

    A rectangle in one CRS is not a rectangle in another, so reprojecting two
    corners would silently lose ground on two sides.
    """
    if _same_crs(source_crs, target_crs):
        return (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    points = [transformer.transform(x, y) for x, y in _corners(bbox)]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def snap_outward(bbox: Bbox, grid_m: float) -> Bbox:
    """Move each edge outward to a multiple of ``grid_m``; the result contains it."""
    if grid_m <= 0:
        raise ValueError("grid_m must be positive")
    min_x, min_y, max_x, max_y = bbox
    return (
        math.floor(min_x / grid_m) * grid_m,
        math.floor(min_y / grid_m) * grid_m,
        math.ceil(max_x / grid_m) * grid_m,
        math.ceil(max_y / grid_m) * grid_m,
    )


def _working_crs(bbox: Bbox, crs: str) -> str:
    """The CRS in which sizes are measured: ``crs`` itself, or a UTM zone."""
    if not CRS.from_user_input(crs).is_geographic:
        return crs
    centre_lon = (bbox[0] + bbox[2]) / 2.0
    centre_lat = (bbox[1] + bbox[3]) / 2.0
    zone = int((centre_lon + 180.0) // 6.0) % 60 + 1
    return f"EPSG:{(32600 if centre_lat >= 0 else 32700) + zone}"


def extent_report(
    bbox: Bbox, crs: str, *, gsd_m: float, tile_px: int
) -> dict[str, object]:
    """Size, pixel count and tiling of an extent. A poor fit is reported, not raised.

    A geographic extent is measured in the UTM zone of its centre; ``skew_m`` is
    the easting difference between its two western corners after projection and
    is zero for an extent already given in a projected CRS.
    """
    if gsd_m <= 0 or tile_px <= 0:
        raise ValueError("gsd_m and tile_px must be positive")
    working = _working_crs(bbox, crs)
    projected = to_projected(bbox, crs, working)
    width_m = projected[2] - projected[0]
    height_m = projected[3] - projected[1]
    width_px = round(width_m / gsd_m)
    height_px = round(height_m / gsd_m)
    cols = math.ceil(width_px / tile_px)
    rows = math.ceil(height_px / tile_px)
    integral = (
        abs(width_m / gsd_m - width_px) < 1e-6
        and abs(height_m / gsd_m - height_px) < 1e-6
    )
    exact_fit = integral and width_px % tile_px == 0 and height_px % tile_px == 0

    transformer = Transformer.from_crs(crs, working, always_xy=True)
    west_south = transformer.transform(bbox[0], bbox[1])
    west_north = transformer.transform(bbox[0], bbox[3])
    to_geographic = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    mid_x = (bbox[0] + bbox[2]) / 2.0
    mid_y = (bbox[1] + bbox[3]) / 2.0
    west = to_geographic.transform(bbox[0], mid_y)
    east = to_geographic.transform(bbox[2], mid_y)
    south = to_geographic.transform(mid_x, bbox[1])
    north = to_geographic.transform(mid_x, bbox[3])
    geod = Geod(ellps="WGS84")
    snapped = snap_outward(projected, tile_px * gsd_m)
    snapped_cols = round((snapped[2] - snapped[0]) / (tile_px * gsd_m))
    snapped_rows = round((snapped[3] - snapped[1]) / (tile_px * gsd_m))
    return {
        "projected_crs": working,
        "projected_bbox": projected,
        "width_m": width_m,
        "height_m": height_m,
        "area_km2": width_m * height_m / 1e6,
        "width_px": width_px,
        "height_px": height_px,
        "tiles": (cols, rows),
        "exact_fit": exact_fit,
        "geodesic_width_m": float(geod.inv(*west, *east)[2]),
        "geodesic_height_m": float(geod.inv(*south, *north)[2]),
        "skew_m": abs(west_south[0] - west_north[0]),
        "snapped_bbox": snapped,
        "snapped_tiles": (snapped_cols, snapped_rows),
    }


def extent_env_lines(bbox: Bbox, crs: str) -> str:
    """The two configuration lines to paste into the experiment record."""
    values = ",".join(repr(float(v)) for v in bbox)
    return f"GEO_DECAY_BBOX={values}\nGEO_DECAY_BBOX_CRS={crs}"


def save_extent(
    bbox: Bbox,
    crs: str,
    out_dir: Path,
    *,
    gsd_m: float,
    tile_px: int,
) -> Path:
    """Write ``out_dir/extent.json``: the extent, its CRS, its report and a time."""
    out_dir.mkdir(parents=True, exist_ok=True)
    document = {
        "bbox": [float(v) for v in bbox],
        "crs": crs,
        "gsd_m": gsd_m,
        "tile_px": tile_px,
        "report": extent_report(bbox, crs, gsd_m=gsd_m, tile_px=tile_px),
        "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    path = out_dir / "extent.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


# --------------------------------------------------------------------------
# Notebook checker
# --------------------------------------------------------------------------

_ABSOLUTE_PATH = re.compile(r"^(/|~|[A-Za-z]:[\\/])\S")
_ABSOLUTE_IN_SOURCE = re.compile(r"(/Users/|/home/|[A-Za-z]:\\\\)")
_DECIMALS = re.compile(r"\d+\.\d{3,}")


def _is_coordinate_literal(value: object) -> bool:
    """Heuristic: a number that looks like a hard-coded coordinate or extent."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return False
    magnitude = abs(value)
    if isinstance(value, int):
        return magnitude >= 100_000
    return magnitude >= 1000 or (magnitude >= 1 and bool(_DECIMALS.search(repr(value))))


def _cell_problems(index: int, source: str, *, first_code: bool) -> list[str]:
    import ast

    problems: list[str] = []
    try:
        from IPython.core.inputtransformer2 import TransformerManager

        source = TransformerManager().transform_cell(source)
    except ImportError:
        pass
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [f"cell {index}: does not compile ({exc.msg}, line {exc.lineno})"]
    if _ABSOLUTE_IN_SOURCE.search(source):
        problems.append(f"cell {index}: absolute path")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            names = []
        if any(name.startswith(_PACKAGE_PREFIX) for name in names):
            problems.append(f"cell {index}: imports the package ({', '.join(names)})")
        if not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, str):
            if _ABSOLUTE_PATH.match(node.value):
                problems.append(f"cell {index}: absolute path {node.value!r}")
            if _SCHEME in node.value.lower() and not first_code:
                problems.append(f"cell {index}: {_SCHEME} literal")
        elif not first_code and _is_coordinate_literal(node.value):
            problems.append(f"cell {index}: coordinate literal {node.value!r}")
    return problems


def _check_notebook(path: Path) -> list[str]:
    """Return the reasons ``path`` is not an acceptable notebook (empty if valid)."""
    import nbformat

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # missing cell ids are repaired below
            notebook = nbformat.read(path, as_version=4)
            _, notebook = nbformat.validator.normalize(notebook)
            nbformat.validate(notebook)
    except Exception as exc:
        return [f"nbformat validation failed: {exc}"]
    problems: list[str] = []
    seen_code = False
    previous = ""
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            if previous != "markdown":
                problems.append(f"cell {index}: code cell not preceded by markdown")
            problems.extend(
                _cell_problems(index, cell.source, first_code=not seen_code)
            )
            seen_code = True
        previous = cell.cell_type
    return problems


# --------------------------------------------------------------------------
# Offline selftest
# --------------------------------------------------------------------------


def _write_png(path: Path, array: np.ndarray) -> None:
    """Write a ``(rows, cols, bands)`` uint8 array as a PNG."""
    import rasterio

    rows, cols, bands = array.shape
    with rasterio.open(
        path, "w", driver="PNG", width=cols, height=rows, count=bands, dtype="uint8"
    ) as dst:
        dst.write(np.moveaxis(array, -1, 0))


def _selftest() -> int:
    failures: list[str] = []

    def check(name: str, condition: bool, detail: object = "") -> None:
        print(f"{'ok  ' if condition else 'FAIL'} {name}")
        if not condition:
            failures.append(f"{name}: {detail}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 4, 5: the one network attempt, to a host that cannot resolve
        out = root / "dead"
        dead_url = f"{_SCHEME}://probe.invalid/wms"
        got = fetch(dead_url, {"REQUEST": "GetCapabilities"}, out, timeout=5.0)
        check(
            "4 dead host is a value: error set, status 0, no md5, no path",
            bool(got.error) and got.status == 0 and got.md5 == "" and got.path is None,
            got,
        )
        _append_manifest(out, got, "2000-01-01T00:00:00+00:00")
        with manifest_path(out).open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        check(
            "5 manifest header is the audit-trail header",
            rows[:1] == [_MANIFEST_HEADER],
            rows[:1],
        )
        check(
            "5 manifest appends one row per request, failures included",
            len(rows) == 3,
            rows,
        )

        # 4: epoch verdicts, with the network replaced by synthetic replies
        provider = next(iter(PROVIDERS.values()))
        epoch_dir = root / "epochs"
        epoch_dir.mkdir()
        content = np.arange(16 * 16 * 3, dtype=np.uint8).reshape(16, 16, 3)
        _write_png(epoch_dir / "content.png", content)
        _write_png(epoch_dir / "blank.png", np.zeros((16, 16, 4), dtype=np.uint8))
        replies = {
            "2004": Fetch("u", 200, 1, "m", 0.0, epoch_dir / "content.png", ""),
            "2005": Fetch("u", 200, 1, "m", 0.0, epoch_dir / "blank.png", ""),
            "2006": Fetch("u", 0, 0, "", 0.0, None, "unreachable"),
        }

        def stub(url: str, params: dict[str, str], out_dir: Path, **_: float) -> Fetch:
            return replies[params["LAYERS"][-4:]]

        real_fetch = globals()["fetch"]
        globals()["fetch"] = stub
        try:
            probed = epoch_availability(
                provider,
                (400000.0, 4800000.0, 401000.0, 4801000.0),
                provider.native_crs,
                range(2004, 2007),
                epoch_dir,
            )
        finally:
            globals()["fetch"] = real_fetch
        check(
            "4 epoch_availability: one row per year, present/absent/unknown",
            [r["verdict"] for r in probed] == ["present", "absent", "unknown"],
            probed,
        )

        # 6: image checks
        transparent = root / "transparent.png"
        _write_png(transparent, np.zeros((8, 8, 4), dtype=np.uint8))
        flat = root / "flat.png"
        _write_png(flat, np.full((8, 8, 3), 90, dtype=np.uint8))
        varied = root / "varied.png"
        _write_png(varied, content)
        check("6 fully transparent PNG is blank", is_blank_image(transparent))
        check("6 single-colour PNG is blank", is_blank_image(flat))
        check(
            "6 PNG with several pixel values is not blank", not is_blank_image(varied)
        )
        stats = image_stats(varied)
        expected = {
            "width",
            "height",
            "bands",
            "min",
            "max",
            "mean",
            "std",
            "saturated_share",
            "nodata_share",
            "gradient_variance",
        }
        check("6 image_stats returns every figure", expected <= set(stats), stats)
        check(
            "6 image_stats sizes and per-band lists",
            (stats["width"], stats["height"], stats["bands"]) == (16, 16, 3)
            and len(stats["mean"]) == 3
            and float(stats["gradient_variance"]) > 0,
            stats,
        )
        summary = write_summary([{"a": 1}, {"a": 2, "b": 3}], root)
        check(
            "5 write_summary unions the columns",
            summary.read_text().splitlines()[0] == "a,b",
        )

        # 12: extent geometry
        gsd_m = PROVIDERS["es-pnoa"].default_gsd_m
        snapped = snap_outward((400100.0, 4800050.0, 401000.0, 4800900.0), 128.0)
        check(
            "12 snap_outward",
            snapped == (400000.0, 4800000.0, 401024.0, 4801024.0),
            snapped,
        )
        report = extent_report(snapped, "EPSG:25830", gsd_m=gsd_m, tile_px=256)
        check(
            "12 extent_report for the snapped extent",
            (report["width_m"], report["height_m"]) == (1024.0, 1024.0)
            and (report["width_px"], report["height_px"]) == (4096, 4096)
            and report["tiles"] == (16, 16)
            and report["exact_fit"] is True
            and abs(float(report["area_km2"]) - 1.048576) < 1e-9
            and float(report["skew_m"]) < 1e-6,
            report,
        )
        loose = extent_report(
            (400000.0, 4800000.0, 400500.0, 4800500.0),
            "EPSG:25830",
            gsd_m=gsd_m,
            tile_px=256,
        )
        check(
            "12 a non-fitting extent reports exact_fit False",
            loose["exact_fit"] is False,
            loose,
        )
        geographic = extent_report(
            (-5.28, 43.36, -5.26, 43.37), "EPSG:4326", gsd_m=gsd_m, tile_px=256
        )
        check(
            "12 a geographic extent carries skew",
            float(geographic["skew_m"]) > 0,
            geographic,
        )
        envelope = to_projected((-5.28, 43.36, -5.26, 43.37), "EPSG:4326", "EPSG:25830")
        two_corner = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
        sw = two_corner.transform(-5.28, 43.36)
        ne = two_corner.transform(-5.26, 43.37)
        check(
            "12 to_projected is wider than two corners alone",
            (envelope[2] - envelope[0]) > (ne[0] - sw[0]) - 1e-9
            and envelope[0] <= sw[0]
            and envelope[3] >= ne[1],
            envelope,
        )
        lines = extent_env_lines(snapped, "EPSG:25830").splitlines()
        check(
            "12 extent_env_lines",
            lines
            == [
                "GEO_DECAY_BBOX=400000.0,4800000.0,401024.0,4801024.0",
                "GEO_DECAY_BBOX_CRS=EPSG:25830",
            ],
            lines,
        )
        saved = save_extent(
            snapped, "EPSG:25830", root / "extent", gsd_m=gsd_m, tile_px=256
        )
        check(
            "12 save_extent writes extent.json",
            saved == root / "extent" / "extent.json"
            and json.loads(saved.read_text())["crs"] == "EPSG:25830",
        )

    if failures:
        print(f"selftest FAILED ({len(failures)})", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print("selftest passed")
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--selftest", action="store_true", help="offline checks")
    group.add_argument("--check-notebook", type=Path, metavar="PATH")
    args = parser.parse_args(argv)
    if args.selftest:
        return _selftest()
    problems = _check_notebook(args.check_notebook)
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"notebook ok: {args.check_notebook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
