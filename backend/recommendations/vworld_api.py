import json
import os
import urllib.parse
import urllib.request
from functools import lru_cache
from math import asin, cos, radians, sin, sqrt

from .loaders import load_vworld_api_key


VWORLD_DATA_URL = "https://api.vworld.kr/req/data"
VWORLD_TRAIL_LAYER = "LT_L_FRSTCLIMB"


def fetch_vworld_trails(lat=None, lng=None, mountain_name="", radius_km=5, page_no=1, size=50, timeout=8):
    api_key = load_vworld_api_key()
    if not api_key:
        return {"ok": False, "error": "Missing VWorld API key", "items": []}

    base_query = {
        "service": "data",
        "request": "GetFeature",
        "version": "2.0",
        "data": VWORLD_TRAIL_LAYER,
        "format": "json",
        "crs": "EPSG:4326",
        "page": int(page_no),
        "size": int(size),
        "key": api_key,
    }

    if lat is not None and lng is not None:
        base_query["geomFilter"] = build_bbox_filter(float(lat), float(lng), float(radius_km))

    last_result = None
    for domain in vworld_domain_candidates():
        query = {**base_query}
        if domain:
            query["domain"] = domain
        result = _cached_fetch_vworld_trails(tuple(sorted(query.items())), mountain_name.strip(), timeout)
        last_result = result
        if result.get("ok") or not is_auth_error(result.get("error", "")):
            return result
    return last_result or {"ok": False, "error": "VWorld trail API request failed", "items": []}


def is_auth_error(error):
    normalized = str(error or "").lower()
    return any(keyword in normalized for keyword in ("인증", "auth", "key", "키"))


def vworld_domain_candidates():
    configured = os.environ.get("VWORLD_API_DOMAIN", "").strip()
    candidates = [
        configured,
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "",
    ]
    seen = set()
    return [domain for domain in candidates if not (domain in seen or seen.add(domain))]


@lru_cache(maxsize=128)
def _cached_fetch_vworld_trails(query_items, mountain_name, timeout):
    query = dict(query_items)
    safe_query = urllib.parse.urlencode(query, safe="(),:%")
    url = f"{VWORLD_DATA_URL}?{safe_query}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:
        return {"ok": False, "error": f"VWorld trail API request failed: {exc}", "items": []}

    return parse_vworld_trails_json(body, mountain_name=mountain_name)


def build_bbox_filter(lat, lng, radius_km):
    lat_delta = radius_km / 111.0
    lng_delta = radius_km / max(111.0 * cos(radians(lat)), 1)
    min_lng = lng - lng_delta
    min_lat = lat - lat_delta
    max_lng = lng + lng_delta
    max_lat = lat + lat_delta
    return f"BOX({min_lng:.6f},{min_lat:.6f},{max_lng:.6f},{max_lat:.6f})"


def parse_vworld_trails_json(body, mountain_name=""):
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "error": "VWorld response was not valid JSON", "items": []}

    response = payload.get("response", {})
    status = response.get("status", "")
    if status and status != "OK":
        error = response.get("error") or {}
        return {"ok": False, "error": error.get("text", "VWorld returned an error"), "items": []}

    features = response.get("result", {}).get("featureCollection", {}).get("features", [])
    items = []
    for index, feature in enumerate(features, start=1):
        item = normalize_vworld_feature(index, feature, mountain_name)
        if item:
            items.append(item)

    return {"ok": True, "total_count": parse_total_count(response), "items": items}


def normalize_vworld_feature(index, feature, mountain_name=""):
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    route_geometry = extract_route_geometry(geometry)
    if not route_geometry:
        return None

    name = first_text(properties, ["mntil_nm", "mntilnm", "mtn_nm", "mntn_nm", "name", "road_name", "명칭"])
    course_name = name or (f"{mountain_name} 등산로" if mountain_name else "브이월드 등산로")
    center = route_center(route_geometry)
    distance_km = first_float(properties, ["length", "len", "shape_leng", "st_length"])
    if distance_km is None:
        distance_km = route_length_km(route_geometry)
    if distance_km and distance_km > 100:
        distance_km = distance_km / 1000

    duration_min = max(round((distance_km or 1.5) * 34), 20)
    difficulty = infer_difficulty(distance_km or 0, duration_min)

    return {
        "id": f"vworld-{index}-{course_name}",
        "mountain": mountain_name or first_text(properties, ["mntn_nm", "mtn_nm", "mountain"]) or "브이월드 등산로",
        "name": course_name,
        "region": first_text(properties, ["emd_kor_nm", "sig_kor_nm", "addr", "region"]) or "VWorld 국가중점데이터",
        "difficulty": difficulty,
        "distance_km": round(distance_km or 0, 2),
        "duration_min": duration_min,
        "elevation_gain_m": round((distance_km or 1.5) * {"easy": 35, "medium": 65, "hard": 95}[difficulty]),
        "lat": center["lat"],
        "lng": center["lng"],
        "crowding": 0.28,
        "highlights": ["브이월드 등산로 지오메트리", "카카오맵 경로 표시 가능", "위험 구간 시각화 후보"],
        "source": "브이월드_등산로_LT_L_FRSTCLIMB",
        "route_geometry": route_geometry,
        "properties": safe_public_properties(properties),
    }


def extract_route_geometry(geometry):
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    if geometry_type == "LineString":
        return coordinates_to_lat_lng(coordinates)
    if geometry_type == "MultiLineString":
        longest = max(coordinates, key=len, default=[])
        return coordinates_to_lat_lng(longest)
    return []


def coordinates_to_lat_lng(coordinates):
    points = []
    for point in coordinates:
        if len(point) < 2:
            continue
        lng, lat = point[:2]
        try:
            points.append({"lat": float(lat), "lng": float(lng)})
        except (TypeError, ValueError):
            continue
    return points


def route_center(points):
    midpoint = points[len(points) // 2]
    return {"lat": midpoint["lat"], "lng": midpoint["lng"]}


def route_length_km(points):
    if len(points) < 2:
        return 0
    return sum(haversine_km(a["lat"], a["lng"], b["lat"], b["lng"]) for a, b in zip(points, points[1:]))


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def first_text(properties, keys):
    for key in keys:
        value = properties.get(key)
        if value not in (None, ""):
            return str(value).strip()
    return ""


def first_float(properties, keys):
    for key in keys:
        try:
            value = float(properties.get(key))
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return None


def infer_difficulty(distance_km, duration_min):
    if distance_km >= 6 or duration_min >= 180:
        return "hard"
    if distance_km >= 3 or duration_min >= 90:
        return "medium"
    return "easy"


def parse_total_count(response):
    record = response.get("record") or {}
    try:
        return int(record.get("total") or 0)
    except (TypeError, ValueError):
        return 0


def safe_public_properties(properties):
    allowlist = ["mntil_nm", "mntilnm", "mtn_nm", "mntn_nm", "emd_kor_nm", "sig_kor_nm", "length", "shape_leng"]
    return {key: properties[key] for key in allowlist if key in properties}
