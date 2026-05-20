import math
import struct
from functools import lru_cache

from django.conf import settings

from .loaders import clean_course_name
from .vworld_api import route_length_km


ROAD_DIR = settings.BASE_DIR.parent / "road" / "WG_MT_WAY"
ROAD_SHP_PATH = ROAD_DIR / "WG_MT_WAY.shp"
ROAD_DBF_PATH = ROAD_DIR / "WG_MT_WAY.dbf"


def fetch_local_road_trails(lat=None, lng=None, mountain_name="", radius_km=8, size=30):
    records = load_local_road_trails()
    if not records:
        return {"ok": False, "source": "local_road_shp", "items": [], "error": "Local road shapefile not found"}

    candidates = records
    target = normalize_text(mountain_name)
    if target:
        matched = [
            record
            for record in candidates
            if target in normalize_text(record.get("mountain", ""))
            or target in normalize_text(record.get("name", ""))
            or target in normalize_text(record.get("region", ""))
        ]
        if not matched:
            return {"ok": True, "source": "local_road_shp", "total_count": 0, "items": []}
        candidates = matched

    if lat is not None and lng is not None:
        lat = float(lat)
        lng = float(lng)
        candidates = [
            record
            for record in candidates
            if haversine_km(lat, lng, record["lat"], record["lng"]) <= float(radius_km)
        ] or candidates

    return {
        "ok": True,
        "source": "local_road_shp",
        "total_count": len(candidates),
        "items": candidates[: int(size)],
    }


@lru_cache(maxsize=1)
def load_local_road_trails():
    if not ROAD_SHP_PATH.exists() or not ROAD_DBF_PATH.exists():
        return []

    rows = read_dbf_records(ROAD_DBF_PATH)
    shapes = read_polyline_shapes(ROAD_SHP_PATH)
    courses = []
    for index, (row, shape) in enumerate(zip(rows, shapes), start=1):
        course = normalize_road_record(index, row, shape)
        if course:
            courses.append(course)
    return courses


def normalize_road_record(index, row, points):
    route_geometry = simplify_points([korea_2000_to_wgs84(x, y) for x, y in points], max_points=96)
    if len(route_geometry) < 2:
        return None

    distance_km = parse_float(row.get("PMNTN_LT")) or route_length_km(route_geometry)
    if distance_km and distance_km > 100:
        distance_km = distance_km / 1000
    distance_km = round(distance_km or route_length_km(route_geometry), 2)
    duration_min = max(round(distance_km * 34), 20)
    difficulty = normalize_difficulty(row.get("PMNTN_DFFL"), distance_km, duration_min)
    center = route_geometry[len(route_geometry) // 2]

    mountain = row.get("MNTN_NM") or "등산로"
    name = clean_course_name(row.get("PMNTN_NM") or row.get("PMNTN_MAIN") or f"{mountain} 등산로")
    risk = row.get("PMNTN_RISK", "")

    return {
        "id": f"local-road-{index}-{row.get('MNTN_ID') or row.get('PMNTN_SN') or name}",
        "mountain": mountain,
        "name": name,
        "region": "브이월드 등산로 로컬 SHP",
        "difficulty": difficulty,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "elevation_gain_m": round(distance_km * {"easy": 35, "medium": 65, "hard": 95}[difficulty]),
        "lat": center["lat"],
        "lng": center["lng"],
        "crowding": 0.28,
        "highlights": build_road_highlights(row),
        "source": "road/WG_MT_WAY.shp",
        "route_geometry": route_geometry,
        "road_risk": risk,
    }


def read_polyline_shapes(path):
    data = path.read_bytes()
    offset = 100
    shapes = []
    while offset + 8 <= len(data):
        content_length = struct.unpack(">i", data[offset + 4 : offset + 8])[0] * 2
        content_offset = offset + 8
        content = data[content_offset : content_offset + content_length]
        offset = content_offset + content_length
        if len(content) < 44:
            continue
        shape_type = struct.unpack("<i", content[0:4])[0]
        if shape_type != 3:
            continue
        num_parts = struct.unpack("<i", content[36:40])[0]
        num_points = struct.unpack("<i", content[40:44])[0]
        parts_offset = 44
        points_offset = parts_offset + num_parts * 4
        points = []
        for point_index in range(num_points):
            point_offset = points_offset + point_index * 16
            x, y = struct.unpack("<dd", content[point_offset : point_offset + 16])
            points.append((x, y))
        shapes.append(points)
    return shapes


def read_dbf_records(path):
    data = path.read_bytes()
    record_count = struct.unpack("<I", data[4:8])[0]
    header_length = struct.unpack("<H", data[8:10])[0]
    record_length = struct.unpack("<H", data[10:12])[0]
    field_count = (header_length - 33) // 32
    fields = []
    for index in range(field_count):
        offset = 32 + index * 32
        raw_name = data[offset : offset + 11].split(b"\x00", 1)[0]
        fields.append({"name": raw_name.decode("ascii", errors="ignore"), "length": data[offset + 16]})

    records = []
    for record_index in range(record_count):
        offset = header_length + record_index * record_length
        if offset + record_length > len(data) or data[offset : offset + 1] == b"*":
            continue
        cursor = offset + 1
        row = {}
        for field in fields:
            value = data[cursor : cursor + field["length"]]
            cursor += field["length"]
            row[field["name"]] = value.decode("cp949", errors="ignore").strip()
        records.append(row)
    return records


def korea_2000_to_wgs84(x, y):
    a = 6378137.0
    inv_f = 298.257222101
    f = 1 / inv_f
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)
    k0 = 0.9996
    x0 = 1000000.0
    y0 = 2000000.0
    lon0 = math.radians(127.5)
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


def simplify_points(points, max_points=96):
    if len(points) <= max_points:
        return points
    step = max(1, math.ceil(len(points) / max_points))
    simplified = points[::step]
    if simplified[-1] != points[-1]:
        simplified.append(points[-1])
    return simplified


def normalize_difficulty(value, distance_km, duration_min):
    text = str(value or "")
    if "어려" in text or "상" in text or distance_km >= 6 or duration_min >= 180:
        return "hard"
    if "보통" in text or "중" in text or distance_km >= 3 or duration_min >= 90:
        return "medium"
    return "easy"


def build_road_highlights(row):
    highlights = []
    if row.get("PMNTN_MAIN"):
        highlights.append(row["PMNTN_MAIN"])
    if row.get("PMNTN_MTRQ"):
        highlights.append(row["PMNTN_MTRQ"])
    if row.get("PMNTN_RISK"):
        highlights.append(f"위험요인: {row['PMNTN_RISK']}")
    return highlights[:3] or ["로컬 등산로 선형 데이터"]


def parse_float(value):
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return None


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


def normalize_text(value):
    return "".join(str(value or "").split()).lower()
