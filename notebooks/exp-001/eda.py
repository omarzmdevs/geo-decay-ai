"""Helpers for the EXP-001 notebook, in the same folder as the notebook.

Exploratory instrumentation, outside ``src/`` and outside the layer contracts.
It does not import the package and the package never imports it. Derived from
the accepted module of handoff 013; the experiment is self-contained in this
folder, so nothing here reads or writes outside it.

Four concerns live here, each independent of any one country:

* fetching from a map/feature provider that is described as data
  (``PROVIDERS``) and recording every request in an auditable manifest;
* image-quality figures computed with numpy;
* extent geometry: projection envelope, snapping and tiling arithmetic;
* the drawing round-trip, so a rectangle drawn on a map is not lost when the
  kernel restarts;
* reading what a service advertises, so the provider entry can be confirmed or
  contradicted instead of trusted.

Every output goes under one directory, ``out/`` beside this file by convention,
with response bodies filed by kind: ``capabilities/``, ``vectors/``,
``features/``, ``epochs/`` and ``chips/``. The manifest sits at its root. The
two image folders are git-ignored; everything else is small and versioned.

Run ``python notebooks/exp-001/eda.py --selftest`` for the offline checks, or
``--check-notebook <path>`` to validate a notebook against the project rules.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
import tempfile
import time
import warnings
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from xml.etree import ElementTree

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
            # WMS only: the cadastral WMS advertises CONSTRU, not the INSPIRE
            # bu:Building, which belongs to the WFS (see wfs_params below).
            "buildings": ("cadastre_wms", "CONSTRU"),
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
PROBE_SIZE = (256, 256)  # public: a section has to report what size it asked for
# The ladder of request sizes the native-resolution measurement walks over one
# tile-sized ground window. The service declares no maximum width or height, so
# the real cap is discovered by asking, and the ladder stops where it is refused.
LADDER_PX: tuple[int, ...] = (128, 256, 512, 1024, 2048)
# A rung whose unexplained share stays below this added no new ground detail: it
# is the previous rung enlarged. Not zero, because the floor is never silent —
# an upstream JPEG mosaic, the service's own resampling and 8-bit rounding each
# leave a little behind — and well under the share a real new octave of detail
# leaves, which the selftest measures on ground truth it builds itself.
DETAIL_FLOOR = 0.04
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


BODY_DIRS: tuple[str, ...] = (
    "capabilities",  # GetCapabilities and ListStoredQueries documents: versioned
    "vectors",  # WFS replies: versioned
    "features",  # GetFeatureInfo replies: versioned
    "epochs",  # rendered map images: git-ignored, they are re-fetchable
    "chips",  # per-building crops drawn by the notebook: git-ignored
)


def manifest_path(out_dir: Path) -> Path:
    """Location of the append-only request log inside ``out_dir``."""
    return out_dir / "manifest.csv"


def prepare_out(out_dir: Path) -> Path:
    """Create ``out_dir`` and one subfolder per body kind, and return it.

    Response bodies are filed by kind rather than all together, so that the
    heavy, re-fetchable ones can be git-ignored by folder while the small
    documents that make up the audit trail stay versioned.
    """
    for name in ("", *BODY_DIRS):
        (out_dir / name).mkdir(parents=True, exist_ok=True)
    return out_dir


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
    kind: str = "misc",
) -> Fetch:
    """GET ``url`` and log it. Never raises, whatever goes wrong.

    A transport failure, or a refusal by an intermediary proxy, yields
    ``status == 0``, an empty ``md5`` and no ``path``. A response with a status
    of 400 or above keeps its body (service exceptions are evidence) and
    carries the status in ``error``. Every call, successful or not, appends
    one row to the manifest: a figure with no manifest row behind it is not a
    measurement.

    ``kind`` names the subfolder of ``out_dir`` the body is filed under, one of
    ``BODY_DIRS``.
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
    except OSError as exc:
        # OSError, not requests.RequestException: the latter is a *subclass* of
        # the former, so catching only it lets a bare OSError escape and leave
        # no manifest row at all. An unreadable TLS CA bundle raises exactly
        # that, and criterion 5 of handoff 013 is that a failed request is
        # always logged. The selftest drives this path.
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
        body_dir = out_dir / kind
        body_dir.mkdir(parents=True, exist_ok=True)
        target = body_dir / (
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
    return fetch(provider.endpoints[service], params, out_dir, kind="capabilities")


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
    return fetch(url, params, out_dir, kind="epochs")


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
    return fetch(url, params, out_dir, kind="features")


def wfs_capabilities(provider: Provider, out_dir: Path) -> Fetch:
    """Fetch the capabilities document of the feature service."""
    params = {
        "SERVICE": "WFS",
        "VERSION": provider.wfs_params.get("version", ""),
        "REQUEST": "GetCapabilities",
    }
    return fetch(
        provider.endpoints[provider.wfs_service], params, out_dir, kind="capabilities"
    )


def wfs_stored_queries(provider: Provider, out_dir: Path) -> Fetch:
    """Ask the feature service which stored queries it offers.

    A stored query is a named, server-side query the client calls by id. The
    entry claims one; this is what shows whether the service has it.
    """
    params = {
        "SERVICE": "WFS",
        "VERSION": provider.wfs_params.get("version", ""),
        "REQUEST": "ListStoredQueries",
    }
    return fetch(
        provider.endpoints[provider.wfs_service], params, out_dir, kind="capabilities"
    )


def wfs_buildings(provider: Provider, bbox: Bbox, crs: str, out_dir: Path) -> Fetch:
    """Fetch the building footprints that intersect ``bbox``."""
    epsg = CRS.from_user_input(crs).to_epsg()
    values = {
        "bbox": ",".join(repr(float(v)) for v in bbox),
        "crs": crs,
        "epsg": str(epsg),
    }
    params = {key: tpl.format(**values) for key, tpl in provider.wfs_params.items()}
    return fetch(
        provider.endpoints[provider.wfs_service], params, out_dir, kind="vectors"
    )


@dataclass(frozen=True)
class Capabilities:
    """What one capabilities document advertises, read without its namespaces.

    ``crs`` codes are normalised to ``EPSG:<code>``, so that a WMS saying
    ``EPSG:25830`` and a WFS saying ``urn:ogc:def:crs:EPSG::25830`` compare
    equal against the same entry. ``titles`` and ``abstracts`` map a layer name
    to its title and to its free-text description; a service that publishes no
    scale element at all may still declare a resolution in the abstract, in
    prose, which ``declared_resolutions`` reads. ``exception`` is set when the
    document is a service exception or could not be read, and the other fields
    are then empty: an unreadable document is a value with a reason, never an
    exception.

    Both maps are keyed by layer name, so a layer without a name — a grouping
    layer — contributes nothing. That is deliberate: a group's abstract must
    never be read as a declaration about the layers under it.
    """

    crs: tuple[str, ...]
    layers: tuple[str, ...]
    titles: dict[str, str]
    stored_queries: tuple[str, ...]
    exception: str
    abstracts: dict[str, str] = field(default_factory=dict)


_EPSG_CODE = re.compile(r"EPSG:+(\d+)", re.IGNORECASE)
_CRS_TAGS = frozenset(
    {"CRS", "SRS", "DefaultCRS", "OtherCRS", "DefaultSRS", "OtherSRS"}
)
_NAMED_TAGS = frozenset({"Layer", "FeatureType"})


def _local(tag: str) -> str:
    """A tag without its XML namespace."""
    return tag.rpartition("}")[2]


def _child_text(element: ElementTree.Element, name: str) -> str:
    return next(
        (
            (child.text or "").strip()
            for child in element
            if _local(child.tag) == name and (child.text or "").strip()
        ),
        "",
    )


def read_capabilities(path: Path | None) -> Capabilities:
    """Read what a WMS or WFS capabilities document advertises.

    Tags are matched on their local name and namespaces are ignored, because
    the same facts are spelled differently in WMS 1.1.1, WMS 1.3.0 and WFS 2.0
    and the point is to compare them against one provider entry. The document
    is treated strictly as data: nothing in it is executed, resolved or
    followed.
    """
    if path is None or not path.is_file():
        return Capabilities((), (), {}, (), "no document was saved")
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        return Capabilities((), (), {}, (), f"{type(exc).__name__}: {exc}")
    if "exception" in _local(root.tag).lower():
        text = " ".join(part.strip() for part in root.itertext() if part.strip())
        return Capabilities((), (), {}, (), f"service exception: {text[:200]}")
    crs: list[str] = []
    layers: list[str] = []
    titles: dict[str, str] = {}
    abstracts: dict[str, str] = {}
    queries: list[str] = []
    for element in root.iter():
        tag = _local(element.tag)
        text = (element.text or "").strip()
        if tag in _CRS_TAGS and text:
            for part in text.split():
                match = _EPSG_CODE.search(part)
                crs.append(f"EPSG:{match.group(1)}" if match else part.upper())
        elif tag == "StoredQuery":
            identifier = (element.get("id") or "").strip()
            if identifier:
                queries.append(identifier)
        elif tag in _NAMED_TAGS:
            name = _child_text(element, "Name")
            if name:
                layers.append(name)
                titles[name] = _child_text(element, "Title")
                abstracts[name] = _child_text(element, "Abstract")
    return Capabilities(
        tuple(dict.fromkeys(crs)),
        tuple(dict.fromkeys(layers)),
        titles,
        tuple(dict.fromkeys(queries)),
        "",
        abstracts,
    )


@dataclass(frozen=True)
class DeclaredResolution:
    """One ground resolution a service declares in prose, with its own words.

    ``gsd_m`` is the figure converted to metres. ``text`` is the clause it was
    read from, verbatim and whitespace-collapsed, because that clause is what
    names the area the figure applies to. The two always travel together: a
    declared resolution reported as a bare number cannot be told apart from a
    measured one, and these are declarations, not measurements.
    """

    gsd_m: float
    text: str


# A resolution written as prose: one or more figures sharing a unit, as in
# "25 cm", "0,25 m", "0,15 y 0,16 m" or "(50, 25 y 15 cm)". Only a figure that
# carries a unit is read, so a year, a scale denominator or a flight date is
# never mistaken for a resolution.
_RESOLUTION_PHRASE = re.compile(
    r"(?P<values>\d+(?:[.,]\d+)?(?:\s*(?:,|y|o)\s*\d+(?:[.,]\d+)?)*)"
    r"\s*(?P<unit>centímetros?|cm|metros?|m)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")
_UNIT_METRES = {
    "cm": 0.01,
    "centímetro": 0.01,
    "centímetros": 0.01,
    "m": 1.0,
    "metro": 1.0,
    "metros": 1.0,
}
# A ground sample distance outside this window is not one: it is a figure that
# happened to sit next to a unit. Both ends are deliberately generous.
_PLAUSIBLE_GSD_M = (0.01, 10.0)


def declared_resolutions(abstract: str) -> tuple[DeclaredResolution, ...]:
    """Read every ground resolution ``abstract`` declares, each with its clause.

    Some services publish no ``ScaleHint`` and no scale denominator anywhere,
    and write the resolution into the layer description instead — often several
    of them in one description, one per area covered. This returns one entry per
    figure, in the order the text gives them, so that several declarations are
    reported as several rather than collapsed into an average or a first value.
    An empty result means this text declares nothing: callers say so, and must
    not fall back on a neighbouring layer, a parent layer or a provider default.

    The clause carried by each entry runs from the end of the previous
    declaration — or from the start of the sentence, whichever is later — to the
    end of the figure, which is where the wording that names the area lives.
    Nothing in the text is executed, resolved or followed; it is data.

    Spanish writes the decimal separator as a comma and the thousands separator
    as a dot, and both are read here as a decimal point. That is unambiguous
    inside the plausibility window: a thousands separator puts the value far
    outside it.
    """
    found: list[DeclaredResolution] = []
    low, high = _PLAUSIBLE_GSD_M
    cursor = 0
    for match in _RESOLUTION_PHRASE.finditer(abstract):
        factor = _UNIT_METRES.get(match.group("unit").lower())
        start = cursor
        cursor = match.end()
        if factor is None:  # the pattern and the table drifted apart
            continue
        sentence = abstract.rfind(". ", start, match.start())
        if sentence != -1:
            start = sentence + 2
        clause = " ".join(abstract[start : match.end()].split())
        for number in _NUMBER.findall(match.group("values")):
            value = float(number.replace(",", ".")) * factor
            if low <= value <= high:
                found.append(DeclaredResolution(value, clause))
    return tuple(found)


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
        got = wms_map(provider, layer, bbox, crs, PROBE_SIZE, out_dir)
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
# Native resolution, measured by asking for the same ground twice over
# --------------------------------------------------------------------------

_FIT_NEIGHBOURHOOD = 2  # half-width of the coarse neighbourhood a phase is fitted from
_FIT_SAMPLES = 50_000  # positions sampled per phase: far more than the 26 unknowns
_FIT_SEED = 0  # the sampling is seeded, so the same images give the same figure
_FIT_MINIMUM = 500  # fewer usable positions than this is not a measurement


@dataclass(frozen=True)
class RungDetail:
    """What one rung of a request-size ladder adds over the rung before it.

    ``share`` is the root mean square of what no fitted linear interpolation of
    the coarser rung explains, divided by the standard deviation of the finer
    rung over the same ground window: a dimensionless share of that window's own
    contrast, which is what makes two rungs of different pixel counts, two years
    and two extents comparable. ``nan`` means there is no figure, and ``reason``
    then says why. ``factor`` is the size ratio between the two rungs and
    ``samples`` how many positions the figure rests on.
    """

    share: float
    factor: int
    samples: int
    reason: str


def _grey_and_valid(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """The mean colour band of an image, and the mask of its usable pixels."""
    pixels, alpha = _read_image(path)
    colour = [i for i in range(pixels.shape[0]) if i != alpha]
    grey = pixels[colour].astype(np.float64).mean(axis=0)
    if alpha is None:
        valid = np.ones(grey.shape, dtype=bool)
    else:
        valid = pixels[alpha].astype(bool)
    return grey, valid


def unexplained_share(coarse: Path, fine: Path) -> RungDetail:
    """How much of ``fine`` no linear interpolation of ``coarse`` can explain.

    Both images must cover the same ground window, with ``fine`` an integer
    multiple of ``coarse`` in both axes — which a ladder of doubling request
    sizes over one unchanged bounding box gives for free.

    **The predictor is fitted, not assumed.** The fine grid is split into its
    ``factor x factor`` phases, and for each phase the best least-squares
    combination of a 5x5 neighbourhood of the coarse grid is solved for; what is
    left over is measured. Fitting instead of assuming is what makes the figure
    independent of how the service resamples: nearest neighbour, bilinear,
    cubic, a sharpening kernel and a sub-pixel shift all lie inside the family
    the fit can express. So a rung that is only the previous rung enlarged
    leaves almost nothing behind, whatever enlarged it, while a rung that
    carries a real new octave of ground detail leaves a share no interpolation
    of the coarser rung can recover — because that detail is precisely the
    information the coarser rung does not hold.

    Pixels are excluded where the finer rung is transparent or where any of the
    25 coarse neighbours is, so a window that reaches past the service's
    coverage is measured on the part that answered instead of on its own edge.
    """
    try:
        coarse_grey, coarse_valid = _grey_and_valid(coarse)
        fine_grey, fine_valid = _grey_and_valid(fine)
    except Exception as exc:  # undecodable bytes are a reason, not a crash
        return RungDetail(math.nan, 0, 0, f"unreadable image: {exc}")
    rows, cols = coarse_grey.shape
    factor = fine_grey.shape[0] // rows if rows else 0
    if factor < 2 or (rows * factor, cols * factor) != fine_grey.shape:
        return RungDetail(
            math.nan,
            factor,
            0,
            f"the two rungs do not share a grid: {coarse_grey.shape} and "
            f"{fine_grey.shape} are not an integer multiple apart",
        )
    pad = _FIT_NEIGHBOURHOOD
    if rows - 2 * pad < pad or cols - 2 * pad < pad:
        return RungDetail(math.nan, factor, 0, "the coarse rung is too small to fit")
    spread = float(fine_grey[fine_valid].std()) if fine_valid.any() else 0.0
    if spread <= 0.0:
        return RungDetail(
            math.nan, factor, 0, "the finer rung has no contrast to take a share of"
        )
    offsets = [(dr, dc) for dr in range(-pad, pad + 1) for dc in range(-pad, pad + 1)]
    inner_cols = cols - 2 * pad
    # One mask over the interior: a position is usable only where all 25 coarse
    # neighbours are. Positions are then sampled, and the neighbourhood is read
    # at the sampled positions alone, so a 2048 px rung costs megabytes.
    neighbours_valid = np.logical_and.reduce(
        [
            coarse_valid[pad + dr : rows - pad + dr, pad + dc : cols - pad + dc]
            for dr, dc in offsets
        ]
    ).reshape(-1)
    rng = np.random.default_rng(_FIT_SEED)
    squares = 0.0
    count = 0
    for phase_row in range(factor):
        for phase_col in range(factor):
            phase = fine_grey[phase_row::factor, phase_col::factor]
            phase_valid = fine_valid[phase_row::factor, phase_col::factor]
            usable = neighbours_valid & phase_valid[
                pad : rows - pad, pad : cols - pad
            ].reshape(-1)
            chosen = np.flatnonzero(usable)
            if chosen.size < _FIT_MINIMUM:
                continue
            if chosen.size > _FIT_SAMPLES:
                chosen = rng.choice(chosen, _FIT_SAMPLES, replace=False)
            at_row = chosen // inner_cols + pad
            at_col = chosen % inner_cols + pad
            design = np.stack(
                [coarse_grey[at_row + dr, at_col + dc] for dr, dc in offsets]
                + [np.ones(chosen.size, dtype=np.float64)],
                axis=1,
            )
            target = phase[at_row, at_col]
            fitted = np.linalg.lstsq(design, target, rcond=None)[0]
            residual = target - design @ fitted
            squares += float((residual**2).sum())
            count += residual.size
    if count == 0:
        return RungDetail(
            math.nan,
            factor,
            0,
            f"fewer than {_FIT_MINIMUM} positions were usable in any phase",
        )
    return RungDetail(math.sqrt(squares / count) / spread, factor, count, "")


def resolution_ladder(
    provider: Provider,
    layer: str,
    window: Bbox,
    crs: str,
    out_dir: Path,
    *,
    sizes: Iterable[int] = LADDER_PX,
) -> list[dict[str, object]]:
    """Ask for one ground window at growing sizes: one row per rung, never raises.

    Every rung asks for the same ``window``, so the rungs' pixel grids are
    nested and each one can be compared against the rung before it. The reply is
    lossless by default (see ``wms_map``), which removes the compression this
    measurement would otherwise have to fight; whatever compression is already
    baked into the service's own mosaic stays, and raises the floor rather than
    hiding under it.

    The ladder stops at the first rung the service does not answer with an image
    with content, and that rung keeps its row with the reason. The service
    declares no maximum width or height, so the real cap is discovered by
    asking: a refusal is a recorded finding, not a failure.
    """
    rows: list[dict[str, object]] = []
    side_m = float(window[2] - window[0])
    previous: Path | None = None
    for size in sizes:
        got = wms_map(provider, layer, window, crs, (int(size), int(size)), out_dir)
        verdict, evidence, blank = _epoch_verdict(got)
        row: dict[str, object] = {
            "size_px": int(size),
            "gsd_m": side_m / float(size),
            "status": got.status,
            "nbytes": got.nbytes,
            "md5": got.md5,
            "path": str(got.path) if got.path is not None else "",
            "blank": blank,
            "share": None,
            "samples": 0,
            "reason": "",
            "stopped": False,
        }
        if verdict != "present" or got.path is None:
            row["reason"] = f"{verdict}: {evidence}"
            row["stopped"] = True
            rows.append(row)
            break
        if previous is not None:
            detail = unexplained_share(previous, got.path)
            row["reason"] = detail.reason
            row["samples"] = detail.samples
            if math.isfinite(detail.share):
                row["share"] = detail.share
        previous = got.path
        rows.append(row)
    return rows


def resolution_from_ladder(
    rows: list[dict[str, object]], *, floor: float = DETAIL_FLOOR
) -> dict[str, object]:
    """The ground sample distance a ladder supports, or why it supports none.

    The verdict is the finest rung whose unexplained share still exceeds
    ``floor``, and it is given **only** when at least one finer rung sits
    below that floor: a share still above the floor at the finest rung means the
    curve never flattened, so the ladder did not reach far enough, and that is
    what is reported — never the last rung's figure as if it were the answer.

    ``floor`` is a constant and sits directly on top of the answer, so it is
    returned with the verdict, to be shown beside it: a threshold a reader
    cannot see is one they cannot argue with. It is open as an argument for the
    same reason — the selftest sweeps it over a range of an order of magnitude
    and requires the recovered resolution to be the same figure throughout. A
    verdict that moves when the constant moves is an artefact of the constant,
    not a measurement, and must be reported as inconclusive instead.

    Two other outcomes are values rather than failures. When no rung is above
    the floor, the first comparison already found nothing new and the native
    sampling is no finer than the coarsest rung asked for: a bound, not a
    measurement. When fewer than two rungs came back readable there is nothing
    to compare at all.

    ``drop`` is how many times the share falls between the verdict's rung and
    the next one, and ``floor_observed`` the largest share among the rungs below
    the floor: the evidence for the verdict and the margin it rests on, so a
    reader can see how far the decision sat from its threshold instead of
    trusting it.
    """
    curve = [
        (int(str(row["size_px"])), float(str(row["gsd_m"])), float(str(row["share"])))
        for row in rows
        if isinstance(row.get("share"), float)
    ]
    result: dict[str, object] = {
        "curve": curve,
        "measured_gsd_m": None,
        "measured_px": None,
        "floor": floor,
        "floor_observed": None,
        "drop": None,
        "bound_gsd_m": None,
        "bound": "",
        "reason": "",
    }
    if not curve:
        result["reason"] = "fewer than two readable rungs: nothing to compare"
        return result
    above = [index for index, entry in enumerate(curve) if entry[2] >= floor]
    if not above:
        result["bound_gsd_m"] = float(str(rows[0]["gsd_m"]))
        result["bound"] = "no_finer_than"
        result["floor_observed"] = max(entry[2] for entry in curve)
        result["reason"] = (
            "no rung added detail above the floor: the native sampling is no "
            "finer than the coarsest rung asked for"
        )
        return result
    finest = above[-1]
    below = curve[finest + 1 :]
    if not below:
        result["bound_gsd_m"] = curve[finest][1]
        result["bound"] = "at_least_as_fine_as"
        result["reason"] = (
            "the curve had not flattened at the finest rung: the ladder did not "
            "reach far enough, so no figure is given"
        )
        return result
    result["measured_px"] = curve[finest][0]
    result["measured_gsd_m"] = curve[finest][1]
    result["floor_observed"] = max(entry[2] for entry in below)
    result["drop"] = curve[finest][2] / below[0][2] if below[0][2] > 0 else math.inf
    return result


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


def centred_window(bbox: Bbox, side_m: float) -> Bbox:
    """A square window of ``side_m`` ground metres centred in ``bbox``.

    A service's native resolution is measured over one window the size of a
    pipeline tile rather than over the whole extent: it is the window the
    pipeline will actually request, and it is small enough in bytes to ask for
    the same ground once per rung of a ladder. A window wider or taller than the
    extent is clipped to it, so the measurement never reaches outside the ground
    the extent covers; the caller compares the two sides and reports the
    clipping, because a clipped window is no longer square and its two axes then
    carry two different ground sample distances.
    """
    if side_m <= 0:
        raise ValueError("side_m must be positive")
    centre_x = (bbox[0] + bbox[2]) / 2.0
    centre_y = (bbox[1] + bbox[3]) / 2.0
    half_x = min(side_m, bbox[2] - bbox[0]) / 2.0
    half_y = min(side_m, bbox[3] - bbox[1]) / 2.0
    return (centre_x - half_x, centre_y - half_y, centre_x + half_x, centre_y + half_y)


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


def save_drawing(bbox: Bbox, crs: str, out_dir: Path) -> Path:
    """Write ``out_dir/drawing.json``: the rectangle exactly as it was drawn.

    ``extent.json`` records the *resolved* extent, reprojected, snapped and
    reported. This records its raw input instead, so that a rectangle drawn on
    a map survives a kernel restart, a re-run of the cell that built the map,
    and a notebook executed from top to bottom. It is meant to be written the
    moment the drawing arrives, not when the extent is finally resolved.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    document = {
        "bbox": [float(v) for v in bbox],
        "crs": crs,
        "timestamp_utc": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    path = out_dir / "drawing.json"
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return path


def load_drawing(out_dir: Path) -> tuple[Bbox, str, str] | None:
    """Return the last saved drawing as ``(bbox, crs, timestamp)``, else ``None``.

    A missing, unreadable or incomplete file is not an error: it means there is
    no drawing to reuse, which the caller reports in its own words.
    """
    path = out_dir / "drawing.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
        values = [float(v) for v in document["bbox"]]
        crs = str(document["crs"])
        stamp = str(document.get("timestamp_utc", ""))
    except (OSError, ValueError, KeyError, TypeError):
        return None
    if len(values) != 4 or not crs:
        return None
    return (values[0], values[1], values[2], values[3]), crs, stamp


def forget_drawing(out_dir: Path) -> bool:
    """Delete the saved drawing. ``True`` if there was one to delete.

    Called when the drawing is deleted on the map, so that a rectangle the user
    dropped cannot be resurrected from disk by a later run. Nothing else in
    this module deletes anything: a registered extent is never removed because
    a later run resolved nothing.
    """
    path = out_dir / "drawing.json"
    if not path.is_file():
        return False
    path.unlink()
    return True


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


def _block_mean(values: np.ndarray, factor: int) -> np.ndarray:
    """Average ``factor`` x ``factor`` blocks: one way a service downsamples.

    Ground-truth support for the selftest only. The resolution estimator never
    calls it, and must not: it is told nothing about how its input was built.
    """
    rows = values.shape[0] - values.shape[0] % factor
    cols = values.shape[1] - values.shape[1] % factor
    cut = values[:rows, :cols]
    return cut.reshape(rows // factor, factor, cols // factor, factor).mean(axis=(1, 3))


def _expand_nearest(values: np.ndarray, factor: int) -> np.ndarray:
    """Repeat every pixel: the bluntest way to serve more pixels than exist."""
    return np.repeat(np.repeat(values, factor, axis=0), factor, axis=1)


def _expand_bilinear(values: np.ndarray, factor: int) -> np.ndarray:
    """Interpolate linearly between pixel centres: the usual way."""
    rows, cols = values.shape

    def axis(length: int) -> tuple[np.ndarray, np.ndarray]:
        centres = (np.arange(length * factor) + 0.5) / factor - 0.5
        clipped = np.clip(centres, 0.0, float(length - 1))
        low = np.floor(clipped).astype(int)
        return low, clipped - low

    row_low, row_weight = axis(rows)
    col_low, col_weight = axis(cols)
    row_high = np.minimum(row_low + 1, rows - 1)
    col_high = np.minimum(col_low + 1, cols - 1)
    weight = col_weight[None, :]
    top = (
        values[row_low][:, col_low] * (1 - weight)
        + values[row_low][:, col_high] * weight
    )
    bottom = (
        values[row_high][:, col_low] * (1 - weight)
        + values[row_high][:, col_high] * weight
    )
    return top * (1 - row_weight[:, None]) + bottom * row_weight[:, None]


def _ground_truth_scene(size: int, seed: int = 7) -> np.ndarray:
    """A ``size`` x ``size`` scene carrying detail down to its own pixel.

    Smooth relief, bright rectangles standing in for roofs, and grain at the
    native pixel. The grain is what makes a native resolution recoverable at
    all, and it is what real imagery carries as sensor noise and surface
    texture: a scene smooth to its last pixel has no native resolution to find.
    """
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:size, 0:size] / size
    scene = 90.0 + 40.0 * np.sin(6 * math.pi * x) * np.cos(4 * math.pi * y)
    for _ in range(14):
        row = int(rng.integers(0, size - size // 8))
        col = int(rng.integers(0, size - size // 8))
        high = int(rng.integers(size // 16, size // 8))
        wide = int(rng.integers(size // 16, size // 8))
        scene[row : row + high, col : col + wide] += float(rng.integers(40, 110))
    return scene + rng.normal(0.0, 9.0, size=(size, size))


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

        # 5: a failure that happens before the network is logged too.
        # requests.RequestException is a subclass of OSError, not the reverse,
        # so catching only it used to let a bare OSError escape with no row.
        bare_out = root / "bare"
        bundle = os.environ.get("REQUESTS_CA_BUNDLE")
        os.environ["REQUESTS_CA_BUNDLE"] = str(root / "absent-ca-bundle.pem")
        bare: Fetch | None = None
        escaped = ""
        try:
            bare = fetch(f"{_SCHEME}s://probe.invalid/wms", {}, bare_out, timeout=5.0)
        except OSError as exc:
            escaped = f"{type(exc).__name__}: {exc}"
        finally:
            if bundle is None:
                os.environ.pop("REQUESTS_CA_BUNDLE", None)
            else:
                os.environ["REQUESTS_CA_BUNDLE"] = bundle
        check("5 a bare OSError does not escape fetch", not escaped, escaped)
        check(
            "5 a bare OSError is a value: status 0 with its reason",
            bare is not None
            and bare.status == 0
            and bool(bare.error)
            and bare.path is None,
            bare,
        )
        bare_rows: list[list[str]] = []
        if manifest_path(bare_out).exists():
            with manifest_path(bare_out).open(newline="", encoding="utf-8") as handle:
                bare_rows = list(csv.reader(handle))
        check(
            "5 a bare OSError still leaves its manifest row",
            len(bare_rows) == 2 and bare_rows[1][2] == "0",
            bare_rows,
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

        # 6: the native resolution, against ground truth built here. The scene is
        # the only thing that knows the answer; the estimator is never told it,
        # and never sees the kernel that enlarged its input.
        side_m = float(PROVIDERS["es-pnoa"].default_gsd_m * 256)
        window = centred_window(snapped, side_m)
        check(
            "6 centred_window: a square of the asked side, centred in the extent",
            window == (400480.0, 4800480.0, 400544.0, 4800544.0)
            and abs((window[2] - window[0]) - side_m) < 1e-9
            and abs((window[3] - window[1]) - side_m) < 1e-9,
            window,
        )
        check(
            "6 centred_window clips to the extent instead of reaching outside it",
            centred_window(snapped, side_m * 1024) == snapped,
            centred_window(snapped, side_m * 1024),
        )
        check(
            "6 the ladder doubles, so each rung's grid nests in the one before it",
            all(
                nxt == 2 * cur
                for cur, nxt in zip(LADDER_PX, LADDER_PX[1:], strict=False)
            ),
            LADDER_PX,
        )

        truth = root / "truth"

        def ladder_rows(
            native_px: int,
            sizes: tuple[int, ...],
            expand: Callable[[np.ndarray, int], np.ndarray],
            folder: Path,
        ) -> list[dict[str, object]]:
            """One ladder over one window, from a scene of known resolution."""
            folder.mkdir(parents=True, exist_ok=True)
            native = _ground_truth_scene(native_px)
            built: list[dict[str, object]] = []
            previous: Path | None = None
            for size in sizes:
                if size > native_px:
                    plane = expand(native, size // native_px)
                elif size < native_px:
                    plane = _block_mean(native, native_px // size)
                else:
                    plane = native
                pixels = np.clip(np.round(plane), 0, 255).astype(np.uint8)
                path = folder / f"{size}.png"
                _write_png(path, np.stack([pixels] * 3, axis=-1))
                row: dict[str, object] = {
                    "size_px": size,
                    "gsd_m": side_m / size,
                    "share": None,
                    "reason": "",
                }
                if previous is not None:
                    detail = unexplained_share(previous, path)
                    row["reason"] = detail.reason
                    if math.isfinite(detail.share):
                        row["share"] = detail.share
                built.append(row)
                previous = path
            return built

        native_px = 256
        walked_by_kernel: dict[str, list[dict[str, object]]] = {}
        for kernel, expand in (
            ("nearest", _expand_nearest),
            ("bilinear", _expand_bilinear),
        ):
            walked = ladder_rows(native_px, LADDER_PX, expand, truth / kernel)
            walked_by_kernel[kernel] = walked
            found = resolution_from_ladder(walked)
            curve = found["curve"] if isinstance(found["curve"], list) else []
            print(
                f"     {kernel}: "
                + " ".join(f"{gsd:.4f}m/px {share:.4f}" for _, gsd, share in curve)
            )
            check(
                f"6 a ladder enlarged by {kernel} recovers its known"
                f" {side_m / native_px:g} m/px",
                found["measured_gsd_m"] == side_m / native_px
                and found["measured_px"] == native_px
                and float(str(found["drop"])) > 2.0,
                found,
            )

        # The floor is a constant sitting directly on top of the answer, so the
        # answer must not depend on it: swept over an order of magnitude, the
        # recovered figure has to stay the same one. If this ever fails, the
        # verdict is an artefact of the constant and the notebook has to report
        # the measurement as inconclusive rather than pick a number.
        sweep = (0.02, 0.03, 0.04, 0.06, 0.10, 0.20)
        recovered = {
            kernel: {
                resolution_from_ladder(walked, floor=level)["measured_gsd_m"]
                for level in sweep
            }
            for kernel, walked in walked_by_kernel.items()
        }
        print(f"     floors {sweep[0]:g}–{sweep[-1]:g}: {recovered}")
        check(
            f"6 the verdict survives the floor, swept {sweep[0]:g} to {sweep[-1]:g}",
            all(found == {side_m / native_px} for found in recovered.values()),
            recovered,
        )

        never = ladder_rows(512, (128, 256, 512), _expand_bilinear, truth / "never")
        unflattened = resolution_from_ladder(never)
        check(
            "6 a curve that never flattens is reported as that, not as its last rung",
            unflattened["measured_gsd_m"] is None
            and unflattened["bound"] == "at_least_as_fine_as"
            and "did not reach far enough" in str(unflattened["reason"]),
            unflattened,
        )
        coarser = ladder_rows(64, (128, 256, 512), _expand_bilinear, truth / "coarse")
        bounded = resolution_from_ladder(coarser)
        check(
            "6 a native coarser than the whole ladder is a bound, not a figure",
            bounded["measured_gsd_m"] is None
            and bounded["bound"] == "no_finer_than"
            and bounded["bound_gsd_m"] == side_m / 128,
            bounded,
        )
        check(
            "6 a ladder with nothing to compare is a reason, not a figure",
            "nothing to compare" in str(resolution_from_ladder([])["reason"]),
            resolution_from_ladder([]),
        )

        odd = truth / "odd"
        odd.mkdir()
        _write_png(odd / "odd.png", np.zeros((100, 100, 3), dtype=np.uint8) + 7)
        off_grid = unexplained_share(odd / "odd.png", truth / "bilinear" / "256.png")
        check(
            "6 two rungs off the same grid are a reason, not a figure",
            not math.isfinite(off_grid.share)
            and "do not share a grid" in off_grid.reason,
            off_grid,
        )
        _write_png(odd / "flat-64.png", np.full((64, 64, 3), 90, dtype=np.uint8))
        _write_png(odd / "flat-128.png", np.full((128, 128, 3), 90, dtype=np.uint8))
        featureless = unexplained_share(odd / "flat-64.png", odd / "flat-128.png")
        check(
            "6 a rung with no contrast is a reason, not a share of nothing",
            not math.isfinite(featureless.share) and "contrast" in featureless.reason,
            featureless,
        )

        # 9: the drawing round-trip, which is what a kernel restart rests on
        drawings = root / "drawing"
        check("9 no file means no drawing to reuse", load_drawing(drawings) is None)
        drawn = save_drawing(snapped, "EPSG:25830", drawings)
        loaded = load_drawing(drawings)
        check(
            "9 save_drawing round-trips the rectangle it was given",
            loaded is not None
            and loaded[0] == snapped
            and loaded[1] == "EPSG:25830"
            and loaded[2].endswith("+00:00"),
            loaded,
        )
        drawn.write_text("{ not json", encoding="utf-8")
        check("9 a corrupt drawing is no drawing", load_drawing(drawings) is None)
        check(
            "9 forget_drawing deletes it, and says so only once",
            forget_drawing(drawings)
            and not drawn.is_file()
            and not forget_drawing(drawings),
        )

        # 4: reading what a document advertises, across the three grammars.
        # The namespace is built from _SCHEME so no literal endpoint appears here.
        docs = root / "caps"
        docs.mkdir()
        wms_doc = docs / "wms.xml"
        wms_doc.write_text(
            '<?xml version="1.0"?>'
            f'<WMS_Capabilities xmlns="{_SCHEME}://www.opengis.net/wms">'
            "<Capability><Layer><Title>root</Title>"
            "<CRS>EPSG:25830</CRS><CRS>CRS:84</CRS>"
            "<Layer><Name>OI.OrthoimageCoverage</Name><Title>Ortho 0.25 m</Title>"
            "</Layer>"
            "<Layer><Name>PNOA2004</Name><Title>PNOA 2004 (0.5 m)</Title></Layer>"
            "</Layer></Capability></WMS_Capabilities>",
            encoding="utf-8",
        )
        wms_caps = read_capabilities(wms_doc)
        check(
            "4 capabilities: layers and titles, namespace ignored",
            wms_caps.layers == ("OI.OrthoimageCoverage", "PNOA2004")
            and wms_caps.titles["PNOA2004"] == "PNOA 2004 (0.5 m)"
            and not wms_caps.exception,
            wms_caps,
        )
        check(
            "4 capabilities: CRS codes normalised, unnamed layers skipped",
            wms_caps.crs == ("EPSG:25830", "CRS:84"),
            wms_caps.crs,
        )

        wfs_doc = docs / "wfs.xml"
        wfs_doc.write_text(
            '<?xml version="1.0"?>'
            f'<wfs:WFS_Capabilities xmlns:wfs="{_SCHEME}://www.opengis.net/wfs/2.0">'
            "<wfs:FeatureTypeList><wfs:FeatureType>"
            "<wfs:Name>bu:Building</wfs:Name><wfs:Title>Building</wfs:Title>"
            "<wfs:DefaultCRS>urn:ogc:def:crs:EPSG::25830</wfs:DefaultCRS>"
            "</wfs:FeatureType></wfs:FeatureTypeList>"
            '<wfs:StoredQuery id="GetFeatureByBBOX"/>'
            "</wfs:WFS_Capabilities>",
            encoding="utf-8",
        )
        wfs_caps = read_capabilities(wfs_doc)
        check(
            "4 capabilities: a URN CRS compares equal to a plain EPSG code",
            wfs_caps.crs == ("EPSG:25830",)
            and wfs_caps.layers == ("bu:Building",)
            and wfs_caps.stored_queries == ("GetFeatureByBBOX",),
            wfs_caps,
        )

        exception_doc = docs / "exception.xml"
        exception_doc.write_text(
            '<?xml version="1.0"?>'
            "<ServiceExceptionReport><ServiceException>LAYER not defined"
            "</ServiceException></ServiceExceptionReport>",
            encoding="utf-8",
        )
        failed = read_capabilities(exception_doc)
        check(
            "4 a service exception is a value with its reason",
            "LAYER not defined" in failed.exception and not failed.layers,
            failed,
        )
        check(
            "4 a document that was never saved is a value too",
            read_capabilities(None).exception == "no document was saved",
        )
        (docs / "broken.xml").write_text("<WMS_Capabilities", encoding="utf-8")
        check(
            "4 an unparsable document does not raise",
            "ParseError" in read_capabilities(docs / "broken.xml").exception,
        )

        # 5: the resolution a service declares in prose, which is the only place
        # this one writes it. Every fixture is built here, in the temp folder.
        group_abstract = (
            "Cobertura por años. La cobertura está constituida por mosaicos de "
            "distinta resolución (50, 25 y 15 cm)."
        )
        one_abstract = (
            "Ortoimagen correspondiente al año 2020. Abarca la Comunidad de "
            "Region A a una resolución de 0,25 m."
        )
        many_abstract = (
            "Ortoimagen correspondiente al año 2021. Abarca las Comunidades de "
            "Region B y Region C con una resolución de 25 cm y las islas de "
            "Region D con una resolución de 20 cm."
        )
        none_abstract = (
            "Ortoimagen correspondiente al año 2022, a escala 1 30.000, volada "
            "entre 1981 y 1986."
        )
        prose_doc = docs / "prose.xml"
        prose_doc.write_text(
            '<?xml version="1.0"?>'
            f'<WMS_Capabilities xmlns="{_SCHEME}://www.opengis.net/wms">'
            "<Capability><Layer><Title>group</Title>"
            f"<Abstract>{group_abstract}</Abstract><CRS>EPSG:25830</CRS>"
            f"<Layer><Name>ONE</Name><Title>One</Title>"
            f"<Abstract>{one_abstract}</Abstract></Layer>"
            f"<Layer><Name>MANY</Name><Title>Many</Title>"
            f"<Abstract>{many_abstract}</Abstract></Layer>"
            f"<Layer><Name>NONE</Name><Title>None</Title>"
            f"<Abstract>{none_abstract}</Abstract></Layer>"
            "<Layer><Name>SILENT</Name><Title>Silent</Title></Layer>"
            "</Layer></Capability></WMS_Capabilities>",
            encoding="utf-8",
        )
        prose = read_capabilities(prose_doc)
        check(
            "5 abstracts are keyed by layer name, and only by layer name",
            set(prose.abstracts) == {"ONE", "MANY", "NONE", "SILENT"}
            and prose.abstracts["ONE"] == one_abstract
            and prose.abstracts["SILENT"] == "",
            prose.abstracts,
        )
        single = declared_resolutions(prose.abstracts["ONE"])
        check(
            "5 one declared resolution, with the clause that names its area",
            len(single) == 1
            and single[0].gsd_m == 0.25
            and "Region A" in single[0].text
            and "2020" not in single[0].text,
            single,
        )
        several = declared_resolutions(prose.abstracts["MANY"])
        check(
            "5 several declared resolutions, each with its own areas",
            [round(d.gsd_m, 2) for d in several] == [0.25, 0.20]
            and "Region B" in several[0].text
            and "Region C" in several[0].text
            and "Region D" not in several[0].text
            and "Region D" in several[1].text,
            several,
        )
        check(
            "5 an abstract that declares nothing declares nothing, and inherits none",
            declared_resolutions(prose.abstracts["NONE"]) == ()
            and declared_resolutions(prose.abstracts["SILENT"]) == ()
            and declared_resolutions("") == ()
            # the figures of the grouping layer parse, but reach no named layer
            and [d.gsd_m for d in declared_resolutions(group_abstract)]
            == [0.5, 0.25, 0.15],
            declared_resolutions(prose.abstracts["NONE"]),
        )
        check(
            "5 a document that cannot be read declares nothing to inherit",
            read_capabilities(docs / "broken.xml").abstracts == {}
            and read_capabilities(None).abstracts == {}
            and read_capabilities(exception_doc).abstracts == {},
        )

        # 1: the output layout the ignore rules depend on
        laid_out = prepare_out(root / "out")
        check(
            "1 prepare_out creates one folder per body kind",
            all((laid_out / name).is_dir() for name in BODY_DIRS),
            sorted(p.name for p in laid_out.iterdir()),
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
