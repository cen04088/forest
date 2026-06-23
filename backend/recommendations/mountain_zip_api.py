import json
import math
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from io import BytesIO
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .loaders import clean_course_name


DEFAULT_ARCHIVE_PATHS = (
    settings.BASE_DIR.parent / "data" / "mountain.zip",
    Path.home() / "Downloads" / "mountain.zip",
)


def fetch_mountain_zip_trails(lat=None, lng=None, mountain_name="", radius_km=8, size=30):
    target = normalize_text(mountain_name)
    records = load_mountain_zip_trails_for_mountain(target) if target else []
    if not records:
        return {
            "ok": False,
            "source": "forest_mountain_zip",
            "items": [],
            "error": "Mountain zip archive not found",
        }

    candidates = records
    if target:
        matched = [
            record
            for record in candidates
            if target in normalize_text(record.get("mountain", ""))
            or target in normalize_text(record.get("name", ""))
        ]
        if not matched and (lat is None or lng is None):
            return {"ok": True, "source": "forest_mountain_zip", "total_count": 0, "items": []}
        if matched:
            candidates = matched

    if lat is not None and lng is not None:
        lat = float(lat)
        lng = float(lng)
        nearby = [
            record
            for record in candidates
            if haversine_km(lat, lng, record["lat"], record["lng"]) <= float(radius_km)
        ]
        if nearby:
            candidates = nearby

    return {
        "ok": True,
        "source": "forest_mountain_zip",
        "total_count": len(candidates),
        "items": candidates[: int(size)],
    }


@lru_cache(maxsize=1)
def load_mountain_zip_trails():
    archive_path = resolve_archive_path()
    if not archive_path:
        return []

    courses = []
    with zipfile.ZipFile(archive_path) as archive:
        geojson_entries = sorted(
            entry for entry in archive.namelist() if entry.endswith("_geojson.zip")
        )
        for entry_name in geojson_entries:
            try:
                courses.extend(read_geojson_bundle(archive, entry_name))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError):
                continue

    return courses


@lru_cache(maxsize=128)
def load_mountain_zip_trails_for_mountain(target):
    archive_path = resolve_archive_path()
    if not archive_path or not target:
        return []

    index = mountain_zip_index()
    entry_names = index.get(target, [])
    if not entry_names:
        entry_names = [
            entry
            for name, entries in index.items()
            if target in name
            for entry in entries
        ]
    if not entry_names:
        return []

    courses = []
    with zipfile.ZipFile(archive_path) as archive:
        for entry_name in sorted(set(entry_names)):
            try:
                courses.extend(read_geojson_bundle(archive, entry_name))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile, ET.ParseError):
                continue

    return courses


@lru_cache(maxsize=1)
def mountain_zip_index():
    archive_path = resolve_archive_path()
    if not archive_path:
        return {}

    index = {}
    with zipfile.ZipFile(archive_path) as archive:
        for entry_name in sorted(entry for entry in archive.namelist() if entry.endswith("_geojson.zip")):
            try:
                mountain = read_bundle_mountain_name(archive, entry_name)
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile):
                continue
            key = normalize_text(mountain)
            if key:
                index.setdefault(key, []).append(entry_name)
    return index


def read_bundle_mountain_name(outer_archive, entry_name):
    with outer_archive.open(entry_name) as nested_file:
        with zipfile.ZipFile(BytesIO(nested_file.read())) as nested_archive:
            line_name = first_entry(
                nested_archive,
                lambda name: name.endswith(".json")
                and not Path(name).name.startswith("PMNTN_SPOT_"),
            )
            if not line_name:
                return ""
            with nested_archive.open(line_name) as line_file:
                payload = json.loads(line_file.read().decode("utf-8-sig"))
            for feature in (payload.get("features") or [])[:5]:
                mountain = (feature.get("attributes") or {}).get("MNTN_NM")
                if clean_value(mountain):
                    return mountain
    return ""


def resolve_archive_path():
    configured = os.environ.get("MOUNTAIN_ZIP_PATH", "").strip()
    candidates = [Path(configured)] if configured else []
    candidates.extend(DEFAULT_ARCHIVE_PATHS)
    for path in candidates:
        if path and path.exists():
            return path
    return None


def read_geojson_bundle(outer_archive, entry_name):
    with outer_archive.open(entry_name) as nested_file:
        with zipfile.ZipFile(BytesIO(nested_file.read())) as nested_archive:
            line_name = first_entry(
                nested_archive,
                lambda name: name.endswith(".json")
                and Path(name).name.startswith("PMNTN_")
                and not Path(name).name.startswith("PMNTN_SPOT_"),
            )
            if not line_name:
                return []

            with nested_archive.open(line_name) as line_file:
                payload = json.loads(line_file.read().decode("utf-8-sig"))

            mountain_code = parse_mountain_code(entry_name)
            gpx_entry = f"mountain/{mountain_code}_gpx.zip" if mountain_code else ""
            gpx_tracks = read_gpx_tracks(outer_archive, gpx_entry) if gpx_entry else []
            return normalize_features(payload, gpx_tracks, entry_name)


def first_entry(archive, predicate):
    for name in archive.namelist():
        if predicate(name):
            return name
    return None


def parse_mountain_code(entry_name):
    match = re.search(r"/(\d+)_geojson\.zip$", entry_name)
    return match.group(1) if match else ""


def read_gpx_tracks(outer_archive, entry_name):
    if entry_name not in set(outer_archive.namelist()):
        return []
    with outer_archive.open(entry_name) as nested_file:
        with zipfile.ZipFile(BytesIO(nested_file.read())) as nested_archive:
            gpx_name = first_entry(
                nested_archive,
                lambda name: name.endswith(".gpx")
                and Path(name).name.startswith("PMNTN_")
                and not Path(name).name.startswith("PMNTN_SPOT_"),
            )
            if not gpx_name:
                return []
            with nested_archive.open(gpx_name) as gpx_file:
                return parse_gpx_tracks(gpx_file.read())


def parse_gpx_tracks(body):
    root = ET.fromstring(body)
    namespace = {"gpx": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
    selector = ".//gpx:trkseg" if namespace else ".//trkseg"
    point_selector = "gpx:trkpt" if namespace else "trkpt"
    tracks = []
    for segment in root.findall(selector, namespace):
        points = []
        for point in segment.findall(point_selector, namespace):
            lat = point.get("lat")
            lng = point.get("lon")
            if lat is None or lng is None:
                continue
            points.append({"lat": float(lat), "lng": float(lng)})
        if len(points) >= 2:
            tracks.append(points)
    return tracks


def normalize_features(payload, gpx_tracks, bundle_name):
    features = payload.get("features") or []
    groups = {}
    for index, feature in enumerate(features, start=1):
        attributes = feature.get("attributes") or {}
        geometry = geometry_from_gpx_or_geojson(gpx_tracks, index - 1, feature.get("geometry") or {})
        if len(geometry) < 2:
            continue

        mountain = clean_value(attributes.get("MNTN_NM")) or "산림청 등산로"
        name = clean_course_name(clean_value(attributes.get("PMNTN_NM")) or f"{mountain} 등산로")
        key = (clean_value(attributes.get("MNTN_CODE")), mountain, name)
        group = groups.setdefault(
            key,
            {
                "attributes": attributes,
                "distance_km": 0,
                "segments": [],
                "risks": [],
                "surfaces": [],
                "closed": False,
            },
        )

        distance_km = parse_float(attributes.get("PMNTN_LT")) or route_length_km(geometry)
        if distance_km and distance_km > 100:
            distance_km = distance_km / 1000
        group["distance_km"] += distance_km or 0
        group["segments"].append(geometry)
        if clean_value(attributes.get("PMNTN_RISK")):
            group["risks"].append(clean_value(attributes.get("PMNTN_RISK")))
        if clean_value(attributes.get("PMNTN_MTRQ")):
            group["surfaces"].append(clean_value(attributes.get("PMNTN_MTRQ")))
        if clean_value(attributes.get("PMNTN_CNRL")):
            group["closed"] = True

    courses = []
    course_index = 1
    for _index, ((mountain_code, mountain, name), group) in enumerate(groups.items(), start=1):
        attributes = group["attributes"]
        components = connected_segment_components(group["segments"])
        for component_index, component in enumerate(components, start=1):
            route_geometry = simplify_points(order_component_segments(component), max_points=160)
            if len(route_geometry) < 2:
                continue

            distance_km = round(sum(route_length_km(segment) for segment in component), 2)
            if distance_km < 0.8:
                continue

            duration_min = max(round(distance_km * 34), 20)
            difficulty = normalize_difficulty(attributes.get("PMNTN_DFFL"), distance_km, duration_min)
            trailhead = route_geometry[0]
            risk = clean_value(attributes.get("PMNTN_RISK"))
            closed = group["closed"]
            course_name = name if len(components) == 1 else f"{name} {component_index}"

            courses.append(
                {
                    "id": f"forest-zip-{mountain_code}-{normalize_text(name) or course_index}-{component_index}",
                    "mountain": mountain,
                    "name": course_name,
                    "region": "산림청 등산로 데이터",
                    "difficulty": difficulty,
                    "distance_km": distance_km,
                    "duration_min": duration_min,
                    "elevation_gain_m": round(distance_km * {"easy": 35, "medium": 65, "hard": 95}[difficulty]),
                    "lat": trailhead["lat"],
                    "lng": trailhead["lng"],
                    "route_geometry": route_geometry,
                    "crowding": 0.25,
                    "highlights": build_highlights(attributes, group),
                    "source": "산림청_등산로_mountain.zip",
                    "road_risk": risk,
                    "is_closed": bool(closed),
                    "recommended_flag": clean_value(attributes.get("PMNTN_RECO")),
                    "data_standard_date": clean_value(attributes.get("DATA_STDR_")),
                    "properties": {
                        "bundle": bundle_name,
                        "surface": ", ".join(unique_values(group["surfaces"])[:3]),
                        "control": clean_value(attributes.get("PMNTN_CNRL")),
                    },
                }
            )
            course_index += 1
    return courses


def geometry_from_gpx_or_geojson(gpx_tracks, index, geometry):
    if index < len(gpx_tracks):
        return gpx_tracks[index]
    paths = geometry.get("paths") or []
    if not paths:
        return []
    points = []
    for point in paths[0]:
        if len(point) < 2:
            continue
        points.append(korea_central_belt_to_wgs84(point[0], point[1]))
    return points


def korea_central_belt_to_wgs84(x, y):
    a = 6378137.0
    inv_f = 298.257222101
    f = 1 / inv_f
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    k0 = 1.0
    x0 = 200000.0
    y0 = 600000.0
    lon0 = math.radians(127.0)
    lat0 = math.radians(38.0)

    def meridional_arc(phi):
        return a * (
            (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * phi
            - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * phi)
            + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * phi)
            - (35 * e2**3 / 3072) * math.sin(6 * phi)
        )

    m0 = meridional_arc(lat0)
    m = m0 + (y - y0) / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))
    e1 = (1 - math.sqrt(1 - e2)) / (1 + math.sqrt(1 - e2))
    phi1 = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * math.sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * math.sin(4 * mu)
        + (151 * e1**3 / 96) * math.sin(6 * mu)
        + (1097 * e1**4 / 512) * math.sin(8 * mu)
    )

    sin_phi1 = math.sin(phi1)
    cos_phi1 = math.cos(phi1)
    tan_phi1 = math.tan(phi1)
    n1 = a / math.sqrt(1 - e2 * sin_phi1**2)
    r1 = a * (1 - e2) / (1 - e2 * sin_phi1**2) ** 1.5
    t1 = tan_phi1**2
    c1 = ep2 * cos_phi1**2
    d = (x - x0) / (n1 * k0)

    lat = phi1 - (n1 * tan_phi1 / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lon = lon0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / cos_phi1

    return {"lat": math.degrees(lat), "lng": math.degrees(lon)}


def normalize_difficulty(value, distance_km, duration_min):
    text = clean_value(value)
    if "어려" in text or "상" in text or distance_km >= 6 or duration_min >= 180:
        return "hard"
    if "보통" in text or "중" in text or distance_km >= 3 or duration_min >= 90:
        return "medium"
    return "easy"


def build_highlights(attributes, group=None):
    group = group or {}
    highlights = []
    main = clean_value(attributes.get("PMNTN_MAIN"))
    if main:
        highlights.append(main)
    surfaces = unique_values(group.get("surfaces") or [clean_value(attributes.get("PMNTN_MTRQ"))])
    if surfaces:
        highlights.append(", ".join(surfaces[:3]))
    risks = unique_values(group.get("risks") or [clean_value(attributes.get("PMNTN_RISK"))])
    risk = risks[0] if risks else ""
    if risk:
        highlights.append(f"위험요인: {risk}")
    if group.get("closed") or clean_value(attributes.get("PMNTN_CNRL")):
        highlights.append("통제 정보 확인 필요")
    return highlights[:3] or ["산림청 등산로 경로 데이터"]


def connected_segment_components(segments, threshold_m=35):
    usable = [segment for segment in segments if len(segment) >= 2]
    if not usable:
        return []

    parent = list(range(len(usable)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(a, b):
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    threshold_km = threshold_m / 1000
    endpoints = [(segment[0], segment[-1]) for segment in usable]
    for i, first in enumerate(endpoints):
        for j in range(i + 1, len(endpoints)):
            second = endpoints[j]
            if endpoint_distance_km(first, second) <= threshold_km:
                union(i, j)

    buckets = {}
    for index, segment in enumerate(usable):
        buckets.setdefault(find(index), []).append(segment)

    components = sorted(buckets.values(), key=lambda value: sum(route_length_km(s) for s in value), reverse=True)
    return components[:4]


def endpoint_distance_km(first, second):
    return min(
        haversine_km(a["lat"], a["lng"], b["lat"], b["lng"])
        for a in first
        for b in second
    )


def order_component_segments(segments, max_gap_m=45):
    remaining = [list(segment) for segment in segments if len(segment) >= 2]
    if not remaining:
        return []

    start_index = min(range(len(remaining)), key=lambda i: (remaining[i][0]["lat"], remaining[i][0]["lng"]))
    route = remaining.pop(start_index)
    max_gap_km = max_gap_m / 1000

    while remaining:
        tail = route[-1]
        best = None
        for index, segment in enumerate(remaining):
            start_gap = haversine_km(tail["lat"], tail["lng"], segment[0]["lat"], segment[0]["lng"])
            end_gap = haversine_km(tail["lat"], tail["lng"], segment[-1]["lat"], segment[-1]["lng"])
            gap = min(start_gap, end_gap)
            if best is None or gap < best[0]:
                best = (gap, index, end_gap < start_gap)

        if best is None or best[0] > max_gap_km:
            break

        _gap, index, should_reverse = best
        segment = remaining.pop(index)
        if should_reverse:
            segment = list(reversed(segment))
        route.extend(segment[1:])

    return route


def unique_values(values):
    result = []
    seen = set()
    for value in values:
        cleaned = clean_value(value)
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def clean_value(value):
    text = str(value or "").strip()
    return "" if not text else text


def parse_float(value):
    try:
        return float(str(value or "").replace(",", "").strip())
    except ValueError:
        return None


def simplify_points(points, max_points=96):
    if len(points) <= max_points:
        return points
    step = max(1, math.ceil(len(points) / max_points))
    simplified = points[::step]
    if simplified[-1] != points[-1]:
        simplified.append(points[-1])
    return simplified


def route_length_km(points):
    if len(points) < 2:
        return 0
    return sum(haversine_km(a["lat"], a["lng"], b["lat"], b["lng"]) for a, b in zip(points, points[1:]))


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def normalize_text(value):
    return "".join(str(value or "").split()).lower()
