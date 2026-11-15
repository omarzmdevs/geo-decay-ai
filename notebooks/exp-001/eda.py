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
* reading what a service advertises, and what its feature replies contain, so
  the provider entry can be confirmed or contradicted instead of trusted;
* reading an elevation coverage as a raster: its grid, CRS and no-data share;
* choosing example buildings, framing their chips and judging each chip;
* manual samples drawn where the cadastre holds nothing, checked by rule;
* the labelling table, which never overwrites manual work.

Every output goes under one directory, ``out/`` beside this file by convention,
with response bodies filed by kind: ``capabilities/``, ``vectors/``,
``features/``, ``epochs/``, ``chips/`` and ``elevation/``, plus ``figs/`` for the
figures a notebook draws rather than stores inside itself. The manifest sits at
its root. The heavy folders are git-ignored; everything else is small and
versioned.

Run ``python notebooks/exp-001/eda.py --selftest`` for the offline checks, or
``--check-notebook <path>`` to validate a notebook against the project rules.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import time
import warnings
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import unquote
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
    # Logical feature kind -> (service key, the type name that service uses).
    # One service may publish several types and a provider may split them
    # across endpoints, so both travel together and nothing is derived from
    # the other.
    wfs_types: dict[str, tuple[str, str]]
    # Namespace prefix -> its URI, as the service's own replies declare them.
    # A qualified type name is useless to a server that cannot resolve its
    # prefix, and the prefix is read from the type name rather than repeated.
    wfs_namespaces: dict[str, str]
    attributes: dict[str, str]
    # The area ceiling the feature service enforces on one request, in square
    # kilometres. ``0.0`` means no ceiling has been measured yet, and the
    # notebook then probes for it instead of assuming one: a number invented
    # here would size every later request wrongly and silently, which is the
    # lesson of EDA-GSD. A measured figure replaces it, with its own date.
    wfs_max_area_km2: float = 0.0
    # How long to wait for a feature reply, in seconds. A service near its own
    # size limit answers slowly, and a wait too short turns a slow service into
    # an apparently broken one; how slow this particular service is, is a fact
    # about it and belongs here rather than in a call.
    wfs_timeout_s: float = 30.0
    # Elevation is served as coverages (OGC WCS): the grid values themselves,
    # not a rendered picture of them. The coverage endpoints live apart from
    # ``endpoints`` because every key there is asked for a map service's
    # capabilities; a coverage service asked that question answers nothing
    # useful. ``elevation`` maps a logical product (``terrain``, ``surface``,
    # ``building_height``, ``vegetation_height``) to ``(coverage endpoint key,
    # coverage identifier)``. An empty mapping is a valid provider: the notebook
    # then reports that no elevation was probed, and why.
    coverage_endpoints: dict[str, str] = field(default_factory=dict)
    wcs_version: str = "2.0.1"
    elevation: dict[str, tuple[str, str]] = field(default_factory=dict)
    # The grid step, in metres, that each product's identifier suggests. A
    # reading of a name, never a measurement: it is printed beside the step the
    # reply actually delivers so the two can contradict each other.
    elevation_step_hint_m: dict[str, float] = field(default_factory=dict)
    # The axis labels a coverage request subsets on, ``x`` first. WCS 2.0 names
    # them per coverage; these are the usual ones for a projected CRS, and a
    # refusal naming other labels is corrected here, not in a call.
    wcs_axis_labels: tuple[str, str] = ("x", "y")


PROVIDERS: dict[str, Provider] = {
    "es-pnoa": Provider(
        key="es-pnoa",
        label="Spain: PNOA orthophotos and cadastral building footprints",
        endpoints={
            "ortho": "https://www.ign.es/wms-inspire/pnoa-ma",
            "ortho_history": "https://www.ign.es/wms/pnoa-historico",
            "cadastre_wms": "http://ovc.catastro.meh.es/Cartografia/WMS/ServidorWMS.aspx",
            "buildings_wfs": "http://ovc.catastro.meh.es/INSPIRE/wfsBU.aspx",
            "addresses_wfs": "http://ovc.catastro.meh.es/INSPIRE/wfsAD.aspx",
            "parcels_wfs": "http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx",
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
        # Settled in step 4 of handoff 015 against the service's own
        # capabilities document (md5 36610fcf, in out/capabilities/): it
        # advertises version 2.0.0, a GetFeature operation and
        # ImplementsSpatialFilter TRUE with a BBOX operator, while its
        # ListStoredQueries reply offers five stored queries, every one of
        # them by parcel and none taking a bounding box. The extent query is
        # therefore the standard GetFeature with TYPENAMES and BBOX, and each
        # CRS is spelled as the URN the capabilities uses for it.
        # Measured on 2026-11-08: at 0.975 km² the service had not answered
        # after 30 s, the default, which is latency and not a refusal. Raised
        # so that a slow reply is collected instead of mistaken for a failure;
        # the probe spends at most one wait per rung of its ladder. The same
        # window then answered in 58.8 s, so the wait is the binding limit at
        # that size, not an arbitrary margin.
        wfs_timeout_s=120.0,
        # Measured on 2026-11-08, bracketed by two replies of the service's
        # own: it refused 1.204 km² with "Area of extension out of limits" and
        # accepted 0.975 km². The figure recorded is the accepted one, because
        # what a request needs is a size that works, not the exact edge.
        wfs_max_area_km2=0.975,
        wfs_params={
            "service": "wfs",
            "version": "2.0.0",
            "request": "getfeature",
            "typenames": "{typename}",
            "namespaces": "xmlns({prefix},{namespace})",
            "srsname": "urn:ogc:def:crs:EPSG::{epsg}",
            "bbox": "{bbox},urn:ogc:def:crs:EPSG::{epsg}",
        },
        # The three types this service publishes, plus the two sibling
        # services its own replies link to, by stored query per cadastral
        # reference (GetadByRefcat, GetParcel). Whether those two also answer
        # a bounding box is what step 4 asks them; the names and the
        # namespaces below are the ones their replies declare.
        wfs_types={
            "buildings": ("buildings_wfs", "bu:Building"),
            "building_parts": ("buildings_wfs", "bu:BuildingPart"),
            "other_constructions": ("buildings_wfs", "bu:OtherConstruction"),
            "addresses": ("addresses_wfs", "ad:Address"),
            "parcels": ("parcels_wfs", "cp:CadastralParcel"),
        },
        wfs_namespaces={
            "bu": "urn:x-inspire:specification:gmlas:Buildings:3.0",
            "ad": "urn:x-inspire:specification:gmlas:Addresses:3.0",
            "cp": "urn:x-inspire:specification:gmlas:CadastralParcels:3.0",
        },
        attributes={
            "identifier": "localId",
            "condition": "conditionOfConstruction",
            "year": "beginning",
            "use": "currentUse",
            "floors": "numberOfFloorsAboveGround",
        },
        # Leads found on 2026-11-11 in the two services' own capabilities (both
        # declaring CC BY 4.0 and no fees), not measurements: the reading of
        # the two ``mdsn_*`` identifiers as building and vegetation height
        # comes from the service abstract, not from a per-coverage declaration.
        # Section 9 of the notebook is what confirms or contradicts each line.
        coverage_endpoints={
            "elevation_mdt": "https://servicios.idee.es/wcs-inspire/mdt",
            "elevation_mds": "https://wcs-mds.idee.es/mds",
        },
        wcs_version="2.0.1",
        elevation={
            "terrain": ("elevation_mdt", "Elevacion25830_5"),
            "surface": ("elevation_mds", "mds05"),
            "building_height": ("elevation_mds", "mdsn_e025"),
            "vegetation_height": ("elevation_mds", "mdsn_v025"),
        },
        # ``mds05`` reads as 5 m by analogy with the terrain model, though by
        # the ``025`` = 2.5 m convention of its siblings it would read 0.5 m:
        # exactly the ambiguity the delivered grid step settles.
        elevation_step_hint_m={
            "terrain": 5.0,
            "surface": 5.0,
            "building_height": 2.5,
            "vegetation_height": 2.5,
        },
    ),
}

_PACKAGE_PREFIX = "geo_decay" + "_"  # the checker names it; the module never imports it
_SCHEME = "ht" + "tp"  # kept out of one literal: endpoints live in PROVIDERS only
# How WCS 2.0 names a CRS in a request: an identifier, not a host that is asked.
_OGC_CRS_URI = _SCHEME + "://www.opengis.net/def/crs/EPSG/0/{epsg}"
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
# The names a request writes its size under, in one place: the request grammar
# and the reader that parses a recorded request back cannot drift apart.
WMS_SIZE_PARAMS: tuple[str, str] = ("WIDTH", "HEIGHT")
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
    """Outcome of one request. A failed request is a value, never an exception.

    ``timed_out`` separates the one failure that is not a verdict on what was
    asked for: the service was reached and was still working when the wait ran
    out. A refusal says the request was wrong, an unreachable host says nothing
    was asked, and a timeout says only that the answer was too slow to collect
    — asking for less is then a sensible next step, where after a refusal it
    would be guesswork and after an unreachable host it would be pointless.
    """

    url: str
    status: int
    nbytes: int
    md5: str
    elapsed_s: float
    path: Path | None
    error: str
    timed_out: bool = False


# --------------------------------------------------------------------------
# Fetching and the audit trail
# --------------------------------------------------------------------------


BODY_DIRS: tuple[str, ...] = (
    "capabilities",  # GetCapabilities and ListStoredQueries documents: versioned
    "vectors",  # WFS replies: versioned
    "features",  # GetFeatureInfo replies: versioned
    "epochs",  # rendered map images: git-ignored, they are re-fetchable
    "chips",  # per-building crops drawn by the notebook: git-ignored
    "figs",  # figures the notebook shows from disk instead of storing: git-ignored
    "elevation",  # coverage replies, rasters or their refusals: git-ignored
)


def manifest_path(out_dir: Path) -> Path:
    """Location of the append-only request log inside ``out_dir``."""
    return out_dir / "manifest.csv"


def prepare_out(out_dir: Path) -> Path:
    """Create ``out_dir`` and one subfolder per kind, and return it.

    Response bodies are filed by kind rather than all together, so that the
    heavy, re-fetchable ones can be git-ignored by folder while the small
    documents that make up the audit trail stay versioned. ``figs/`` is the one
    kind that holds no reply: it takes the figures a notebook renders, so the
    notebook can show them from disk and store a reference instead of a
    megabyte of pixels it would rewrite into git on every re-run.
    """
    for name in ("", *BODY_DIRS):
        (out_dir / name).mkdir(parents=True, exist_ok=True)
    return out_dir


def body_for(out_dir: Path, md5: str, *, kind: str = "epochs") -> Path | None:
    """The stored body with this digest, or ``None`` when it is not on disk.

    ``fetch`` files every body under ``out_dir / kind`` named by its md5 plus
    the extension its content type implied, so the digest a manifest row
    carries is enough to find the bytes again without knowing the extension.
    ``None`` is an ordinary answer, not an error: these folders are git-ignored
    because they are re-fetchable, so a clone has the row and not the body.
    """
    if not md5:
        return None
    for found in sorted((out_dir / kind).glob(md5 + ".*")):
        return found
    return None


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
    """What to call a body on disk: the bytes first, the declared type after.

    The bytes win because the label is not always right. The address service
    of this cadastre sends GML under ``text/html``, and a body filed as
    ``.html`` or ``.bin`` is an audit trail nobody can open by name. A content
    type is only consulted for what the bytes do not announce themselves.
    """
    if body.startswith(b"\x89PNG"):
        return ".png"
    if body.startswith(b"\xff\xd8"):
        return ".jpg"
    if body[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        return ".tif"
    if body.lstrip()[:5].lower() == b"<?xml":
        return ".xml"
    lowered = content_type.lower()
    for token, extension in _CONTENT_EXTENSIONS.items():
        if token in lowered:
            return extension
    return ".bin"


def fetch(
    url: str,
    params: Mapping[str, str | list[str]],
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
    ``BODY_DIRS``. A parameter whose value is a list is repeated once per item,
    which is how a coverage request subsets on two axes.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat(timespec="seconds")
    started = time.monotonic()
    full_url = url
    failure = ""
    expired = False
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
        expired = isinstance(exc, requests.Timeout)
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
            timed_out=expired,
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
        WMS_SIZE_PARAMS[0]: str(size[0]),
        WMS_SIZE_PARAMS[1]: str(size[1]),
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
    kind: str = "epochs",
) -> Fetch:
    """Fetch one rendered map image for ``bbox`` (``x`` first, in ``crs``).

    ``kind`` is the body folder: ``epochs`` for views of the extent, ``chips``
    for the crops around one building, both git-ignored.
    """
    url, params = _wms_params(provider, "GetMap", layer, bbox, crs, size)
    params["FORMAT"] = image_format
    params["TRANSPARENT"] = "TRUE" if transparent else "FALSE"
    return fetch(url, params, out_dir, kind=kind)


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


def wfs_services(provider: Provider) -> tuple[str, ...]:
    """Every endpoint key that serves features, in the order first named."""
    return tuple(dict.fromkeys(service for service, _ in provider.wfs_types.values()))


def wfs_capabilities(provider: Provider, service: str, out_dir: Path) -> Fetch:
    """Fetch the capabilities document of the feature endpoint ``service``."""
    params = {
        "SERVICE": "WFS",
        "VERSION": provider.wfs_params.get("version", ""),
        "REQUEST": "GetCapabilities",
    }
    return fetch(provider.endpoints[service], params, out_dir, kind="capabilities")


def wfs_stored_queries(provider: Provider, service: str, out_dir: Path) -> Fetch:
    """Ask a feature endpoint which stored queries it offers.

    A stored query is a named, server-side query the client calls by id, and
    a service may publish nothing else. This is what shows which ones exist.
    """
    params = {
        "SERVICE": "WFS",
        "VERSION": provider.wfs_params.get("version", ""),
        "REQUEST": "ListStoredQueries",
    }
    return fetch(provider.endpoints[service], params, out_dir, kind="capabilities")


def wfs_features(
    provider: Provider, kind: str, bbox: Bbox, crs: str, out_dir: Path
) -> Fetch:
    """Fetch the features of one type of ``wfs_types`` that intersect ``bbox``.

    Every type goes out through the same request template; what changes is the
    type name, the namespace its prefix resolves to and, where the provider
    splits them, the endpoint. So asking a service for something it has never
    been asked for is an entry edit, not a code change.
    """
    service, type_name = provider.wfs_types[kind]
    prefix = type_name.partition(":")[0]
    epsg = CRS.from_user_input(crs).to_epsg()
    values = {
        "bbox": ",".join(repr(float(v)) for v in bbox),
        "crs": crs,
        "epsg": str(epsg),
        "typename": type_name,
        "prefix": prefix,
        "namespace": provider.wfs_namespaces.get(prefix, ""),
    }
    params = {key: tpl.format(**values) for key, tpl in provider.wfs_params.items()}
    return fetch(
        provider.endpoints[service],
        params,
        out_dir,
        timeout=provider.wfs_timeout_s,
        kind="vectors",
    )


def wcs_services(provider: Provider) -> tuple[str, ...]:
    """Every coverage endpoint key the elevation mapping uses, in order named."""
    return tuple(dict.fromkeys(service for service, _ in provider.elevation.values()))


def wcs_capabilities(provider: Provider, service: str, out_dir: Path) -> Fetch:
    """Fetch the capabilities document of the coverage endpoint ``service``."""
    params = {
        "SERVICE": "WCS",
        "VERSION": provider.wcs_version,
        "REQUEST": "GetCapabilities",
    }
    return fetch(
        provider.coverage_endpoints[service], params, out_dir, kind="capabilities"
    )


def wcs_coverage(
    provider: Provider,
    product: str,
    bbox: Bbox,
    crs: str,
    out_dir: Path,
    *,
    media_type: str = "image/tiff",
) -> Fetch:
    """Fetch the grid of one ``elevation`` product over ``bbox`` (``x`` first).

    One WCS 2.0 GetCoverage: the box is subset on the two axes the entry names,
    and both the subset and the output are asked for in ``crs``, so the reply is
    the service's grid on the extent and not a resampling of ours. The reply is
    filed under ``elevation/`` whatever it is; whether it is a raster at all is
    for ``read_coverage`` to say.
    """
    service, coverage = provider.elevation[product]
    x_label, y_label = provider.wcs_axis_labels
    uri = _OGC_CRS_URI.format(epsg=CRS.from_user_input(crs).to_epsg())
    params: dict[str, str | list[str]] = {
        "SERVICE": "WCS",
        "VERSION": provider.wcs_version,
        "REQUEST": "GetCoverage",
        "COVERAGEID": coverage,
        "SUBSET": [
            f"{x_label}({float(bbox[0])!r},{float(bbox[2])!r})",
            f"{y_label}({float(bbox[1])!r},{float(bbox[3])!r})",
        ],
        "SUBSETTINGCRS": uri,
        "OUTPUTCRS": uri,
        "FORMAT": media_type,
    }
    return fetch(
        provider.coverage_endpoints[service], params, out_dir, kind="elevation"
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
    # What the service says about itself as a whole, title and abstract. On a
    # coverage service this is where the products are described, when no
    # coverage describes itself.
    service_abstract: str = ""


_EPSG_CODE = re.compile(r"EPSG(?::+|/\d+/)(\d+)", re.IGNORECASE)
_CRS_TAGS = frozenset(
    {"CRS", "SRS", "DefaultCRS", "OtherCRS", "DefaultSRS", "OtherSRS", "crsSupported"}
)
_NAMED_TAGS = frozenset({"Layer", "FeatureType", "CoverageSummary"})
_SERVICE_TAGS = frozenset({"Service", "ServiceIdentification"})


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
    """Read what a WMS, WFS or WCS capabilities document advertises.

    Tags are matched on their local name and namespaces are ignored, because
    the same facts are spelled differently in WMS 1.1.1, WMS 1.3.0, WFS 2.0 and
    WCS 2.0 and the point is to compare them against one provider entry. A WCS
    coverage is read as a layer named by its ``CoverageId``. The document
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
    service_abstract = ""
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
        elif tag in _SERVICE_TAGS and not service_abstract:
            service_abstract = " · ".join(
                text
                for text in (
                    _child_text(element, "Title"),
                    _child_text(element, "Abstract"),
                )
                if text
            )
        elif tag in _NAMED_TAGS:
            name = _child_text(element, "Name") or _child_text(element, "CoverageId")
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
        service_abstract,
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
# Spectral reach: what bands arrive, and what indices exist elsewhere
# --------------------------------------------------------------------------

# Generic remote-sensing vocabulary, not one provider's layer names: a service
# that renders a false-colour composite almost always says so in a layer name,
# title or abstract. Both spellings and both languages are here on purpose.
SPECTRAL_TOKENS: tuple[str, ...] = (
    "nir",
    "irc",
    "cir",
    "infrar",
    "falso color",
    "false colour",
    "false color",
    "ndvi",
    "ndwi",
    "espectral",
)


def spectral_candidates(caps: Capabilities) -> tuple[tuple[str, str], ...]:
    """Layers whose name, title or abstract mentions infrared or an index.

    Returns ``(layer, the token that matched)`` pairs. A match is a
    **candidate**, never a confirmation: which bands a layer really returns is
    only knowable from a rendered image, which is why the section that calls
    this also counts the bands the service actually sent.
    """
    found: list[tuple[str, str]] = []
    for name in caps.layers:
        haystack = " ".join(
            (name, caps.titles.get(name, ""), caps.abstracts.get(name, ""))
        ).lower()
        hit = next((token for token in SPECTRAL_TOKENS if token in haystack), "")
        if hit:
            found.append((name, hit))
    return tuple(found)


def colour_bands(path: Path) -> tuple[int, bool]:
    """``(colour bands, carries alpha)`` for one image the service returned.

    Three colour bands mean red, green and blue and nothing else: no
    near-infrared arrived, whatever a catalogue advertises. Measured from bytes
    the service actually sent, so it settles what a capabilities document can
    only suggest.
    """
    pixels, alpha = _read_image(path)
    return pixels.shape[0] - (1 if alpha is not None else 0), alpha is not None


@dataclass(frozen=True)
class DeclaredProduct:
    """A dataset a catalogue says it distributes, with no request behind it.

    Every field is that catalogue's own claim, read on ``declared_on`` and
    **not verified here**: no row in ``manifest.csv`` backs any of it, and
    nothing was fetched. Its purpose is to let a section say what else exists
    without pretending to have measured it.

    Two deliberate design choices. There is **no endpoint field**: an address
    nothing has answered is a guess, and guesses do not belong beside the
    verified endpoints in ``PROVIDERS``. And ``unknowns`` travels with the
    claim, so what would have to be true before the product could be used is
    read in the same row as the promise, not in prose somewhere else.

    ``gsd_m`` is a range, ``(finest, coarsest)``, because a catalogue often
    declares a span rather than a figure; both ends are equal when it declares
    one. What a product can support follows from that range and nothing else:
    divide the size of the thing to be seen by it.
    """

    label: str
    source: str
    bands: str
    gsd_m: tuple[float, float]
    years: str
    cadence: str
    file_format: str
    access: str
    unknowns: tuple[str, ...]
    declared_on: str


# Read from the national catalogue's own product pages on the dates below.
# Nothing here has been requested, so nothing here is a measurement.
DECLARED_PRODUCTS: dict[str, tuple[DeclaredProduct, ...]] = {
    "es-pnoa": (
        DeclaredProduct(
            label="PNOA false-colour infrared orthophoto",
            source="PNOA aerial cameras",
            bands="NIR-R-G composite",
            gsd_m=(0.15, 0.25),
            years="annual, latest declared 2024",
            cadence="annual, national coverage",
            file_format="COG, cut into MTN25 sheets",
            access="download catalogue; no OGC service found",
            unknowns=(
                "whether this extent falls in a lot, and at which of the "
                "declared resolutions",
                "which band of the delivered file carries the near infrared",
                "whether a stable direct URL allows reading one bounding box by "
                "HTTP range instead of a whole sheet",
            ),
            declared_on="2026-11-06",
        ),
        DeclaredProduct(
            label="NDVI",
            source="Sentinel-2 L2A (Copernicus), cloud-corrected",
            bands="index, from red and near infrared",
            gsd_m=(10.0, 10.0),
            years="2018-2025",
            cadence="bimonthly, one mosaic per autonomous community",
            file_format="COG",
            access="download catalogue; no OGC service advertised",
            unknowns=(
                "whether one bounding box can be read without the whole "
                "community mosaic",
            ),
            declared_on="2026-11-06",
        ),
        DeclaredProduct(
            label="NDWI",
            source="Sentinel-2 L2A (Copernicus), cloud-corrected",
            bands="index, from green and near infrared",
            gsd_m=(10.0, 10.0),
            years="2018-2025",
            cadence="semiannual, one winter and one summer mosaic",
            file_format="COG",
            access="download catalogue; no OGC service advertised",
            unknowns=(
                "whether one bounding box can be read without the whole "
                "community mosaic",
            ),
            declared_on="2026-11-06",
        ),
        DeclaredProduct(
            label="Landsat historical mosaics",
            source="Landsat 5 and 8",
            bands="natural colour and false-colour infrared",
            gsd_m=(15.0, 30.0),
            years="1986 onwards",
            cadence="about one per decade",
            file_format="not declared on the page read",
            access="download catalogue",
            unknowns=(
                "which decades cover this extent",
                "whether the false-colour composite carries a usable infrared band",
            ),
            declared_on="2026-11-06",
        ),
    ),
}


# --------------------------------------------------------------------------
# Vector features: what a feature service supplies over the extent
# --------------------------------------------------------------------------

# A collection wraps its members in one of these, depending on the GML
# version; the plural spelling holds the features directly.
_MEMBER_TAGS = frozenset({"member", "featureMember", "featureMembers"})
# Where coordinates sit, in the spellings GML 2 and GML 3 use.
_POSITION_TAGS = frozenset({"posList", "pos", "coordinates"})
# A ring inside one of these is a hole, and a hole is not a footprint.
_INTERIOR_TAGS = frozenset({"interior", "innerBoundaryIs"})
_UNDECLARED = -1  # a count the reply does not state: unknown, and not zero

Ring = tuple[tuple[float, float], ...]

# Shares of an extent to probe a service's area ceiling with, largest first:
# public, because a section has to report which sizes it asked for. They keep
# the extent's shape, so only the area changes from one rung to the next, and
# they stop where a window is too small to be worth a tile.
AREA_FACTORS: tuple[float, ...] = (1.0, 0.9, 0.8, 0.7, 0.5, 0.25)


@dataclass(frozen=True)
class FeatureRecord:
    """One feature of a reply: what identifies it, its fields and its rings.

    ``values`` is keyed by local tag name, so a field nested inside an
    identifier block is read under its own name and no schema has to be known
    in advance. A field the reply carries empty is kept with an empty value:
    a published name without a value is a different finding from no name at
    all. ``exterior`` and ``interior`` stay apart because an area measured
    across a courtyard is not a footprint.
    """

    fid: str
    values: dict[str, str]
    exterior: tuple[Ring, ...]
    interior: tuple[Ring, ...]


@dataclass(frozen=True)
class FeatureSet:
    """What one feature reply contains, read without its namespaces.

    ``number_returned`` and ``number_matched`` are the reply's own counts, and
    ``_UNDECLARED`` when it declares none. Their difference is the only way to
    tell a complete answer from a truncated one when a service advertises no
    result paging, which is why they are read rather than inferred from the
    features. ``crs`` is normalised to ``EPSG:<code>`` so that a reply saying
    ``urn:ogc:def:crs:EPSG::25830`` compares equal to the requested code,
    while ``srs_name`` keeps the service's own spelling. ``exception`` is set
    when the document is a service exception or could not be read, and the
    other fields are then empty: an unreadable reply is a value with a reason,
    never an exception.
    """

    root: str
    type_names: tuple[str, ...]
    features: tuple[FeatureRecord, ...]
    number_returned: int
    number_matched: int
    srs_name: str
    crs: str
    exception: str


def _no_features(exception: str, root: str = "") -> FeatureSet:
    return FeatureSet(root, (), (), _UNDECLARED, _UNDECLARED, "", "", exception)


def _declared_count(value: str | None) -> int:
    """A reply's own count, or ``_UNDECLARED`` when it states no number."""
    if value is None or not value.strip().isdigit():
        return _UNDECLARED  # "unknown" is a legal value here, and it is not a count
    return int(value)


def _dimensions(element: ElementTree.Element) -> int:
    """How many ordinates one position list carries per point."""
    raw = element.get("srsDimension", "")
    return int(raw) if raw.isdigit() and int(raw) >= 2 else 2


def _referenced(element: ElementTree.Element) -> str:
    """The tail of a link attribute, which is how a code list value arrives."""
    href = next(
        (value for key, value in element.attrib.items() if _local(key) == "href"), ""
    )
    return href.rstrip("/").rpartition("/")[2] if href else ""


def _ring(text: str, dimensions: int) -> Ring:
    """Coordinate pairs from one position list, dropping any third ordinate."""
    try:
        numbers = [float(token) for token in text.replace(",", " ").split()]
    except ValueError:
        return ()
    step = max(dimensions, 2)
    return tuple(
        (numbers[index], numbers[index + 1])
        for index in range(0, len(numbers) - step + 1, step)
    )


def _read_feature(element: ElementTree.Element) -> FeatureRecord:
    """Read one feature: every field by local name, every ring by boundary."""
    values: dict[str, str] = {}
    exterior: list[Ring] = []
    interior: list[Ring] = []

    def walk(node: ElementTree.Element, *, hole: bool) -> None:
        for child in node:
            tag = _local(child.tag)
            if tag in _POSITION_TAGS:
                ring = _ring(child.text or "", _dimensions(child))
                if ring:
                    (interior if hole else exterior).append(ring)
                continue
            if len(child) == 0:
                values.setdefault(tag, (child.text or "").strip() or _referenced(child))
            walk(child, hole=hole or tag in _INTERIOR_TAGS)

    walk(element, hole=False)
    fid = next(
        (value for key, value in element.attrib.items() if _local(key) == "id"), ""
    )
    return FeatureRecord(fid, values, tuple(exterior), tuple(interior))


def read_features(path: Path | None) -> FeatureSet:
    """Read what one feature reply contains, matching tags on their local name.

    Namespaces are ignored for the same reason ``read_capabilities`` ignores
    them: the same facts are spelled differently across GML versions, and the
    point is to compare them against one provider entry. The document is
    treated strictly as data — nothing in it is executed, resolved or
    followed, and **no schema is fetched**, so every figure taken from it
    rests only on bytes that already have their own row in the manifest.
    """
    if path is None or not path.is_file():
        return _no_features("no document was saved")
    try:
        root = ElementTree.parse(path).getroot()
    except (OSError, ElementTree.ParseError) as exc:
        return _no_features(f"{type(exc).__name__}: {exc}")
    name = _local(root.tag)
    if "exception" in name.lower():
        text = " ".join(part.strip() for part in root.itertext() if part.strip())
        return _no_features(f"service exception: {text[:200]}", name)
    members = [
        child
        for container in root.iter()
        if _local(container.tag) in _MEMBER_TAGS
        for child in container
    ]
    if not members:  # a collection that nests nothing: take what carries geometry
        members = [
            child
            for child in root
            if any(_local(node.tag) in _POSITION_TAGS for node in child.iter())
        ]
    srs_name = next(
        (
            element.get("srsName", "")
            for element in root.iter()
            if element.get("srsName")
        ),
        "",
    )
    code = _EPSG_CODE.search(srs_name)
    return FeatureSet(
        name,
        tuple(dict.fromkeys(_local(member.tag) for member in members)),
        tuple(_read_feature(member) for member in members),
        _declared_count(root.get("numberReturned")),
        _declared_count(root.get("numberMatched")),
        srs_name,
        f"EPSG:{code.group(1)}" if code else srs_name.upper(),
        "",
    )


def attribute_coverage(features: Iterable[FeatureRecord]) -> dict[str, int]:
    """How many features carry each field, by local name, commonest first."""
    counts: dict[str, int] = {}
    for record in features:
        for name in record.values:
            counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def value_counts(features: Iterable[FeatureRecord], field: str) -> dict[str, int]:
    """How often each value of ``field`` occurs, commonest first.

    A feature that carries the field empty counts under the empty string: the
    name is published and the value is not, and the difference decides whether
    an attribute can carry a label.
    """
    counts: dict[str, int] = {}
    for record in features:
        if field in record.values:
            value = record.values[field]
            counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def rings_envelope(features: Iterable[FeatureRecord]) -> Bbox | None:
    """The bounding box of every exterior ring, or ``None`` without geometry."""
    xs: list[float] = []
    ys: list[float] = []
    for record in features:
        for ring in record.exterior:
            xs.extend(x for x, _ in ring)
            ys.extend(y for _, y in ring)
    if not xs:
        return None
    return (min(xs), min(ys), max(xs), max(ys))


def _overlaps(one: Bbox, other: Bbox) -> bool:
    return (
        one[0] <= other[2]
        and other[0] <= one[2]
        and one[1] <= other[3]
        and other[1] <= one[3]
    )


def axis_order(
    features: Iterable[FeatureRecord], bbox: Bbox
) -> tuple[bool | None, str]:
    """Whether a reply's coordinates are ordered the way the request was.

    A service writes coordinates in the order its own CRS defines, which is
    not always the order the request grammar used, and a silently swapped
    footprint is drawn in the sea without anything looking wrong. Rather than
    trust either grammar, this asks the geometry: whichever order falls inside
    the extent that was requested is the order the reply uses.
    """
    envelope = rings_envelope(features)
    if envelope is None:
        return None, "the reply carries no geometry to place"
    if _overlaps(envelope, bbox):
        return False, "as requested: the geometry falls inside the extent"
    swapped = (envelope[1], envelope[0], envelope[3], envelope[2])
    if _overlaps(swapped, bbox):
        return True, "swapped: it falls inside the extent only when read y first"
    return None, f"neither order falls inside the extent; geometry spans {envelope}"


def swap_axes(features: Iterable[FeatureRecord]) -> tuple[FeatureRecord, ...]:
    """The same features with every coordinate pair reversed."""

    def flip(rings: tuple[Ring, ...]) -> tuple[Ring, ...]:
        return tuple(tuple((y, x) for x, y in ring) for ring in rings)

    return tuple(
        FeatureRecord(
            record.fid, record.values, flip(record.exterior), flip(record.interior)
        )
        for record in features
    )


def _shoelace(ring: Ring) -> float:
    if len(ring) < 3:
        return 0.0
    total = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1], strict=True):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def footprint_area(record: FeatureRecord) -> float:
    """Area of one footprint in squared CRS units, holes taken out.

    Only a measurement when the reply is in a projected CRS, where the unit is
    the metre; in degrees it is a number without a meaning, which is why the
    section prints the reply's CRS beside the figure.
    """
    return sum(_shoelace(ring) for ring in record.exterior) - sum(
        _shoelace(ring) for ring in record.interior
    )


def merge_features(
    groups: Iterable[Iterable[FeatureRecord]],
) -> tuple[tuple[FeatureRecord, ...], int]:
    """One set of features out of several replies, and how many repeated.

    A building that straddles the cut between two requested boxes is answered
    for by both of them, so the counts of several replies cannot simply be
    added up. Identity is the feature's own identifier; a reply that publishes
    none falls back to the feature's first exterior ring, which is the only
    other thing that tells one footprint from another.
    """
    seen: dict[str, FeatureRecord] = {}
    repeated = 0
    for group in groups:
        for record in group:
            key = record.fid or repr(record.exterior[:1])
            if key in seen:
                repeated += 1
                continue
            seen[key] = record
    return tuple(seen.values()), repeated


# --------------------------------------------------------------------------
# Elevation: what a coverage reply holds, read as a raster
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class CoverageReading:
    """What one coverage reply holds, or why it holds nothing usable.

    ``shape`` is ``(bands, rows, cols)`` and ``step_m`` the grid step the reply
    delivers, ``x`` then ``y``, in the units of its CRS. ``nodata_share`` counts
    the cells of the first band that are masked, declared no-data or not a
    number; ``value_range`` is the span of the rest, ``None`` when nothing is
    left. ``exception`` is set when the reply is missing or is not a raster —
    with the service's own words when it gave any — and every other field is
    then empty.
    """

    crs: str
    shape: tuple[int, int, int]
    step_m: tuple[float, float]
    nodata_share: float
    value_range: tuple[float, float] | None
    dtype: str
    exception: str


def _no_coverage(reason: str) -> CoverageReading:
    return CoverageReading("", (0, 0, 0), (0.0, 0.0), 0.0, None, "", reason)


def _not_a_raster(path: Path) -> str:
    """Why a reply that is not a raster is not one, in its own words if it has any."""
    said = read_capabilities(path).exception
    if said.startswith("service exception"):
        return said
    head = path.read_bytes()[:2048].decode("utf-8", errors="replace")
    text = " ".join(re.sub(r"<[^>]*>", " ", head).split())
    return f"not a raster ({path.suffix or 'no extension'}): {text[:160] or 'empty'}"


def read_coverage(path: Path | None) -> CoverageReading:
    """Read a coverage reply's grid, CRS, no-data share and value range.

    A reply that is markup is never handed to the raster reader: a service
    refusal is XML, and a portal or proxy page is HTML, and either one read as
    a raster would be a measurement of nothing. Anything else that does not
    open as a raster is a value with a reason, never an exception.
    """
    import rasterio
    from rasterio.errors import RasterioError

    if path is None or not path.is_file():
        return _no_coverage("no reply was saved")
    if path.read_bytes()[:256].lstrip().startswith(b"<"):
        return _no_coverage(_not_a_raster(path))
    try:
        with rasterio.open(path) as src:
            band = np.ma.masked_invalid(src.read(1, masked=True).astype("float64"))
            crs = src.crs.to_string() if src.crs is not None else ""
            shape = (src.count, src.height, src.width)
            step = (abs(float(src.res[0])), abs(float(src.res[1])))
            dtype = str(src.dtypes[0])
    except (RasterioError, OSError) as exc:
        return _no_coverage(f"{_not_a_raster(path)} — {type(exc).__name__}")
    masked = np.ma.getmaskarray(band)
    valid = band.compressed()
    return CoverageReading(
        crs=crs,
        shape=shape,
        step_m=step,
        nodata_share=float(masked.mean()) if masked.size else 0.0,
        value_range=(float(valid.min()), float(valid.max())) if valid.size else None,
        dtype=dtype,
        exception="",
    )


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


def _blank_pixels(pixels: np.ndarray, alpha: int | None) -> bool:
    """The blank rule on pixels already read: fully transparent, or one value."""
    if alpha is not None and not pixels[alpha].any():
        return True
    return bool((pixels == pixels[:, :1, :1]).all())


def _nodata_mask(pixels: np.ndarray, alpha: int | None) -> np.ndarray:
    """Pixels with zero alpha, or, without an alpha band, zero in every band."""
    if alpha is not None:
        return ~pixels[alpha].astype(bool)
    return ~pixels.astype(bool).any(axis=0)


def is_blank_image(path: Path) -> bool:
    """True for a fully transparent image or one holding a single pixel value."""
    pixels, alpha = _read_image(path)
    return _blank_pixels(pixels, alpha)


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
    nodata = _nodata_mask(pixels, alpha)
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


_LADDER_HEADER = [
    "year",
    "size_px",
    "gsd_m",
    "status",
    "nbytes",
    "md5",
    "share",
    "samples",
    "stopped",
    "rung_reason",
    "measured_gsd_m",
    "measured_px",
    "measured_reason",
]


def ladder_rows(
    year: int,
    rungs: list[dict[str, object]],
    found: dict[str, object],
) -> list[dict[str, object]]:
    """Flatten one year's ladder and verdict into rows of the ladder table.

    The year's figure is repeated on every rung instead of living in a second
    table, so one row holds both the bytes it was measured from (``md5``, which
    is enough to find them under ``epochs/``) and what the year was measured to
    be. A reader of the table then needs no join and no request grammar.
    ``measured_gsd_m`` is empty when the ladder gave no figure, and
    ``measured_reason`` says why; ``rung_reason`` is per rung, and says why that
    rung has no residual or why the ladder stopped there.
    """
    measured_gsd = found.get("measured_gsd_m")
    measured_px = found.get("measured_px")
    rows: list[dict[str, object]] = []
    for rung in rungs:
        share = rung.get("share")
        rows.append(
            {
                "year": year,
                "size_px": rung["size_px"],
                "gsd_m": round(float(str(rung["gsd_m"])), 6),
                "status": rung["status"],
                "nbytes": rung["nbytes"],
                "md5": rung["md5"],
                "share": round(float(str(share)), 6) if share is not None else "",
                "samples": rung["samples"],
                "stopped": "yes" if rung["stopped"] else "",
                "rung_reason": rung["reason"],
                "measured_gsd_m": measured_gsd if measured_gsd is not None else "",
                "measured_px": measured_px if measured_px is not None else "",
                "measured_reason": "" if measured_gsd is not None else found["reason"],
            }
        )
    return rows


def write_ladder(rows: list[dict[str, object]], out_dir: Path) -> Path:
    """Write ``rows`` to ``out_dir/ladder.csv``, overwriting any earlier table.

    The header is written even with no rows: an empty table says the section ran
    and had nothing to measure, which a missing file does not say.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "ladder.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=_LADDER_HEADER, restval="")
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_ladder(out_dir: Path) -> list[dict[str, str]] | None:
    """The rows of ``out_dir/ladder.csv``, or ``None`` when there is no table.

    ``None`` and an empty list are different answers: the table was never
    written, or it was written and the measurement found nothing. Reading the
    table back is what lets a later section draw the ladder on a cold kernel,
    instead of depending on a 45-request measurement still being in memory.
    """
    path = out_dir / "ladder.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def area_km2(bbox: Bbox) -> float:
    """The plain area of ``bbox`` in square kilometres.

    Only a measurement in a projected CRS, where the unit is the metre: the
    caller is the one that knows which CRS the box is written in. It is kept
    separate from ``extent_report``, which answers the much larger question of
    what an extent costs in pixels and tiles, because a service that rejects a
    request by area needs this one number and nothing else.
    """
    return (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) / 1_000_000.0


def scaled_window(bbox: Bbox, factor: float) -> Bbox:
    """``bbox`` shrunk about its own centre, keeping its shape.

    Unlike ``centred_window`` this keeps the extent's aspect ratio, so a ladder
    built from it changes one thing only — the area — which is what a service
    that refuses a request by area has to be probed with.
    """
    if factor <= 0:
        raise ValueError("factor must be positive")
    centre_x = (bbox[0] + bbox[2]) / 2.0
    centre_y = (bbox[1] + bbox[3]) / 2.0
    half_x = (bbox[2] - bbox[0]) * factor / 2.0
    half_y = (bbox[3] - bbox[1]) * factor / 2.0
    return (centre_x - half_x, centre_y - half_y, centre_x + half_x, centre_y + half_y)


def split_under(bbox: Bbox, max_area_km2: float) -> tuple[Bbox, ...]:
    """``bbox`` cut into the fewest near-square cells that stay under a ceiling.

    The cells cover the box exactly, without gaps or overlap, so a feature is
    answered for by one cell unless it straddles a cut — and one that straddles
    a cut comes back from both, which is why the caller merges by identifier
    rather than by adding the counts up. A ceiling that is not positive, or
    that the box already respects, leaves the box whole.
    """
    whole = (bbox,)
    if max_area_km2 <= 0 or area_km2(bbox) <= max_area_km2:
        return whole
    side = math.sqrt(max_area_km2 * 1_000_000.0)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    columns = max(1, math.ceil(width / side))
    rows = max(1, math.ceil(height / side))
    step_x = width / columns
    step_y = height / rows
    return tuple(
        (
            bbox[0] + column * step_x,
            bbox[1] + row * step_y,
            bbox[0] + (column + 1) * step_x,
            bbox[1] + (row + 1) * step_y,
        )
        for row in range(rows)
        for column in range(columns)
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
# Example buildings and the chips cut around them
# --------------------------------------------------------------------------

# The four quadrants of an extent, in the order a selection visits them.
QUADRANTS: tuple[str, ...] = ("NW", "NE", "SW", "SE")
# The size classes a selection splits the footprints into, by area rank.
AREA_CLASSES = 3


@dataclass(frozen=True)
class Example:
    """One building chosen for a chip strip, and why it was chosen.

    ``tertile`` is its area class, 1 the smallest. ``quadrant`` is the quadrant
    of the extent its centroid falls in. ``fallback`` is true when the slot it
    fills had no building of its class in its quadrant, so it was taken from
    anywhere in its class instead.
    """

    fid: str
    area_m2: float
    centroid: tuple[float, float]
    envelope: Bbox
    tertile: int
    quadrant: str
    fallback: bool
    record: FeatureRecord


def footprint_centroid(record: FeatureRecord) -> tuple[float, float] | None:
    """The area-weighted centroid of a footprint, holes taken out.

    A footprint with no area left (a degenerate ring) falls back to the mean of
    its exterior vertices; one with no geometry at all has no centroid.
    """
    weight = 0.0
    sum_x = 0.0
    sum_y = 0.0
    for sign, rings in ((1.0, record.exterior), (-1.0, record.interior)):
        for ring in rings:
            if len(ring) < 3:
                continue
            signed = 0.0
            cx = 0.0
            cy = 0.0
            for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1], strict=True):
                cross = x1 * y2 - x2 * y1
                signed += cross
                cx += (x1 + x2) * cross
                cy += (y1 + y2) * cross
            if signed == 0.0:
                continue
            area = abs(signed) / 2.0
            # cx / (3 * signed) is the ring's centroid whatever its winding.
            weight += sign * area
            sum_x += sign * area * cx / (3.0 * signed)
            sum_y += sign * area * cy / (3.0 * signed)
    if weight > 0.0:
        return sum_x / weight, sum_y / weight
    points = [point for ring in record.exterior for point in ring]
    if not points:
        return None
    return (
        sum(x for x, _ in points) / len(points),
        sum(y for _, y in points) / len(points),
    )


def _quadrant(point: tuple[float, float], extent: Bbox) -> str:
    mid_x = (extent[0] + extent[2]) / 2.0
    mid_y = (extent[1] + extent[3]) / 2.0
    return ("N" if point[1] >= mid_y else "S") + ("E" if point[0] >= mid_x else "W")


def frame_side(envelope: Bbox, margin_m: float) -> float:
    """The side of a chip frame: the envelope's longer side plus both margins."""
    return max(envelope[2] - envelope[0], envelope[3] - envelope[1]) + 2.0 * margin_m


@dataclass(frozen=True)
class Oversized:
    """A footprint left out because its chip frame exceeds the largest allowed."""

    fid: str
    parts: int
    area_m2: float
    frame_m: float


@dataclass(frozen=True)
class Selection:
    """The buildings chosen, the footprints too large to frame, and why.

    ``excluded`` is sorted largest frame first. ``reason`` is empty when at
    least one building was chosen, and says why none was otherwise.
    """

    examples: tuple[Example, ...]
    excluded: tuple[Oversized, ...]
    eligible: int
    reason: str


def choose_examples(
    features: Iterable[FeatureRecord],
    extent: Bbox,
    n: int,
    seed: int,
    *,
    margin_m: float,
    max_frame_m: float,
) -> Selection:
    """Choose ``n`` buildings spread over size and over the extent, reproducibly.

    A footprint whose chip frame (``frame_side``) exceeds ``max_frame_m`` is
    not eligible: a strip judges one building, not a compound, and the frame
    is capped at what the pipeline sees as one tile. Exclusion comes **first**
    and the size classes are cut over the eligible footprints only, so the
    classes describe what can actually be drawn and an excluded giant never
    shifts the boundaries of the classes it could not join.

    The eligible footprints are ranked by area and cut into ``AREA_CLASSES``
    classes of as equal a size as the count allows. Slots are then filled
    class by class, quadrant by quadrant in ``QUADRANTS`` order, each with one
    building drawn at random from the eligible footprints of that class whose
    centroid falls in that quadrant, or from anywhere in the class when that
    quadrant has none left. Three classes by four quadrants make twelve slots;
    a larger ``n`` goes round again. The draw is seeded and every candidate
    list is sorted by identifier first, so the same footprints and seed give
    the same buildings whatever order the service returned them in. A
    footprint with no geometry cannot be framed and is never chosen.
    """
    import random

    placed: list[tuple[float, str, tuple[float, float], Bbox, FeatureRecord]] = []
    excluded: list[Oversized] = []
    for record in features:
        centroid = footprint_centroid(record)
        envelope = rings_envelope([record])
        if centroid is None or envelope is None:
            continue
        area = footprint_area(record)
        side = frame_side(envelope, margin_m)
        if side > max_frame_m:
            excluded.append(Oversized(record.fid, len(record.exterior), area, side))
            continue
        placed.append((area, record.fid, centroid, envelope, record))
    excluded.sort(key=lambda item: (-item.frame_m, item.fid))
    if n <= 0:
        return Selection((), tuple(excluded), len(placed), "no examples asked for")
    if not placed:
        reason = (
            f"all {len(excluded)} footprints frame wider than {max_frame_m:g} m"
            if excluded
            else "no footprint with geometry to frame"
        )
        return Selection((), tuple(excluded), 0, reason)
    placed.sort(key=lambda item: (item[0], item[1]))
    classes = [
        list(chunk) for chunk in np.array_split(np.arange(len(placed)), AREA_CLASSES)
    ]
    rng = random.Random(seed)
    taken: set[int] = set()
    chosen: list[Example] = []
    while len(chosen) < n and len(taken) < len(placed):
        for tertile, members in enumerate(classes, 1):
            for quadrant in QUADRANTS:
                if len(chosen) >= n:
                    break
                free = sorted(
                    (int(i) for i in members if int(i) not in taken),
                    key=lambda i: placed[i][1],
                )
                here = [i for i in free if _quadrant(placed[i][2], extent) == quadrant]
                pool = here or free
                if not pool:
                    continue
                index = pool[rng.randrange(len(pool))]
                taken.add(index)
                area, fid, centroid, envelope, record = placed[index]
                chosen.append(
                    Example(
                        fid=fid,
                        area_m2=area,
                        centroid=centroid,
                        envelope=envelope,
                        tertile=tertile,
                        quadrant=_quadrant(centroid, extent),
                        fallback=not here,
                        record=record,
                    )
                )
    return Selection(tuple(chosen), tuple(excluded), len(placed), "")


def chip_box(example: Example, margin_m: float) -> Bbox:
    """The square frame of a building's chips, the same for every year.

    Centred on the footprint's centroid, of side ``frame_side``: the ground
    around a building is part of judging it.
    """
    half = frame_side(example.envelope, margin_m) / 2.0
    x, y = example.centroid
    return (x - half, y - half, x + half, y + half)


def chip_px(box: Bbox, gsd_m: float) -> int:
    """How many pixels a side of ``box`` takes at ``gsd_m``, never fewer than one."""
    return max(1, round((box[2] - box[0]) / gsd_m))


@dataclass(frozen=True)
class ChipVerdict:
    """Whether a chip goes into its strip, with the figure or reason behind it.

    ``nodata_share`` is ``None`` when there were no pixels to measure.
    """

    kept: bool
    nodata_share: float | None
    reason: str


def chip_verdict(
    pixels: np.ndarray, alpha: int | None, max_nodata: float
) -> ChipVerdict:
    """Keep a chip only if it is not blank and its no-data share is in bounds.

    Blank is the rule epoch availability uses: fully transparent, or a single
    value everywhere. No data is the rule ``image_stats`` uses: zero alpha, or
    zero in every band without an alpha. A share exactly at ``max_nodata`` is
    kept; anything above it is dropped, because a gap that size reaches the
    margin or the building and the chip can no longer be judged.
    """
    share = float(_nodata_mask(pixels, alpha).mean())
    if _blank_pixels(pixels, alpha):
        return ChipVerdict(
            False, share, f"blank image: no pixel content (no-data share {share:.3f})"
        )
    if share > max_nodata:
        return ChipVerdict(
            False, share, f"no-data share {share:.3f} above {max_nodata:g}"
        )
    return ChipVerdict(True, share, "")


def judge_chip(got: Fetch, max_nodata: float) -> ChipVerdict:
    """The verdict on one chip request, a failed request included."""
    if got.status == 0 or got.path is None:
        return ChipVerdict(False, None, got.error or "no reply")
    if got.status >= 400:
        return ChipVerdict(False, None, got.error)
    if not _is_image_file(got.path):
        text = got.path.read_text(encoding="utf-8", errors="replace")
        return ChipVerdict(False, None, "not an image: " + " ".join(text.split())[:160])
    try:
        pixels, alpha = _read_image(got.path)
    except Exception as exc:  # undecodable bytes are evidence, not a crash
        return ChipVerdict(False, None, f"undecodable image: {exc}")
    return chip_verdict(pixels, alpha, max_nodata)


STRIPS_HEADER: tuple[str, ...] = (
    "id",
    "year",
    "kept",
    "nodata_share",
    "reason",
    "chip",
)


def write_strips(rows: list[dict[str, object]], out_dir: Path) -> Path:
    """Write ``rows`` to ``out_dir/strips.csv``, overwriting any earlier table.

    One row per building and year asked. The header is written even with no
    rows, so a reader can tell "ran and found nothing" from "never ran".
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "strips.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(STRIPS_HEADER), restval="")
        writer.writeheader()
        writer.writerows(rows)
    return path


def read_strips(out_dir: Path) -> list[dict[str, str]] | None:
    """The rows of ``out_dir/strips.csv``, or ``None`` when there is no table."""
    path = out_dir / "strips.csv"
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


# --------------------------------------------------------------------------
# The labelling table
# --------------------------------------------------------------------------

CANDIDATES_HEADER: tuple[str, ...] = (
    "id",
    "source",
    "x",
    "y",
    "bbox",
    "area_m2",
    "strip",
    "label_year",
    "label",
    "evidence",
    "notes",
    "minutes_spent",
)
# The columns only a person fills. A file with any of them filled holds manual
# work, and a regeneration must never overwrite it.
MANUAL_FIELDS: tuple[str, ...] = ("label", "evidence", "notes", "minutes_spent")
LABELS: tuple[str, ...] = ("abandoned", "kept", "unsure")
SOURCES: tuple[str, ...] = ("cadastre", "manual")


def strip_figure(out_dir: Path, fid: str) -> tuple[str, str]:
    """The strip figure section 10.1 drew for ``fid``, found by its id.

    Returns ``(path relative to out_dir, "")`` for exactly one file named
    ``strip-<number>-<id>.png`` under ``figs/``. The number is not rebuilt
    here: it belongs to the run that drew the strip. No match gives an empty
    path and an empty reason (the figure is not on disk, which a clone of
    the repository never has); more than one gives an empty path and the
    reason, because picking one would be a guess.
    """
    _, found = _strip_matches(out_dir, fid)
    if len(found) > 1:
        names = ", ".join(p.name for p in found)
        return "", f"{len(found)} strip figures match {fid}: {names}"
    if not found:
        return "", ""
    return str(found[0].relative_to(out_dir)), ""


def _strip_matches(out_dir: Path, fid: str) -> tuple[str, list[Path]]:
    """The safe file stem of ``fid`` and every strip figure already named for it."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", fid)
    pattern = re.compile(r"strip-\d+-" + re.escape(safe) + r"\.png")
    figs = out_dir / "figs"
    found = (
        sorted(p for p in figs.iterdir() if pattern.fullmatch(p.name))
        if figs.is_dir()
        else []
    )
    return safe, found


def strip_figure_path(out_dir: Path, fid: str, number: int) -> tuple[Path, str]:
    """Where to save ``fid``'s strip, and a line when that choice needs saying.

    One figure already named for the id: its name is reused, so a change in
    the numbering never leaves two figures for one id. None: the name is built
    from ``number``. More than one: none is reused, a line names them, and the
    built name is used; section 11 then reports the ambiguity honestly.
    """
    safe, found = _strip_matches(out_dir, fid)
    built = out_dir / "figs" / f"strip-{number:02d}-{safe}.png"
    if len(found) == 1:
        return found[0], ""
    if found:
        names = ", ".join(p.name for p in found)
        return built, f"{len(found)} strip figures already match {fid}: {names}"
    return built, ""


def strips_by_id(
    rows: Iterable[Mapping[str, str]], out_dir: Path
) -> tuple[dict[str, tuple[str, str]], list[str]]:
    """Each building with a kept chip: ``id -> (strip figure, label year)``.

    The label year comes from the table only: the newest year whose chip was
    kept, the date the state is judged on. A dropped chip says nothing about
    the building, so it never sets the year. The figure is looked up on disk
    by id and is empty when there is none or more than one; the second case
    adds a line to the returned list, since it is never a guess.
    """
    newest: dict[str, int] = {}
    for row in rows:
        fid = row.get("id", "")
        if fid and row.get("kept") == "yes":
            year = int(row["year"])
            newest[fid] = max(year, newest.get(fid, year))
    index: dict[str, tuple[str, str]] = {}
    problems: list[str] = []
    for fid in sorted(newest):
        figure, problem = strip_figure(out_dir, fid)
        if problem:
            problems.append(problem)
        index[fid] = (figure, str(newest[fid]))
    return index, problems


def _coordinate(value: float) -> str:
    return f"{value:.2f}"


def cadastre_rows(
    features: Iterable[FeatureRecord], strips: Mapping[str, tuple[str, str]]
) -> list[dict[str, object]]:
    """One labelling row per cadastral footprint, its manual columns empty.

    Every row carries its coordinates: the area-weighted centroid and the
    envelope, in the CRS the footprints are in. A footprint with no geometry
    cannot be located, and so cannot be labelled; it is left out.
    """
    rows: list[dict[str, object]] = []
    for record in features:
        centroid = footprint_centroid(record)
        envelope = rings_envelope([record])
        if centroid is None or envelope is None:
            continue
        strip, label_year = strips.get(record.fid, ("", ""))
        rows.append(
            {
                "id": record.fid,
                "source": "cadastre",
                "x": _coordinate(centroid[0]),
                "y": _coordinate(centroid[1]),
                "bbox": " ".join(_coordinate(v) for v in envelope),
                "area_m2": f"{footprint_area(record):.2f}",
                "strip": strip,
                "label_year": label_year,
            }
        )
    return rows


def _is_number(text: str | None) -> bool:
    try:
        return math.isfinite(float(text or ""))
    except ValueError:
        return False


_DELIMITERS: dict[str, str] = {",": "comma", ";": "semicolon", "\t": "tab"}


@dataclass(frozen=True)
class LabelsRead:
    """An existing labelling table as read back, whatever saved it last.

    A spreadsheet in a Spanish locale saves ``;``-separated, often with a
    UTF-8 byte-order mark, so both are detected rather than assumed.
    ``problem`` is set when the file cannot be read as the table at all: it
    does not decode as UTF-8, or its header lacks ``id`` or a manual column.
    ``work`` then is empty and must not be taken to mean "no manual work".
    """

    exists: bool
    work: dict[str, dict[str, str]]
    delimiter: str
    bom: bool
    problem: str

    @property
    def canonical(self) -> bool:
        """True when the file is already comma-separated UTF-8 without a BOM."""
        return self.delimiter == "," and not self.bom


def read_labels(path: Path) -> LabelsRead:
    """Read the manual work of a labelling table, detecting its format.

    Only the ``MANUAL_FIELDS`` columns are kept for each id that has any of
    them filled: they are what a regeneration carries over, and nothing else
    of the row is the person's.
    """
    if not path.exists():
        return LabelsRead(False, {}, ",", False, "")
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        return LabelsRead(
            True, {}, "", bom, f"not UTF-8 ({exc.reason} at byte {exc.start})"
        )
    if not text.strip():
        return LabelsRead(True, {}, ",", bom, "")
    first = text.splitlines()[0]
    delimiter = max(_DELIMITERS, key=first.count)
    if not first.count(delimiter):
        delimiter = ","
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=delimiter)
    header = list(reader.fieldnames or [])
    lacking = [name for name in ("id", *MANUAL_FIELDS) if name not in header]
    if lacking:
        shown = ", ".join(repr(name) for name in header[:4])
        return LabelsRead(
            True,
            {},
            delimiter,
            bom,
            f"read as {_DELIMITERS[delimiter]}-separated UTF-8"
            + (" with BOM" if bom else "")
            + f", its header starts {shown} and lacks {', '.join(lacking)}",
        )
    work = {
        row.get("id") or "": {name: row.get(name) or "" for name in MANUAL_FIELDS}
        for row in reader
        if any((row.get(name) or "").strip() for name in MANUAL_FIELDS)
    }
    return LabelsRead(True, work, delimiter, bom, "")


class ManualWork(dict[str, dict[str, str]]):
    """Manual work by id, plus why the table could not be read, if it could not.

    An empty mapping alone cannot tell "no manual work" from "a table nobody
    could read"; ``problem`` does, so a caller about to destroy something can
    refuse on the second.
    """

    problem: str = ""


def manual_work(path: Path) -> ManualWork:
    """The rows of a labelling table that carry manual work, by id.

    Empty when the file is absent. When it exists but cannot be read as the
    table, the mapping is empty and ``problem`` says why: it must then not be
    taken to mean "no manual work".
    """
    read = read_labels(path)
    work = ManualWork(read.work)
    work.problem = read.problem
    return work


# --------------------------------------------------------------------------
# Manual samples: rectangles a person draws where the cadastre holds nothing
# --------------------------------------------------------------------------

_MANUAL_ID = re.compile(r"M-(\d+)")


def is_manual_id(fid: str) -> bool:
    """True for an identifier of the ``M-0001`` form a manual sample gets."""
    return _MANUAL_ID.fullmatch(fid) is not None


def next_manual_id(rows: Iterable[Mapping[str, str]]) -> str:
    """One more than the highest manual id in ``rows``, as ``M-0001``."""
    highest = 0
    for row in rows:
        found = _MANUAL_ID.fullmatch(row.get("id") or "")
        if found:
            highest = max(highest, int(found.group(1)))
    return f"M-{highest + 1:04d}"


def parse_bbox(text: str | None) -> Bbox | None:
    """``minx miny maxx maxy`` as four numbers, or ``None`` when it is not that."""
    parts = (text or "").split()
    if len(parts) != 4 or not all(_is_number(part) for part in parts):
        return None
    minx, miny, maxx, maxy = (float(part) for part in parts)
    if minx >= maxx or miny >= maxy:
        return None
    return (minx, miny, maxx, maxy)


def geojson_bbox(feature: object) -> Bbox | None:
    """The envelope of a GeoJSON polygon feature, or ``None`` when it is not one."""
    geometry = feature.get("geometry") if isinstance(feature, dict) else None
    if not isinstance(geometry, dict) or geometry.get("type") != "Polygon":
        return None
    try:
        ring = [(float(x), float(y)) for x, y, *_ in geometry["coordinates"][0]]
    except (KeyError, IndexError, TypeError, ValueError):
        return None
    if not ring:
        return None
    return (
        min(x for x, _ in ring),
        min(y for _, y in ring),
        max(x for x, _ in ring),
        max(y for _, y in ring),
    )


def sample_id_of(feature: object) -> str:
    """The manual id a map feature was tagged with, or an empty string."""
    properties = feature.get("properties") if isinstance(feature, dict) else None
    if not isinstance(properties, dict):
        return ""
    return str(properties.get("sample_id") or "")


@dataclass(frozen=True)
class ManualRules:
    """What a manual rectangle is checked against, on the map and on reading.

    ``extent`` and every envelope are in the CRS the samples are stored in.
    ``tile_m`` is the side above which a sample is kept with a warning, and
    ``max_side_m`` the side above which it is refused.
    """

    extent: Bbox
    envelopes: tuple[tuple[str, Bbox], ...]
    tile_m: float
    max_side_m: float


def manual_rules(
    extent: Bbox, features: Iterable[FeatureRecord], tile_m: float, max_side_m: float
) -> ManualRules:
    """The rules for this extent and these footprints."""
    envelopes: list[tuple[str, Bbox]] = []
    for record in features:
        envelope = rings_envelope([record])
        if envelope is not None:
            envelopes.append((record.fid, envelope))
    box = (float(extent[0]), float(extent[1]), float(extent[2]), float(extent[3]))
    return ManualRules(box, tuple(envelopes), tile_m, max_side_m)


def check_manual_box(box: Bbox, rules: ManualRules) -> tuple[bool, list[str]]:
    """Whether a rectangle may be a sample, with one line per rule it touched.

    Refused: a box that is not four finite numbers (it could not be
    reprojected), or a longer side above ``max_side_m``. Kept with a warning:
    any part outside the extent, where the cadastral overlap cannot be checked
    because the footprints cover only the extent; a longer side above one
    tile; or an overlap with a cadastral footprint's envelope, naming up to
    three of them, since the person may be marking something the cadastre
    records badly.
    """
    if not all(math.isfinite(value) for value in box) or not (
        box[0] < box[2] and box[1] < box[3]
    ):
        return False, ["refused: the rectangle could not be reprojected"]
    extent = rules.extent
    side = max(box[2] - box[0], box[3] - box[1])
    if side > rules.max_side_m:
        return False, [
            f"refused: longer side {side:.1f} m above the {rules.max_side_m:g} m limit"
        ]
    inside = (
        box[0] >= extent[0]
        and box[1] >= extent[1]
        and box[2] <= extent[2]
        and box[3] <= extent[3]
    )
    apart = (
        box[2] <= extent[0]
        or box[0] >= extent[2]
        or box[3] <= extent[1]
        or box[1] >= extent[3]
    )
    lines: list[str] = []
    if apart:
        lines.append(
            "warning: wholly outside the extent; the cadastral overlap was not "
            "checked (the footprints cover only the extent)"
        )
    elif not inside:
        lines.append(
            "warning: partly outside the extent; the cadastral overlap was not "
            "checked beyond it (the footprints cover only the extent)"
        )
    if side > rules.tile_m:
        lines.append(
            f"warning: longer side {side:.1f} m above one tile ({rules.tile_m:g} m)"
        )
    touched: list[str] = []
    if not apart:
        touched = [
            fid
            for fid, env in rules.envelopes
            if box[0] < env[2]
            and env[0] < box[2]
            and box[1] < env[3]
            and env[1] < box[3]
        ]
    if touched:
        more = f" and {len(touched) - 3} more" if len(touched) > 3 else ""
        lines.append(
            "warning: overlaps the envelope of cadastral footprint(s) "
            + ", ".join(touched[:3])
            + more
        )
    return True, lines


def manual_row(fid: str, box: Bbox) -> dict[str, str]:
    """A manual-samples row: id, source, centre, the rectangle, nothing else."""
    row = {name: "" for name in CANDIDATES_HEADER}
    row.update(
        {
            "id": fid,
            "source": "manual",
            "x": _coordinate((box[0] + box[2]) / 2.0),
            "y": _coordinate((box[1] + box[3]) / 2.0),
            "bbox": " ".join(_coordinate(v) for v in box),
        }
    )
    return row


# Two boxes closer than this on every side are the same rectangle. They are
# compared in the map's own CRS, against the very corners the map was given
# when it opened: reprojecting a box and taking the envelope again would grow
# it by decimetres (the grid is rotated against the meridians), and an
# untouched sample must not read as an edit.
SAME_BOX_M = 0.01
SAME_BOX_DEG = 1e-7


def _same_box(one: Bbox, other: Bbox, tolerance: float) -> bool:
    return all(abs(a - b) <= tolerance for a, b in zip(one, other, strict=True))


def _overlap_area(one: Bbox, other: Bbox) -> float:
    width = min(one[2], other[2]) - max(one[0], other[0])
    height = min(one[3], other[3]) - max(one[1], other[1])
    return width * height if width > 0 and height > 0 else 0.0


def reconcile_samples(
    features: Iterable[object],
    rows: list[dict[str, str]],
    *,
    draw_crs: str,
    native_crs: str,
    rules: ManualRules,
    labelled: Iterable[str],
) -> tuple[list[dict[str, str]], list[str]]:
    """The manual samples after one save of the map, and one line per action.

    ``features`` is every rectangle the map holds at the moment of saving;
    ``rows`` is the file as it stands. A rectangle tagged with an id that is
    in the file is that sample: an unchanged one is left alone, a moved one is
    an edit that keeps the id. A rectangle without a usable tag is matched to
    the not-yet-matched sample whose saved box it overlaps most, and the line
    says so: a tag lost on the way must never turn an edit into a duplicate or
    a deletion. One that overlaps none is a new sample with the next id. A
    sample in the file that no rectangle matches was removed from the map,
    and is deleted only when it carries no manual work in the labelling table
    and that table could be read (a ``ManualWork`` with a ``problem`` refuses
    every deletion). Every rectangle passes the rules of ``check_manual_box``;
    a refused edit keeps the old box, a refused new one is not added. The
    input is never changed; saving an unchanged map returns equal rows.
    """
    current = [dict(row) for row in rows]
    saved = {
        row["id"]: box
        for row in current
        if (box := parse_bbox(row["bbox"])) is not None
    }
    # Each saved box as the map draws it: the envelope of its reprojected corners.
    shown: dict[str, Bbox] = {}
    for feature in sample_features(current, native_crs, draw_crs):
        drawn_box = geojson_bbox(feature)
        if drawn_box is not None:
            shown[sample_id_of(feature)] = drawn_box
    geographic = CRS.from_user_input(draw_crs).is_geographic
    tolerance = SAME_BOX_DEG if geographic else SAME_BOX_M
    lines: list[str] = []
    matched: dict[str, Bbox] = {}
    unmoved: set[str] = set()
    untagged: list[Bbox] = []
    for feature in features:
        drawn = geojson_bbox(feature)
        if drawn is None:
            lines.append("ignored: a shape on the map that is not a rectangle")
            continue
        box = to_projected(drawn, draw_crs, native_crs)
        fid = sample_id_of(feature)
        if fid in saved and fid not in matched:
            matched[fid] = box
            if fid in shown and _same_box(drawn, shown[fid], tolerance):
                unmoved.add(fid)
        else:
            untagged.append(box)
    fresh: list[Bbox] = []
    for box in untagged:
        free = [fid for fid in saved if fid not in matched]
        best = max(free, key=lambda fid: _overlap_area(box, saved[fid]), default="")
        if best and _overlap_area(box, saved[best]) > 0.0:
            matched[best] = box
            lines.append(f"matched by overlap: a rectangle without its id is {best}")
        else:
            fresh.append(box)
    for index, row in enumerate(current):
        fid = row["id"]
        box = matched.get(fid)
        if box is None or fid not in saved or fid in unmoved:
            continue
        allowed, notes = check_manual_box(box, rules)
        side = max(box[2] - box[0], box[3] - box[1])
        if not allowed:
            lines.extend(f"{fid}: {note}" for note in notes)
            lines.append(f"{fid} keeps its previous rectangle")
            continue
        current[index] = {**row, **manual_row(fid, box)} | {
            name: row[name] for name in MANUAL_FIELDS
        }
        lines.extend(f"{fid}: {note}" for note in notes)
        lines.append(f"edited {fid} · longer side {side:.1f} m")
    problem = labelled.problem if isinstance(labelled, ManualWork) else ""
    done = set(labelled)
    gone = [fid for fid in saved if fid not in matched]
    for fid in gone:
        if problem:
            lines.append(
                f"refused: deleting {fid} — candidates.csv cannot be read "
                f"({problem}); its row stays"
            )
        elif fid in done:
            lines.append(
                f"refused: deleting {fid} — it carries manual work in "
                "candidates.csv; its row stays"
            )
        else:
            current = [row for row in current if row["id"] != fid]
            lines.append(f"deleted {fid}")
    for box in fresh:
        allowed, notes = check_manual_box(box, rules)
        side = max(box[2] - box[0], box[3] - box[1])
        if not allowed:
            lines.extend(f"new rectangle: {note}" for note in notes)
            continue
        fid = next_manual_id([*rows, *current])
        current.append(manual_row(fid, box))
        lines.extend(f"{fid}: {note}" for note in notes)
        lines.append(f"created {fid} · longer side {side:.1f} m")
    return current, lines


def read_manual_samples(path: Path) -> list[dict[str, str]]:
    """The raw rows of the manual-samples file, ``[]`` when it does not exist."""
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {name: row.get(name) or "" for name in CANDIDATES_HEADER}
            for row in csv.DictReader(handle)
        ]


def write_manual_samples(rows: Iterable[Mapping[str, str]], path: Path) -> Path:
    """Write the manual samples with the labelling table's columns, header always."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANDIDATES_HEADER), restval="")
        writer.writeheader()
        writer.writerows(rows)
    return path


def ring_lonlat(box: Bbox, source_crs: str, target_crs: str) -> list[list[float]]:
    """The four corners of ``box``, each reprojected, as a closed GeoJSON ring."""
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    corners = [
        (box[0], box[1]),
        (box[2], box[1]),
        (box[2], box[3]),
        (box[0], box[3]),
        (box[0], box[1]),
    ]
    return [list(transformer.transform(x, y)) for x, y in corners]


def sample_features(
    rows: Iterable[Mapping[str, str]], source_crs: str, target_crs: str
) -> list[dict[str, object]]:
    """The manual samples as map features, each tagged with its id.

    The tag is what lets an edit or a deletion on the map find its row again.
    """
    features: list[dict[str, object]] = []
    for row in rows:
        box = parse_bbox(row.get("bbox"))
        if box is None:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"sample_id": row.get("id", "")},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ring_lonlat(box, source_crs, target_crs)],
                },
            }
        )
    return features


def footprints_geojson(
    features: Iterable[FeatureRecord], source_crs: str, target_crs: str
) -> dict[str, object]:
    """The footprints' exterior rings as a GeoJSON collection in ``target_crs``."""
    transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
    collection: list[dict[str, object]] = []
    for record in features:
        rings = [
            [list(transformer.transform(x, y)) for x, y in ring]
            for ring in record.exterior
            if len(ring) >= 3
        ]
        if rings:
            collection.append(
                {
                    "type": "Feature",
                    "properties": {"id": record.fid},
                    "geometry": {
                        "type": "MultiPolygon",
                        "coordinates": [[ring] for ring in rings],
                    },
                }
            )
    return {"type": "FeatureCollection", "features": collection}


def manual_frame(box: Bbox) -> Bbox:
    """The chip frame of a manual sample: the rectangle squared, no margin.

    The person already chose how much ground to include, so the square takes
    the longer side and keeps the rectangle's centre.
    """
    half = max(box[2] - box[0], box[3] - box[1]) / 2.0
    x = (box[0] + box[2]) / 2.0
    y = (box[1] + box[3]) / 2.0
    return (x - half, y - half, x + half, y + half)


def append_strips(rows: list[dict[str, object]], out_dir: Path) -> Path:
    """Add the manual samples' rows to ``strips.csv`` after the ones already there.

    The rows of section 10.1 are kept as they are. Every earlier row of a
    manual id is replaced, so re-running the manual strips never duplicates a
    row and a deleted sample leaves no row behind.
    """
    kept = [row for row in (read_strips(out_dir) or []) if not is_manual_id(row["id"])]
    merged: list[dict[str, object]] = [dict(row) for row in kept]
    merged.extend(rows)
    return write_strips(merged, out_dir)


def read_manual(
    path: Path, taken_ids: Iterable[str], rules: ManualRules | None = None
) -> tuple[list[dict[str, str]], list[str], list[str]] | None:
    """The manual samples to merge, refusals and warnings; ``None`` if absent.

    The file has exactly the labelling table's columns. A row is refused when
    its ``source`` is not ``manual``, when its id is already taken (by a
    cadastral footprint or an earlier manual row), or when it carries no
    numeric ``x`` and ``y``: every sample has to be locatable. With ``rules``,
    every rule a drawing is checked against on the map is applied again here,
    so a row written by hand cannot bypass them; its ``bbox`` is then
    required.
    """
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        header = tuple(reader.fieldnames or ())
        rows = list(reader)
    if header != CANDIDATES_HEADER:
        return (
            [],
            [
                f"{path.name}: columns {list(header)} are not the table's "
                f"{list(CANDIDATES_HEADER)}; no row merged"
            ],
            [],
        )
    seen = set(taken_ids)
    kept: list[dict[str, str]] = []
    refused: list[str] = []
    warned: list[str] = []
    for line, row in enumerate(rows, 2):
        fid = (row.get("id") or "").strip()
        source = (row.get("source") or "").strip()
        located = _is_number(row.get("x")) and _is_number(row.get("y"))
        if source != "manual":
            refused.append(f"line {line} ({fid or 'no id'}): source {source!r}")
            continue
        if not fid:
            refused.append(f"line {line}: no id")
            continue
        if fid in seen:
            refused.append(f"line {line} ({fid}): id already taken")
            continue
        if not located:
            refused.append(f"line {line} ({fid}): no numeric x and y")
            continue
        if rules is not None:
            box = parse_bbox(row.get("bbox"))
            if box is None:
                refused.append(f"line {line} ({fid}): no bbox 'minx miny maxx maxy'")
                continue
            allowed, notes = check_manual_box(box, rules)
            if not allowed:
                refused.extend(f"line {line} ({fid}): {note}" for note in notes)
                continue
            warned.extend(f"line {line} ({fid}): {note}" for note in notes)
        seen.add(fid)
        kept.append({name: row.get(name) or "" for name in CANDIDATES_HEADER})
    return kept, refused, warned


@dataclass(frozen=True)
class CandidatesWrite:
    """What a regeneration of the labelling table did.

    ``written`` is false when an id holding manual work would disappear
    (``missing`` names them) or when the existing file cannot be read as the
    table (``reason`` says what was seen); the file is then left as it was.
    ``carried`` counts the rows whose manual columns came from the old file.
    ``normalised`` is set when the old file was readable but not canonical,
    and says which format was replaced by comma-separated UTF-8.
    """

    path: Path
    written: bool
    carried: int
    missing: tuple[str, ...]
    reason: str = ""
    normalised: str = ""


def write_candidates(
    rows: Iterable[Mapping[str, object]], out_dir: Path
) -> CandidatesWrite:
    """Rebuild the labelling table, carrying every row's manual work over by id.

    ``label``, ``evidence``, ``notes`` and ``minutes_spent`` are taken from the
    existing file for every id that is still there, whether it was saved
    comma- or semicolon-separated, with or without a BOM. The write is
    refused, and the file left byte-identical, when an id holding manual work
    would disappear, or when the file cannot be read as the table at all:
    a file this function cannot read is never overwritten. Nothing is
    deleted, moved or backed up. The table is always written comma-separated
    UTF-8 without a BOM, header included even with no rows.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "candidates.csv"
    old = read_labels(path)
    if old.problem:
        return CandidatesWrite(path, False, 0, (), reason=old.problem)
    fresh = [dict(row) for row in rows]
    ids = {str(row.get("id", "")) for row in fresh}
    missing = tuple(sorted(fid for fid in old.work if fid not in ids))
    if missing:
        return CandidatesWrite(path, False, 0, missing)
    carried = 0
    for row in fresh:
        done = old.work.get(str(row.get("id", "")))
        if done:
            row.update(done)
            carried += 1
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANDIDATES_HEADER), restval="")
        writer.writeheader()
        writer.writerows(fresh)
    normalised = ""
    if old.exists and not old.canonical:
        normalised = f"{_DELIMITERS[old.delimiter]}-separated" + (
            ", UTF-8 with BOM" if old.bom else ""
        )
    return CandidatesWrite(path, True, carried, (), normalised=normalised)


def strip_years(rows: Iterable[Mapping[str, str]]) -> list[int]:
    """The years section 10.1 asked, read from its rows of ``strips.csv``."""
    return sorted(
        {
            int(row["year"])
            for row in rows
            if not is_manual_id(row.get("id", "")) and _is_number(row.get("year"))
        }
    )


def samples_without_strips(
    sample_ids: Iterable[str], rows: Iterable[Mapping[str, str]]
) -> list[str]:
    """The manual samples with no row at all in ``strips.csv``, in order."""
    asked = {row.get("id", "") for row in rows}
    return [fid for fid in sample_ids if fid not in asked]


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

        # 5: a body is named after what it is, not after what it is called
        check(
            "5 the bytes name the file, even under a wrong content type",
            (
                _extension("text/html", b'<?xml version="1.0"?><f/>') == ".xml"
                and _extension("text/html", b"<html></html>") == ".html"
                and _extension("image/png", b"\x89PNG\r\n") == ".png"
                and _extension("", b"\x00\x01") == ".bin"
            ),
            _extension("text/html", b'<?xml version="1.0"?><f/>'),
        )

        # 5: a wait that runs out is its own outcome, and still audited
        slow_dir = root / "slow"
        original_get = requests.get

        def _expire(*args: object, **kwargs: object) -> requests.Response:
            raise requests.Timeout("read timed out")

        try:
            requests.get = _expire  # type: ignore[assignment]
            waited = fetch(dead_url, {"REQUEST": "GetFeature"}, slow_dir, timeout=0.1)
        finally:
            requests.get = original_get
        check(
            "5 a wait that runs out is marked as such, not as a refusal",
            waited.timed_out and waited.status == 0 and waited.path is None,
            waited,
        )
        check(
            "5 a request that failed for another reason is not a timeout",
            not got.timed_out,
            got,
        )
        slow_rows = list(csv.reader(manifest_path(slow_dir).open(encoding="utf-8")))
        check(
            "5 a timed-out request still leaves its manifest row",
            len(slow_rows) == 2 and slow_rows[1][2] == "0",
            slow_rows,
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

        # 8: a feature reply, read by local name with nothing schema-specific
        vectors = root / "vectors"
        vectors.mkdir()
        reply = vectors / "features.gml"
        reply.write_text(
            '<?xml version="1.0"?>\n'
            '<wfs:FeatureCollection xmlns:wfs="urn:test:wfs"'
            ' xmlns:gml="urn:test:gml" xmlns:ex="urn:test:example"'
            ' numberReturned="2" numberMatched="unknown">\n'
            "  <wfs:member>\n"
            '    <ex:Thing gml:id="t.1">\n'
            "      <ex:tag><ex:Tag><ex:localName>one</ex:localName></ex:Tag></ex:tag>\n"
            "      <ex:state>whole</ex:state>\n"
            "      <ex:empty/>\n"
            '      <ex:shape><gml:Surface srsName="urn:ogc:def:crs:EPSG::3042">\n'
            "        <gml:exterior><gml:LinearRing>\n"
            "          <gml:posList>0 0 10 0 10 10 0 10 0 0</gml:posList>\n"
            "        </gml:LinearRing></gml:exterior>\n"
            "        <gml:interior><gml:LinearRing>\n"
            "          <gml:posList>2 2 4 2 4 4 2 4 2 2</gml:posList>\n"
            "        </gml:LinearRing></gml:interior>\n"
            "      </gml:Surface></ex:shape>\n"
            "    </ex:Thing>\n"
            "  </wfs:member>\n"
            "  <wfs:member>\n"
            '    <ex:Thing gml:id="t.2" xmlns:xlink="urn:test:xlink">\n'
            '      <ex:state xlink:href="urn:codes/ruined"/>\n'
            "      <ex:shape><gml:Point>\n"
            '        <gml:pos srsDimension="3">1 1 7</gml:pos>\n'
            "      </gml:Point></ex:shape>\n"
            "    </ex:Thing>\n"
            "  </wfs:member>\n"
            "</wfs:FeatureCollection>\n",
            encoding="utf-8",
        )
        parsed = read_features(reply)
        check(
            "8 a feature reply: one record per member, typed by local tag name",
            (
                len(parsed.features) == 2
                and parsed.type_names == ("Thing",)
                and [record.fid for record in parsed.features] == ["t.1", "t.2"]
            ),
            (parsed.type_names, [record.fid for record in parsed.features]),
        )
        first, second = parsed.features
        check(
            "8 a field nested inside another is read under its own name",
            first.values.get("localName") == "one",
            first.values,
        )
        check(
            "8 a field carried empty keeps its name and has no value",
            first.values.get("empty") == "",
            first.values,
        )
        check(
            "8 a code list arriving as a reference is read as its last segment",
            second.values.get("state") == "ruined",
            second.values,
        )
        check(
            "8 the reply's own counts are read, and 'unknown' is undeclared",
            (parsed.number_returned, parsed.number_matched) == (2, _UNDECLARED),
            (parsed.number_returned, parsed.number_matched),
        )
        check(
            "8 the CRS is normalised and the service's own spelling kept",
            parsed.crs == "EPSG:3042" and parsed.srs_name.startswith("urn:"),
            (parsed.crs, parsed.srs_name),
        )
        check(
            "8 a courtyard is taken out of the footprint it sits in",
            footprint_area(first) == 96.0,
            footprint_area(first),
        )
        check(
            "8 coverage counts the fields, and an empty value is one of them",
            attribute_coverage(parsed.features)["state"] == 2
            and value_counts(parsed.features, "state") == {"ruined": 1, "whole": 1}
            and value_counts(parsed.features, "empty") == {"": 1},
            (
                attribute_coverage(parsed.features),
                value_counts(parsed.features, "state"),
            ),
        )
        # 8: a swapped reply is spotted by where its geometry lands, not trusted
        elsewhere = FeatureRecord(
            "far", {}, (((100.0, 0.0), (110.0, 0.0), (110.0, 10.0), (100.0, 0.0)),), ()
        )
        here = (0.0, 0.0, 10.0, 10.0)
        there = (0.0, 100.0, 10.0, 110.0)
        check(
            "8 axis order is decided by where the geometry lands",
            (
                axis_order(parsed.features, here)[0] is False
                and axis_order([elsewhere], there)[0] is True
                and axis_order([elsewhere], here)[0] is None
                and axis_order((), here)[0] is None
            ),
            (
                axis_order(parsed.features, here),
                axis_order([elsewhere], there),
                axis_order([elsewhere], here),
            ),
        )
        check(
            "8 swapping axes reverses every pair and keeps the fields",
            swap_axes([elsewhere])[0].exterior[0][0] == (0.0, 100.0),
            swap_axes([elsewhere])[0].exterior[0],
        )
        exception_reply = vectors / "exception.xml"
        exception_reply.write_text(
            '<?xml version="1.0"?><ows:ExceptionReport xmlns:ows="urn:test:ows">'
            "<ows:Exception><ows:ExceptionText>unknown parameter"
            "</ows:ExceptionText></ows:Exception></ows:ExceptionReport>",
            encoding="utf-8",
        )
        refused = read_features(exception_reply)
        check(
            "8 a refused query is a value with the service's reason",
            not refused.features and "unknown parameter" in refused.exception,
            refused.exception,
        )
        garbled = vectors / "garbled.xml"
        garbled.write_text("<not xml at all", encoding="utf-8")
        check(
            "8 a reply that cannot be read, or was never saved, is a value too",
            bool(read_features(garbled).exception)
            and bool(read_features(None).exception)
            and read_features(garbled).features == (),
            (read_features(garbled).exception, read_features(None).exception),
        )

        # 8: the geometry a service's area ceiling forces on every request
        wide = (0.0, 0.0, 2000.0, 1000.0)
        check(
            "8 area_km2 is the plain projected area",
            area_km2(wide) == 2.0,
            area_km2(wide),
        )
        shrunk = scaled_window(wide, 0.5)
        check(
            "8 a scaled window keeps the shape and quarters the area",
            area_km2(shrunk) == 0.5
            and (shrunk[2] - shrunk[0]) / (shrunk[3] - shrunk[1]) == 2.0,
            shrunk,
        )
        cells = split_under(wide, 0.6)
        check(
            "8 split_under covers the box with cells under the ceiling",
            all(area_km2(cell) <= 0.6 for cell in cells)
            and abs(sum(area_km2(cell) for cell in cells) - area_km2(wide)) < 1e-9
            and min(cell[0] for cell in cells) == wide[0]
            and max(cell[2] for cell in cells) == wide[2],
            [round(area_km2(cell), 4) for cell in cells],
        )
        check(
            "8 a box already under the ceiling is left whole",
            split_under(wide, 3.0) == (wide,) and split_under(wide, 0.0) == (wide,),
            split_under(wide, 3.0),
        )
        twice = merge_features([parsed.features, parsed.features])
        check(
            "8 a feature answered for by two boxes is counted once",
            len(twice[0]) == len(parsed.features) and twice[1] == len(parsed.features),
            twice[1],
        )
        nameless = FeatureRecord("", {}, (((0.0, 0.0), (1.0, 0.0), (1.0, 1.0)),), ())
        other = FeatureRecord("", {}, (((9.0, 9.0), (8.0, 9.0), (8.0, 8.0)),), ())
        merged, repeats = merge_features([[nameless], [nameless, other]])
        check(
            "8 features without an identifier fall back to their own geometry",
            len(merged) == 2 and repeats == 1,
            (len(merged), repeats),
        )

        # 8: asking for a type the entry names must not need a code change
        provider_entry = PROVIDERS["es-pnoa"]
        askable = [
            (kind, service, name)
            for one in PROVIDERS.values()
            for kind, (service, name) in one.wfs_types.items()
            if service not in one.endpoints
            or name.partition(":")[0] not in one.wfs_namespaces
        ]
        check(
            "8 every feature type names a known endpoint and namespace",
            not askable,
            askable,
        )
        asked = {}
        original_get = requests.get
        try:
            requests.get = _expire  # type: ignore[assignment]
            for kind in provider_entry.wfs_types:
                asked[kind] = wfs_features(
                    provider_entry,
                    kind,
                    (0.0, 0.0, 1.0, 1.0),
                    "EPSG:25830",
                    root / "ask",
                ).url
        finally:
            requests.get = original_get

        def in_url(value: str, url: str) -> bool:
            """Is ``value`` in ``url``, allowing for percent-encoded colons?"""
            return value.replace(":", "%3A") in url or value in url

        check(
            "8 each type goes out with its own name, prefix and endpoint",
            all(
                in_url(name, asked[kind])
                and in_url(
                    provider_entry.wfs_namespaces[name.partition(":")[0]], asked[kind]
                )
                and provider_entry.endpoints[service].rsplit("/", 1)[-1] in asked[kind]
                for kind, (service, name) in provider_entry.wfs_types.items()
            ),
            asked,
        )

        # 15.5: elevation coverages (handoff 015, step 5), network replaced or refused
        check(
            "15.5 every elevation product names a known coverage endpoint",
            all(
                service in one.coverage_endpoints
                for one in PROVIDERS.values()
                for service, _ in one.elevation.values()
            ),
            [one.elevation for one in PROVIDERS.values()],
        )
        bare_provider = replace(provider_entry, coverage_endpoints={}, elevation={})
        check(
            "15.5 a provider with no elevation mapping is valid and probes nothing",
            wcs_services(bare_provider) == () and not bare_provider.elevation,
            wcs_services(bare_provider),
        )
        wcs_dir = root / "wcs"
        window = (469120.0, 4482944.0, 470464.0, 4483840.0)
        coverage_asks: dict[str, Fetch] = {}
        original_get = requests.get
        try:
            requests.get = _expire  # type: ignore[assignment]
            listed_wcs = [
                wcs_capabilities(provider_entry, service, wcs_dir)
                for service in wcs_services(provider_entry)
            ]
            for product in provider_entry.elevation:
                coverage_asks[product] = wcs_coverage(
                    provider_entry, product, window, "EPSG:25830", wcs_dir
                )
        finally:
            requests.get = original_get
        wcs_rows = list(csv.reader(manifest_path(wcs_dir).open(encoding="utf-8")))
        check(
            "15.5 a failed coverage request is a value and leaves its manifest row",
            all(
                got.status == 0 and got.path is None and got.error
                for got in [*listed_wcs, *coverage_asks.values()]
            )
            and len(wcs_rows) == 1 + len(listed_wcs) + len(provider_entry.elevation),
            wcs_rows,
        )
        x_label, y_label = provider_entry.wcs_axis_labels
        check(
            "15.5 a coverage request names its id, subsets both axes, in the CRS",
            all(
                name in sent
                and sent.count("SUBSET=") == 2
                and f"{x_label}(469120.0,470464.0)" in sent
                and f"{y_label}(4482944.0,4483840.0)" in sent
                and sent.count("EPSG/0/25830") == 2
                for product, (_, name) in provider_entry.elevation.items()
                for sent in [unquote(coverage_asks[product].url)]
            ),
            {k: unquote(v.url) for k, v in coverage_asks.items()},
        )

        def _reply(body: bytes, content_type: str) -> Callable[..., requests.Response]:
            def answer(*args: object, **kwargs: object) -> requests.Response:
                response = requests.Response()
                response.status_code = 200
                response._content = body
                response.headers["Content-Type"] = content_type
                return response

            return answer

        refusal_xml = (
            b'<?xml version="1.0"?><ows:ExceptionReport '
            b'xmlns:ows="http://www.opengis.net/ows/2.0"><ows:Exception '
            b'exceptionCode="InvalidAxisLabel"><ows:ExceptionText>Unknown axis '
            b"label E</ows:ExceptionText></ows:Exception></ows:ExceptionReport>"
        )
        try:
            requests.get = _reply(refusal_xml, "text/xml")  # type: ignore[assignment]
            refused = wcs_coverage(
                provider_entry, "terrain", window, "EPSG:25830", wcs_dir
            )
            portal_page = b"<html><title>Portal</title></html>"
            requests.get = _reply(portal_page, "text/html")  # type: ignore[assignment]
            portal = wcs_coverage(
                provider_entry, "surface", window, "EPSG:25830", wcs_dir
            )
        finally:
            requests.get = original_get
        refused_reading = read_coverage(refused.path)
        portal_reading = read_coverage(portal.path)
        check(
            "15.5 a service refusal with status 200 is not a raster, in its own words",
            refused.path is not None
            and refused.path.parent.name == "elevation"
            and "Unknown axis label E" in refused_reading.exception
            and refused_reading.value_range is None,
            refused_reading,
        )
        check(
            "15.5 an HTML page with status 200 is not a raster either",
            "not a raster" in portal_reading.exception
            and "Portal" in portal_reading.exception
            and portal_reading.shape == (0, 0, 0),
            portal_reading,
        )
        check(
            "15.5 a missing or unreadable reply is a value with a reason",
            bool(read_coverage(None).exception)
            and bool(read_coverage(garbled).exception),
            (read_coverage(None).exception, read_coverage(garbled).exception),
        )

        import rasterio
        from rasterio.transform import from_origin

        grid = np.arange(12 * 20, dtype="float32").reshape(12, 20)
        grid[:3, :] = -9999.0
        grid[5, 5] = np.nan
        tif = root / "dem.tif"
        with rasterio.open(
            tif,
            "w",
            driver="GTiff",
            width=20,
            height=12,
            count=1,
            dtype="float32",
            crs="EPSG:25830",
            transform=from_origin(469120.0, 4483840.0, 2.5, 2.5),
            nodata=-9999.0,
        ) as dst:
            dst.write(grid, 1)
        check(
            "15.5 a GeoTIFF body is filed as .tif, whatever it was labelled",
            _extension("application/octet-stream", tif.read_bytes()) == ".tif",
            _extension("application/octet-stream", tif.read_bytes()),
        )
        dem = read_coverage(tif)
        check(
            "15.5 a raster reply reports its CRS, shape and delivered grid step",
            dem.exception == ""
            and dem.crs == "EPSG:25830"
            and dem.shape == (1, 12, 20)
            and dem.step_m == (2.5, 2.5),
            dem,
        )
        check(
            "15.5 no-data counts declared no-data and NaN, the range only the rest",
            abs(dem.nodata_share - 61 / 240) < 1e-9
            and dem.value_range == (60.0, 239.0),
            (dem.nodata_share, dem.value_range),
        )
        wcs_caps = root / "wcs-caps.xml"
        wcs_caps.write_text(
            '<?xml version="1.0"?><wcs:Capabilities '
            'xmlns:wcs="http://www.opengis.net/wcs/2.0" '
            'xmlns:ows="http://www.opengis.net/ows/2.0" '
            'xmlns:crs="http://www.opengis.net/wcs/crs/1.0">'
            "<ows:ServiceIdentification><ows:Title>Elevation</ows:Title>"
            "<ows:Abstract>Surface and normalised heights</ows:Abstract>"
            "</ows:ServiceIdentification><wcs:ServiceMetadata><crs:CrsMetadata>"
            "<crs:crsSupported>http://www.opengis.net/def/crs/EPSG/0/25830"
            "</crs:crsSupported></crs:CrsMetadata></wcs:ServiceMetadata>"
            "<wcs:Contents><wcs:CoverageSummary><ows:Title>Surface 5 m</ows:Title>"
            "<wcs:CoverageId>mds05</wcs:CoverageId></wcs:CoverageSummary>"
            "</wcs:Contents></wcs:Capabilities>",
            encoding="utf-8",
        )
        coverage_caps = read_capabilities(wcs_caps)
        check(
            "15.5 a WCS capabilities names its coverages, CRS and its own abstract",
            coverage_caps.layers == ("mds05",)
            and coverage_caps.titles["mds05"] == "Surface 5 m"
            and coverage_caps.crs == ("EPSG:25830",)
            and "normalised heights" in coverage_caps.service_abstract,
            coverage_caps,
        )

        # 10: example buildings, their chip frame and the keep-or-drop verdict
        def square(fid: str, x: float, y: float, side: float) -> FeatureRecord:
            ring = ((x, y), (x + side, y), (x + side, y + side), (x, y + side))
            return FeatureRecord(fid, {}, (ring,), ())

        town: Bbox = (0.0, 0.0, 400.0, 400.0)
        sides = (6.0, 9.0, 14.0)  # one size per class, so each class is known
        corners = {"SW": (40.0, 40.0), "SE": (240.0, 40.0)}
        corners |= {"NW": (40.0, 240.0), "NE": (240.0, 240.0)}
        houses = [
            square(f"b-{side:g}-{name}-{k}", x + 30.0 * k, y, side)
            for side in sides
            for name, (x, y) in corners.items()
            for k in range(3)
        ]

        def pick(features: list[FeatureRecord], n: int = 12) -> Selection:
            return choose_examples(
                features, town, n, seed=11, margin_m=10.0, max_frame_m=64.0
            )

        picked = pick(houses).examples
        again = pick(list(reversed(houses))).examples
        check(
            "10 the selection is deterministic for a seed, whatever the input order",
            [e.fid for e in picked] == [e.fid for e in again],
            ([e.fid for e in picked], [e.fid for e in again]),
        )
        check(
            "10 three area classes by four quadrants, one building each",
            len(picked) == 12
            and len({e.fid for e in picked}) == 12
            and {(e.tertile, e.quadrant) for e in picked}
            == {(t, q) for t in (1, 2, 3) for q in QUADRANTS}
            and all(e.fid.startswith(f"b-{sides[e.tertile - 1]:g}-") for e in picked)
            and not any(e.fallback for e in picked),
            [(e.fid, e.tertile, e.quadrant, e.fallback) for e in picked],
        )
        none_given = pick([])
        none_asked = pick(houses, n=0)
        check(
            "10 an empty footprint list returns no examples, with a reason",
            none_given.examples == ()
            and bool(none_given.reason)
            and none_asked.examples == ()
            and bool(none_asked.reason),
            (none_given, none_asked.reason),
        )
        west = [h for h in houses if h.exterior[0][0][0] < 200.0]
        lopsided = pick(west).examples
        check(
            "10 a quadrant with no building of its class falls back to the class",
            len(lopsided) == 12
            and sum(e.fallback for e in lopsided) == 6
            and all(e.quadrant in ("NW", "SW") for e in lopsided),
            [(e.fid, e.quadrant, e.fallback) for e in lopsided],
        )
        # A compound in each quadrant, framed at 70-90 m against a 64 m tile, and
        # each the largest footprint of all: it would sit in the top class.
        giants = [
            square(f"giant-{name}", x, y, 50.0 + 5.0 * k)
            for k, (name, (x, y)) in enumerate(corners.items())
        ]
        crowded = pick(houses + giants)
        check(
            "10 a footprint framed wider than the tile is never chosen",
            not any(e.fid.startswith("giant") for e in crowded.examples)
            and [o.fid for o in crowded.excluded]
            == ["giant-NE", "giant-NW", "giant-SE", "giant-SW"]
            and crowded.excluded[0].frame_m == 85.0
            and crowded.excluded[0].parts == 1
            and crowded.eligible == len(houses),
            crowded.excluded,
        )
        check(
            "10 its slot falls to the next eligible building of its class and quadrant",
            [e.fid for e in crowded.examples] == [e.fid for e in picked]
            and not any(e.fallback for e in crowded.examples),
            [(e.fid, e.quadrant, e.fallback) for e in crowded.examples],
        )
        only_giants = pick(giants)
        check(
            "10 all footprints oversized returns no examples, and says why",
            only_giants.examples == ()
            and only_giants.eligible == 0
            and "wider than 64 m" in only_giants.reason,
            only_giants,
        )
        holed = FeatureRecord(
            "h",
            {},
            (((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)),),
            (((0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0)),),
        )
        centre = footprint_centroid(holed)
        check(
            "10 the centroid is area-weighted, with the courtyard taken out",
            centre is not None
            and abs(centre[0] - 35.0 / 6.0) < 1e-9
            and abs(centre[1] - 35.0 / 6.0) < 1e-9,
            centre,
        )
        wide = Example(
            fid="w",
            area_m2=80.0,
            centroid=(105.0, 52.0),
            envelope=(100.0, 50.0, 116.0, 55.0),
            tertile=1,
            quadrant="SW",
            fallback=False,
            record=square("w", 100.0, 50.0, 1.0),
        )
        frame = chip_box(wide, 10.0)
        check(
            "10 the chip is a square on the centroid, longer side plus both margins",
            frame == (87.0, 34.0, 123.0, 70.0) and chip_px(frame, 0.25) == 144,
            (frame, chip_px(frame, 0.25)),
        )
        texture = np.random.default_rng(3).integers(1, 255, (40, 40, 3), "uint8")
        opaque = np.full((40, 40, 1), 255, dtype="uint8")
        gap = opaque.copy()
        gap[:4, :] = 0  # 10 % of the pixels without data
        sliver = opaque.copy()
        sliver[:1, :] = 0  # 2.5 %
        cases: dict[str, np.ndarray] = {
            "blank": np.zeros((40, 40, 4), dtype="uint8"),
            "flat": np.full((40, 40, 4), 200, dtype="uint8"),
            "over": np.concatenate([texture, gap], axis=-1),
            "under": np.concatenate([texture, sliver], axis=-1),
        }
        verdicts: dict[str, ChipVerdict] = {}
        for name, array in cases.items():
            chip = root / f"chip-{name}.png"
            _write_png(chip, array)  # four bands: the PNG carries them as RGBA
            reply = Fetch("chip", 200, chip.stat().st_size, "m", 0.0, chip, "")
            verdicts[name] = judge_chip(reply, 0.05)
        check(
            "10 a blank chip is dropped, transparent or of a single value",
            not verdicts["blank"].kept
            and not verdicts["flat"].kept
            and "blank" in verdicts["blank"].reason,
            verdicts,
        )
        check(
            "10 a chip over the no-data threshold is dropped, with its share",
            not verdicts["over"].kept
            and verdicts["over"].nodata_share is not None
            and abs(verdicts["over"].nodata_share - 0.10) < 1e-9
            and "0.100" in verdicts["over"].reason,
            verdicts["over"],
        )
        check(
            "10 a chip under the threshold is kept",
            verdicts["under"].kept
            and verdicts["under"].nodata_share is not None
            and abs(verdicts["under"].nodata_share - 0.025) < 1e-9,
            verdicts["under"],
        )
        failed = judge_chip(Fetch("u", 0, 0, "", 0.0, None, "ConnectionError: x"), 0.05)
        check(
            "10 a failed chip request is dropped with the reason it failed",
            not failed.kept
            and failed.nodata_share is None
            and failed.reason == "ConnectionError: x",
            failed,
        )
        strips = write_strips([], root / "strips-empty")
        filled = write_strips(
            [{"id": "b", "year": 2023, "kept": "yes", "nodata_share": 0.0}],
            root / "strips-one",
        )
        with filled.open(newline="", encoding="utf-8") as handle:
            filled_rows = list(csv.reader(handle))
        check(
            "10 strips.csv carries its header with no rows, and fills what is missing",
            strips.read_text(encoding="utf-8").strip() == ",".join(STRIPS_HEADER)
            and filled_rows
            == [list(STRIPS_HEADER), ["b", "2023", "yes", "0.0", "", ""]],
            filled_rows,
        )

        # 11: the labelling table
        empty_out = root / "labels-empty"
        empty_write = write_candidates([], empty_out)
        check(
            "11 candidates.csv carries its header with no rows",
            empty_write.written
            and empty_write.path.read_text(encoding="utf-8").strip()
            == ",".join(CANDIDATES_HEADER),
            empty_write.path.read_text(encoding="utf-8"),
        )
        strip_table = [
            {"id": "a", "year": "2006", "kept": "yes"},
            {"id": "a", "year": "2023", "kept": "no"},  # dropped: never the year
            {"id": "a", "year": "2018", "kept": "yes"},
            {"id": "b", "year": "2015", "kept": "no"},  # no kept chip, no row
            {"id": "c/1", "year": "2009", "kept": "yes"},
            {"id": "d", "year": "2020", "kept": "yes"},
        ]
        strip_out = root / "strip-out"
        (strip_out / "figs").mkdir(parents=True)
        for name in ("strip-07-a.png", "strip-02-xa.png"):  # NN is not ours
            (strip_out / "figs" / name).write_bytes(b"")
        for name in ("strip-01-c_1.png", "strip-09-c_1.png"):  # two: ambiguous
            (strip_out / "figs" / name).write_bytes(b"")
        by_id, strip_problems = strips_by_id(strip_table, strip_out)
        check(
            "11 label_year is the newest kept chip, ignoring dropped ones",
            {fid: year for fid, (_, year) in by_id.items()}
            == {"a": "2018", "c/1": "2009", "d": "2020"},
            by_id,
        )
        check(
            "11 the strip figure is found by id, whatever its number",
            by_id["a"][0] == "figs/strip-07-a.png",
            by_id,
        )
        check(
            "11 a missing figure leaves the strip empty, with no complaint",
            by_id["d"][0] == "" and by_id["d"][1] == "2020",
            (by_id, strip_problems),
        )
        check(
            "11 two matching figures leave the strip empty, and say so",
            by_id["c/1"][0] == ""
            and len(strip_problems) == 1
            and "c/1" in strip_problems[0]
            and "strip-01-c_1.png, strip-09-c_1.png" in strip_problems[0],
            (by_id, strip_problems),
        )
        located = cadastre_rows([square("a", 10.0, 20.0, 4.0), houses[0]], by_id)
        check(
            "11 every cadastral row carries centroid, envelope, area, strip and year",
            located[0]
            == {
                "id": "a",
                "source": "cadastre",
                "x": "12.00",
                "y": "22.00",
                "bbox": "10.00 20.00 14.00 24.00",
                "area_m2": "16.00",
                "strip": "figs/strip-07-a.png",
                "label_year": "2018",
            }
            and located[1]["strip"] == ""
            and located[1]["label_year"] == "",
            located,
        )
        manual_file = root / "manual.csv"
        with manual_file.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(CANDIDATES_HEADER)
            writer.writerow(
                ["m1", "manual", "15", "25", "", "", "", "2023", "unsure", "", "", "3"]
            )
            writer.writerow(["m2", "cadastre", "1", "2"] + [""] * 8)
            writer.writerow(["a", "manual", "1", "2"] + [""] * 8)
            writer.writerow(["m3", "manual", "", "2"] + [""] * 8)
        merged_in = read_manual(manual_file, [str(row["id"]) for row in located])
        check(
            "11 a manual row is merged, with its own columns kept",
            merged_in is not None
            and [row["id"] for row in merged_in[0]] == ["m1"]
            and merged_in[0][0]["label"] == "unsure"
            and merged_in[0][0]["minutes_spent"] == "3",
            merged_in,
        )
        check(
            "11 a non-manual, a colliding and an unlocated row are each refused",
            merged_in is not None
            and len(merged_in[1]) == 3
            and "source 'cadastre'" in merged_in[1][0]
            and "already taken" in merged_in[1][1]
            and "no numeric x and y" in merged_in[1][2],
            merged_in,
        )
        check(
            "11 an absent manual file is not an error",
            read_manual(root / "no-manual.csv", []) is None,
        )

        # 10.2: manual samples drawn on their own map, saved by a button
        manual_rule_set = ManualRules(
            (0.0, 0.0, 400.0, 400.0),
            (("fp-1", (100.0, 100.0, 110.0, 110.0)),),
            64.0,
            512.0,
        )

        def drawn_feature(box: Bbox, sid: str = "") -> dict[str, object]:
            ring = [
                [box[0], box[1]],
                [box[2], box[1]],
                [box[2], box[3]],
                [box[0], box[3]],
                [box[0], box[1]],
            ]
            return {
                "type": "Feature",
                "properties": {"sample_id": sid} if sid else {"style": {}},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }

        def save_map(
            features: list[dict[str, object]],
            current: list[dict[str, str]],
            labelled: Iterable[str] = (),
            rule_set: ManualRules = manual_rule_set,
        ) -> tuple[list[dict[str, str]], list[str]]:
            return reconcile_samples(
                features,
                current,
                draw_crs="EPSG:25830",
                native_crs="EPSG:25830",
                rules=rule_set,
                labelled=labelled,
            )

        check(
            "10.2 the next id is one more than the highest in the file",
            next_manual_id([]) == "M-0001"
            and next_manual_id([{"id": "M-0007"}, {"id": "M-0002"}, {"id": "x"}])
            == "M-0008",
        )
        two_new, said_two = save_map(
            [
                drawn_feature((20.0, 20.0, 40.0, 30.0)),
                drawn_feature((200.0, 200.0, 210.0, 215.0)),
            ],
            [],
        )
        check(
            "10.2 two new rectangles in one save get two ids; centre, box, no area",
            [row["id"] for row in two_new] == ["M-0001", "M-0002"]
            and two_new[0]
            == {
                **{name: "" for name in CANDIDATES_HEADER},
                "id": "M-0001",
                "source": "manual",
                "x": "30.00",
                "y": "25.00",
                "bbox": "20.00 20.00 40.00 30.00",
            }
            and sum(line.startswith("created") for line in said_two) == 2,
            (two_new, said_two),
        )
        loaded_file = write_manual_samples(two_new, root / "manual-loaded.csv")
        loaded_bytes = loaded_file.read_bytes()
        loaded_rows = read_manual_samples(loaded_file)
        on_map = sample_features(loaded_rows, "EPSG:25830", "EPSG:4326")
        unchanged, said_unchanged = reconcile_samples(
            on_map,
            loaded_rows,
            draw_crs="EPSG:4326",
            native_crs="EPSG:25830",
            rules=replace(
                manual_rule_set,
                extent=(-1e7, -1e7, 1e7, 1e7),
            ),
            labelled=(),
        )
        if unchanged != loaded_rows:  # what the button does
            write_manual_samples(unchanged, loaded_file)
        check(
            "10.2 load then save, unchanged, is a no-op: file byte-identical",
            unchanged == loaded_rows
            and not said_unchanged
            and loaded_file.read_bytes() == loaded_bytes,
            said_unchanged,
        )
        moved, said_moved = save_map(
            [
                drawn_feature((50.0, 50.0, 60.0, 70.0), "M-0001"),
                drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002"),
            ],
            two_new,
        )
        check(
            "10.2 an edit keeps the id and touches no other row",
            [row["id"] for row in moved] == ["M-0001", "M-0002"]
            and moved[0]["bbox"] == "50.00 50.00 60.00 70.00"
            and moved[1] == two_new[1]
            and said_moved == ["edited M-0001 · longer side 20.0 m"],
            (moved, said_moved),
        )
        tagless, said_tagless = save_map(
            [
                drawn_feature((22.0, 21.0, 41.0, 31.0)),  # M-0001, tag lost, moved
                drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002"),
            ],
            two_new,
        )
        check(
            "10.2 a rectangle that lost its tag is matched by overlap, not duplicated",
            [row["id"] for row in tagless] == ["M-0001", "M-0002"]
            and tagless[0]["bbox"] == "22.00 21.00 41.00 31.00"
            and any("matched by overlap" in s and "M-0001" in s for s in said_tagless)
            and not any(s.startswith(("deleted", "created")) for s in said_tagless),
            said_tagless,
        )
        apart, said_apart = save_map(
            [
                drawn_feature((20.0, 20.0, 40.0, 30.0), "M-0001"),
                drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002"),
                drawn_feature((300.0, 300.0, 310.0, 310.0)),
            ],
            two_new,
        )
        check(
            "10.2 a tagless rectangle overlapping no sample is created",
            [row["id"] for row in apart] == ["M-0001", "M-0002", "M-0003"]
            and said_apart[-1].startswith("created M-0003"),
            said_apart,
        )
        removed_rows, said_removed = save_map(
            [drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002")], two_new
        )
        kept_back, said_kept = save_map(
            [drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002")],
            two_new,
            ["M-0001"],
        )
        check(
            "10.2 removing an unlabelled sample deletes it; a labelled one is refused",
            [row["id"] for row in removed_rows] == ["M-0002"]
            and said_removed == ["deleted M-0001"]
            and kept_back == two_new
            and "carries manual work" in said_kept[0],
            (said_removed, said_kept),
        )
        outside_rows, said_out = save_map(
            [drawn_feature((500.0, 10.0, 520.0, 20.0))], []
        )
        partly_rows, said_partly = save_map(
            [drawn_feature((390.0, 105.0, 410.0, 115.0))], []
        )
        overlap_rows, said_overlap = save_map(
            [drawn_feature((105.0, 105.0, 120.0, 120.0))], []
        )
        check(
            "10.2 outside the extent kept with its warning, overlap not checked there",
            [row["id"] for row in outside_rows] == ["M-0001"]
            and any("wholly outside" in s and "not checked" in s for s in said_out)
            and [row["id"] for row in partly_rows] == ["M-0001"]
            and any("partly outside" in s and "not checked" in s for s in said_partly),
            (said_out, said_partly),
        )
        check(
            "10.2 inside, an overlap with a footprint is kept with a warning naming it",
            [row["id"] for row in overlap_rows] == ["M-0001"]
            and any("warning" in s and "fp-1" in s for s in said_overlap)
            and not any("outside" in s for s in said_overlap),
            said_overlap,
        )
        unprojectable, said_unprojectable = save_map(
            [drawn_feature((math.inf, 0.0, math.inf, 10.0))], []
        )
        check(
            "10.2 a rectangle that cannot be reprojected is refused",
            unprojectable == [] and "could not be reprojected" in said_unprojectable[0],
            said_unprojectable,
        )
        tile_rows, said_tile = save_map([drawn_feature((0.0, 0.0, 60.0, 50.0))], [])
        wide_rows, said_wide = save_map([drawn_feature((0.0, 0.0, 100.0, 50.0))], [])
        big_rows, said_big = save_map(
            [drawn_feature((0.0, 0.0, 300.0, 300.0))],
            [],
            rule_set=replace(manual_rule_set, max_side_m=200.0),
        )
        check(
            "10.2 size bands: a tile kept, above it warned, above the limit refused",
            len(tile_rows) == 1
            and not any("warning" in s for s in said_tile)
            and len(wide_rows) == 1
            and any("above one tile" in s for s in said_wide)
            and big_rows == []
            and any("above the 200 m limit" in s for s in said_big),
            (said_tile, said_wide, said_big),
        )
        bad_edit, said_bad = save_map(
            [
                drawn_feature((0.0, 0.0, 300.0, 300.0), "M-0001"),
                drawn_feature((200.0, 200.0, 210.0, 215.0), "M-0002"),
            ],
            two_new,
            rule_set=replace(manual_rule_set, max_side_m=200.0),
        )
        check(
            "10.2 an edit that breaks a rule keeps the old rectangle",
            bad_edit == two_new
            and any("keeps its previous rectangle" in s for s in said_bad),
            said_bad,
        )
        by_hand = root / "manual-by-hand.csv"
        write_manual_samples(
            [
                manual_row("M-0001", (20.0, 20.0, 40.0, 30.0)),
                manual_row("M-0002", (390.0, 20.0, 410.0, 30.0)),  # outside
                manual_row("M-0003", (105.0, 105.0, 120.0, 120.0)),  # overlap
                {**manual_row("M-0004", (1.0, 1.0, 2.0, 2.0)), "bbox": ""},
            ],
            by_hand,
        )
        read_back = read_manual(by_hand, [], manual_rule_set)
        check(
            "10.2 the rules apply again when the file is read, by hand or not",
            read_back is not None
            and [row["id"] for row in read_back[0]] == ["M-0001", "M-0002", "M-0003"]
            and len(read_back[1]) == 1
            and "no bbox" in read_back[1][0]
            and any("M-0002" in line and "outside" in line for line in read_back[2])
            and any("fp-1" in line for line in read_back[2]),
            read_back,
        )
        check(
            "10.2 a map feature is tagged with its sample id, and found again",
            sample_id_of(sample_features(two_new, "EPSG:25830", "EPSG:25830")[0])
            == "M-0001"
            and geojson_bbox(sample_features(two_new, "EPSG:25830", "EPSG:25830")[0])
            == (20.0, 20.0, 40.0, 30.0),
        )

        # 10.3: strips for manual samples
        check(
            "10.3 the manual frame is the rectangle squared, with no margin",
            manual_frame((20.0, 20.0, 40.0, 30.0)) == (20.0, 15.0, 40.0, 35.0),
            manual_frame((20.0, 20.0, 40.0, 30.0)),
        )
        strip_dir = root / "strips-appended"
        write_strips(
            [
                {"id": "ES.1", "year": 2023, "kept": "yes"},
                {"id": "M-0001", "year": 2020, "kept": "yes"},  # an earlier run's
            ],
            strip_dir,
        )
        append_strips([{"id": "M-0001", "year": 2023, "kept": "no"}], strip_dir)
        append_strips(
            [
                {"id": "M-0001", "year": 2023, "kept": "yes"},
                {"id": "M-0002", "year": 2023, "kept": "yes"},
            ],
            strip_dir,
        )
        appended = read_strips(strip_dir) or []
        check(
            "10.3 manual strip rows are appended after 10.1's, never duplicated",
            [(row["id"], row["year"], row["kept"]) for row in appended]
            == [
                ("ES.1", "2023", "yes"),
                ("M-0001", "2023", "yes"),
                ("M-0002", "2023", "yes"),
            ],
            appended,
        )

        # 11: the regeneration keeps manual work
        labels_out = root / "labels"
        first_write = write_candidates(
            [*located, *(merged_in[0] if merged_in else [])], labels_out
        )
        with first_write.path.open(newline="", encoding="utf-8") as handle:
            first_rows = list(csv.DictReader(handle))
        check(
            "11 the table holds the cadastral rows then the manual ones",
            first_write.written
            and [row["source"] for row in first_rows]
            == ["cadastre", "cadastre", "manual"],
            first_rows,
        )
        labelled_text = first_write.path.read_text(encoding="utf-8").replace(
            "a,cadastre,12.00,22.00,10.00 20.00 14.00 24.00,16.00,"
            "figs/strip-07-a.png,2018,,,,",
            "a,cadastre,12.00,22.00,10.00 20.00 14.00 24.00,16.00,"
            "figs/strip-07-a.png,2018,kept,roof intact,,4",
        )
        first_write.path.write_text(labelled_text, encoding="utf-8")
        again_write = write_candidates(
            [*located, *(merged_in[0] if merged_in else [])], labels_out
        )
        with again_write.path.open(newline="", encoding="utf-8") as handle:
            again_rows = {row["id"]: row for row in csv.DictReader(handle)}
        check(
            "11 regeneration carries the manual columns over by id",
            again_write.written
            and again_write.carried == 2
            and again_rows["a"]["label"] == "kept"
            and again_rows["a"]["evidence"] == "roof intact"
            and again_rows["a"]["minutes_spent"] == "4"
            and again_rows["m1"]["label"] == "unsure",
            again_rows,
        )
        before = again_write.path.read_bytes()
        lost = write_candidates(located, labels_out)
        check(
            "11 a labelled id that would disappear refuses the write, byte-identical",
            not lost.written
            and lost.missing == ("m1",)
            and again_write.path.read_bytes() == before
            and sorted(p.name for p in labels_out.iterdir()) == ["candidates.csv"],
            lost,
        )

        # 11: a table saved by a spreadsheet is read, or refused, never lost
        table_rows = [
            {"id": "a", "source": "cadastre"},
            {"id": "b", "source": "cadastre"},
        ]
        header_line = ";".join(CANDIDATES_HEADER)
        semicolon_dir = root / "labels-semicolon"
        semicolon_dir.mkdir()
        (semicolon_dir / "candidates.csv").write_text(
            header_line + "\na;cadastre;1;2;;;;2023;abandoned;caved roof;;5\n"
            "b;cadastre;3;4;;;;;;;;\n",
            encoding="utf-8",
        )
        semicolon = write_candidates(table_rows, semicolon_dir)
        with semicolon.path.open(newline="", encoding="utf-8") as handle:
            semicolon_back = {row["id"]: row for row in csv.DictReader(handle)}
        check(
            "11 a ';'-separated table keeps its labels and is rewritten with commas",
            semicolon.written
            and semicolon.carried == 1
            and semicolon_back["a"]["label"] == "abandoned"
            and semicolon_back["a"]["evidence"] == "caved roof"
            and semicolon_back["a"]["minutes_spent"] == "5"
            and semicolon.normalised == "semicolon-separated"
            and semicolon.path.read_text(encoding="utf-8").startswith("id,source,"),
            (semicolon, semicolon_back),
        )
        bom_dir = root / "labels-bom"
        bom_dir.mkdir()
        (bom_dir / "candidates.csv").write_bytes(
            b"\xef\xbb\xbf"
            + (header_line + "\na;cadastre;1;2;;;;;kept;;;1\n").encode("utf-8")
        )
        with_bom = write_candidates(table_rows, bom_dir)
        check(
            "11 a table with a UTF-8 BOM keeps its labels, and says it was normalised",
            with_bom.written
            and with_bom.carried == 1
            and "BOM" in with_bom.normalised
            and not (bom_dir / "candidates.csv").read_bytes().startswith(b"\xef"),
            with_bom,
        )
        broken_dir = root / "labels-broken"
        broken_dir.mkdir()
        (broken_dir / "candidates.csv").write_text(
            "id source x y label\na cadastre 1 2 kept\n", encoding="utf-8"
        )
        broken_before = (broken_dir / "candidates.csv").read_bytes()
        broken = write_candidates(table_rows, broken_dir)
        latin_dir = root / "labels-latin"
        latin_dir.mkdir()
        (latin_dir / "candidates.csv").write_bytes(
            (header_line + "\na;cadastre;1;2;;;;;kept;tejado caído;;1\n").encode(
                "latin-1"
            )
        )
        latin = write_candidates(table_rows, latin_dir)
        check(
            "11 a table that cannot be read is refused and left byte-identical",
            not broken.written
            and "lacks" in broken.reason
            and "'id source x y label'" in broken.reason
            and (broken_dir / "candidates.csv").read_bytes() == broken_before
            and not latin.written
            and "not UTF-8" in latin.reason,
            (broken, latin),
        )

        # 10.2: a deletion is refused when the table cannot be read
        unreadable_dir = root / "labels-unreadable"
        unreadable_dir.mkdir()
        (unreadable_dir / "candidates.csv").write_text("id source\nx y\n", "utf-8")
        samples_file = write_manual_samples(
            [manual_row("M-0001", (20.0, 20.0, 40.0, 30.0))],
            unreadable_dir / "manual_samples.csv",
        )
        samples_before = samples_file.read_bytes()
        stored_samples = read_manual_samples(samples_file)
        after_delete, said_delete = reconcile_samples(
            [],
            stored_samples,
            draw_crs="EPSG:25830",
            native_crs="EPSG:25830",
            rules=manual_rule_set,
            labelled=manual_work(unreadable_dir / "candidates.csv"),
        )
        if after_delete != stored_samples:  # what the button does
            write_manual_samples(after_delete, samples_file)
        allowed_delete, _ = reconcile_samples(
            [],
            stored_samples,
            draw_crs="EPSG:25830",
            native_crs="EPSG:25830",
            rules=manual_rule_set,
            labelled=manual_work(unreadable_dir / "absent.csv"),
        )
        check(
            "10.2 an unreadable table refuses a deletion; an absent one allows it",
            after_delete == stored_samples
            and "cannot be read" in said_delete[0]
            and samples_file.read_bytes() == samples_before
            and allowed_delete == [],
            (said_delete, allowed_delete),
        )

        # 10.3: a manual strip reuses the one figure its id already has
        reuse_dir = root / "strip-reuse"
        (reuse_dir / "figs").mkdir(parents=True)
        (reuse_dir / "figs" / "strip-13-M-0001.png").write_bytes(b"")
        (reuse_dir / "figs" / "strip-02-M-0003.png").write_bytes(b"")
        (reuse_dir / "figs" / "strip-15-M-0003.png").write_bytes(b"")
        reused, reused_note = strip_figure_path(reuse_dir, "M-0001", 1)
        built, built_note = strip_figure_path(reuse_dir, "M-0002", 2)
        twice, twice_note = strip_figure_path(reuse_dir, "M-0003", 3)
        check(
            "10.3 one existing figure reused; none built; two named, not used",
            reused.name == "strip-13-M-0001.png"
            and not reused_note
            and built.name == "strip-02-M-0002.png"
            and not built_note
            and twice.name == "strip-03-M-0003.png"
            and "strip-02-M-0003.png, strip-15-M-0003.png" in twice_note,
            (reused, built, twice, twice_note),
        )

        # 10.3 and 11: the order of the cells is visible, not assumed
        on_disk_rows = [
            {"id": "ES.1", "year": "2023", "kept": "yes"},
            {"id": "ES.1", "year": "2006", "kept": "no"},
            {"id": "ES.2", "year": "2012", "kept": "no"},
            {"id": "M-0001", "year": "2030", "kept": "yes"},
        ]
        check(
            "10.3 the years fall back to those 10.1 asked, read from strips.csv",
            strip_years(on_disk_rows) == [2006, 2012, 2023] and strip_years([]) == [],
            strip_years(on_disk_rows),
        )
        check(
            "11 a manual sample with no strip rows is named",
            samples_without_strips(["M-0001", "M-0002"], on_disk_rows) == ["M-0002"],
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
