import csv
import os
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .data import COURSES
from .mountain_coordinates import find_mountain_coordinates


TRAIL_CSV_PATH = settings.BASE_DIR.parent / "국립공원공단_탐방로_20240911.csv"
DISASTER_RISK_CSV_PATH = settings.BASE_DIR.parent / "국립공원공단_재난위험지구_20240904.csv"
KEY_FILE_PATH = settings.BASE_DIR.parent / "key.txt"
DATA_LINK_FILE_PATH = settings.BASE_DIR.parent / "data" / "데이터 링크.txt"
VWORLD_KEY_FILE_PATH = settings.BASE_DIR.parent / "vworld_key.txt"
KMA_API_HUB_KEY_FILE_PATH = settings.BASE_DIR.parent / "kma_api_hub_key.txt"


@lru_cache(maxsize=1)
def load_public_trail_courses():
    if not TRAIL_CSV_PATH.exists():
        return COURSES

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return _read_trail_csv(TRAIL_CSV_PATH, encoding)
        except UnicodeDecodeError:
            continue

    return COURSES


def _read_trail_csv(path, encoding):
    segments = []
    seen_keys = set()
    with Path(path).open(encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            course = normalize_trail_row(index, row)
            if course and course["dedupe_key"] not in seen_keys:
                seen_keys.add(course["dedupe_key"])
                course.pop("dedupe_key")
                segments.append(course)

    courses = merge_connected_trail_segments(segments)
    return courses or COURSES


@lru_cache(maxsize=1)
def load_disaster_risk_zones():
    if not DISASTER_RISK_CSV_PATH.exists():
        return []

    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return _read_disaster_risk_csv(DISASTER_RISK_CSV_PATH, encoding)
        except UnicodeDecodeError:
            continue
    return []


def _read_disaster_risk_csv(path, encoding):
    zones = []
    with Path(path).open(encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            zone = normalize_disaster_risk_row(index, row)
            if zone:
                zones.append(zone)
    return zones


def normalize_disaster_risk_row(index, row):
    district = clean_text(row.get("지구명"))
    location = clean_text(row.get("위치"))
    facility = clean_text(row.get("시설명"))
    risk_factor = clean_text(row.get("위험요인"))
    if not any([district, location, facility, risk_factor]):
        return None

    return {
        "id": f"disaster-risk-{index}",
        "district": district,
        "location": location,
        "facility": facility,
        "has_signage": parse_int(row.get("표지판설치")),
        "risk_factor": risk_factor,
        "expected_daily_visitors": parse_int(row.get("일최대예상탐방객")),
        "evacuation_capacity": parse_int(row.get("대피계획인원")),
        "evacuation_place": clean_text(row.get("대피장소")),
        "rescue_equipment": clean_text(row.get("구조대편성 및 구조장비현황")),
        "control_facility": clean_text(row.get("통제시설")),
        "source": "국립공원공단_재난위험지구_20240904",
        "search_text": normalize_search_text(" ".join([district, location, facility, risk_factor])),
    }


def normalize_trail_row(index, row):
    name = clean_text(row.get("시설물명칭"))
    start = clean_text(row.get("구간_시작지점"))
    waypoint = clean_text(row.get("구간_경유지점"))
    end = clean_text(row.get("구간_종착지점"))
    distance_km = parse_distance_km(row.get("탐방로길이"))

    if not name or distance_km <= 0:
        return None

    up_minutes = parse_int(row.get("소요시간_상행"))
    down_minutes = parse_int(row.get("소요시간_하행"))
    duration_min = max(up_minutes, down_minutes, estimate_duration(distance_km))
    difficulty = infer_difficulty(distance_km, duration_min)

    dedupe_key = "|".join([name, start, waypoint, end, str(distance_km)])

    inferred_mountain = infer_mountain_name(name, start, waypoint, end)
    coordinate_mountain, coordinates = find_mountain_coordinates(inferred_mountain, name, start, waypoint, end)
    mountain = coordinate_mountain or inferred_mountain

    return {
        "id": f"public-{index}",
        "mountain": mountain,
        "name": name,
        "region": coordinates["region"] if coordinates else "국립공원 탐방로",
        "difficulty": difficulty,
        "distance_km": distance_km,
        "duration_min": duration_min,
        "elevation_gain_m": infer_elevation_gain(distance_km, difficulty),
        "lat": coordinates["lat"] if coordinates else None,
        "lng": coordinates["lng"] if coordinates else None,
        "crowding": 0.35,
        "highlights": build_highlights(start, waypoint, end),
        "source": "국립공원공단_탐방로_20240911+좌표보강" if coordinates else "국립공원공단_탐방로_20240911",
        "segment_nodes": build_segment_nodes(start, waypoint, end),
        "segment_count": 1,
        "dedupe_key": dedupe_key,
    }


def merge_connected_trail_segments(segments):
    grouped = {}
    for segment in segments:
        nodes = [normalize_node(node) for node in segment.get("segment_nodes", []) if normalize_node(node)]
        if len(nodes) < 2:
            grouped.setdefault(("single", segment["id"]), []).append(segment)
            continue
        grouped.setdefault((segment.get("mountain") or "국립공원", segment.get("source") or ""), []).append(segment)

    merged_courses = []
    for key, group in grouped.items():
        if key[0] == "single":
            merged_courses.extend(strip_segment_fields(course) for course in group)
            continue
        merged_courses.extend(merge_segment_group(group))
    return merged_courses


def merge_segment_group(group):
    node_to_indexes = {}
    for index, segment in enumerate(group):
        nodes = [normalize_node(node) for node in segment.get("segment_nodes", []) if normalize_node(node)]
        for node in set(nodes):
            node_to_indexes.setdefault(node, set()).add(index)

    visited = set()
    courses = []
    for index in range(len(group)):
        if index in visited:
            continue
        stack = [index]
        component = []
        visited.add(index)
        while stack:
            current = stack.pop()
            component.append(group[current])
            for node in [normalize_node(node) for node in group[current].get("segment_nodes", []) if normalize_node(node)]:
                for next_index in node_to_indexes.get(node, set()):
                    if next_index not in visited:
                        visited.add(next_index)
                        stack.append(next_index)

        if len(component) == 1:
            courses.append(strip_segment_fields(component[0]))
        elif should_merge_trail_component(component):
            courses.append(build_merged_course(component))
        else:
            courses.extend(strip_segment_fields(segment) for segment in component)
    return courses


def should_merge_trail_component(component):
    distance_km = sum(float(segment.get("distance_km") or 0) for segment in component)
    return len(component) <= 8 and distance_km <= 15


def build_merged_course(component):
    first = component[0]
    all_nodes = []
    degree = {}
    for segment in component:
        nodes = [node for node in segment.get("segment_nodes", []) if node]
        all_nodes.extend(nodes)
        if len(nodes) >= 2:
            start = normalize_node(nodes[0])
            end = normalize_node(nodes[-1])
            degree[start] = degree.get(start, 0) + 1
            degree[end] = degree.get(end, 0) + 1

    endpoints = [node for node in all_nodes if degree.get(normalize_node(node), 0) == 1]
    start = endpoints[0] if endpoints else all_nodes[0]
    end = endpoints[-1] if len(endpoints) > 1 else all_nodes[-1]
    waypoints = [node for node in all_nodes if node not in {start, end}]
    distance_km = round(sum(float(segment.get("distance_km") or 0) for segment in component), 2)
    duration_min = sum(int(segment.get("duration_min") or 0) for segment in component)
    difficulty = infer_difficulty(distance_km, duration_min)
    lat_values = [segment["lat"] for segment in component if segment.get("lat") is not None]
    lng_values = [segment["lng"] for segment in component if segment.get("lng") is not None]

    return {
        **strip_segment_fields(first),
        "id": f"public-merged-{stable_text_id(first.get('mountain'))}-{stable_text_id(start)}-{stable_text_id(end)}-{len(component)}",
        "name": f"{start}~{end}",
        "difficulty": difficulty,
        "distance_km": distance_km,
        "duration_min": max(duration_min, estimate_duration(distance_km)),
        "elevation_gain_m": infer_elevation_gain(distance_km, difficulty),
        "lat": round(sum(lat_values) / len(lat_values), 6) if lat_values else None,
        "lng": round(sum(lng_values) / len(lng_values), 6) if lng_values else None,
        "highlights": build_merged_highlights(start, waypoints, end, len(component)),
        "segment_count": len(component),
    }


def build_merged_highlights(start, waypoints, end, count):
    highlights = [f"출발: {start}"]
    unique_waypoints = []
    for waypoint in waypoints:
        if waypoint and waypoint not in {start, end} and waypoint not in unique_waypoints:
            unique_waypoints.append(waypoint)
    if unique_waypoints:
        highlights.append(f"주요 경유: {', '.join(unique_waypoints[:3])}")
    highlights.append(f"도착: {end}")
    highlights.append(f"{count}개 연결 구간 통합")
    return highlights[:4]


def strip_segment_fields(course):
    clean = dict(course)
    clean.pop("segment_nodes", None)
    return clean


def clean_text(value):
    return (value or "").strip()


def normalize_search_text(value):
    return re.sub(r"\s+", "", str(value or "").lower())


def normalize_node(value):
    return re.sub(r"\s+", "", str(value or "").strip().lower())


def stable_text_id(value):
    return re.sub(r"[^0-9a-zA-Z가-힣]+", "", str(value or ""))[:24] or "course"


def parse_distance_km(value):
    try:
        raw = float(str(value or "0").strip())
    except ValueError:
        return 0

    if raw > 100:
        return round(raw / 1000, 2)
    return round(raw, 2)


def parse_int(value):
    try:
        return int(float(str(value or "0").strip()))
    except ValueError:
        return 0


def estimate_duration(distance_km):
    return max(round(distance_km * 32), 15)


def infer_difficulty(distance_km, duration_min):
    if distance_km >= 6 or duration_min >= 180:
        return "hard"
    if distance_km >= 3 or duration_min >= 90:
        return "medium"
    return "easy"


def infer_elevation_gain(distance_km, difficulty):
    multiplier = {"easy": 35, "medium": 65, "hard": 95}[difficulty]
    return round(distance_km * multiplier)


def infer_mountain_name(*parts):
    joined = " ".join(part for part in parts if part)
    known_names = [
        "북한산",
        "도봉산",
        "지리산",
        "월출산",
        "한려해상",
        "태안해안",
        "덕유산",
        "변산반도",
        "소백산",
        "오대산",
        "가야산",
        "치악산",
        "설악산",
        "월악산",
        "계룡산",
        "무등산",
        "내장산",
        "속리산",
        "주왕산",
    ]
    for mountain in known_names:
        if mountain in joined:
            return mountain

    if any(keyword in joined for keyword in ["도봉", "우이", "송추", "오봉"]):
        return "북한산"
    if any(keyword in joined for keyword in ["권금성", "소공원", "비선대", "대청봉", "울산바위"]):
        return "설악산"
    if any(keyword in joined for keyword in ["백무동", "중산리", "세석", "연하천"]):
        return "지리산"
    if any(keyword in joined for keyword in ["갑사", "동학사", "신원사"]):
        return "계룡산"
    if any(keyword in joined for keyword in ["백양", "구암사", "내장사"]):
        return "내장산"
    if any(keyword in joined for keyword in ["월정사", "상원사", "두로령"]):
        return "오대산"
    if any(keyword in joined for keyword in ["하늘재", "부봉", "마패봉"]):
        return "월악산"
    if any(keyword in joined for keyword in ["관매도", "하조도", "홍도", "흑산도"]):
        return "다도해해상"
    if any(keyword in joined for keyword in ["해금강", "거제", "매물도", "한산도"]):
        return "한려해상"

    return "국립공원"


def build_highlights(start, waypoint, end):
    highlights = []
    if start:
        highlights.append(f"출발: {start}")
    if waypoint:
        highlights.append(f"경유: {waypoint}")
    if end:
        highlights.append(f"도착: {end}")
    return highlights[:3] or ["탐방로 구간 데이터"]


def build_segment_nodes(start, waypoint, end):
    nodes = [start]
    if waypoint:
        nodes.extend(part.strip() for part in re.split(r"[,/·>]+", waypoint) if part.strip())
    nodes.append(end)
    return [node for node in nodes if node]


@lru_cache(maxsize=1)
def load_public_service_key():
    for path in (KEY_FILE_PATH, DATA_LINK_FILE_PATH):
        key = _load_public_service_key_from_path(path)
        if key:
            return key
    return ""


def _load_public_service_key_from_path(path):
    if not path.exists():
        return ""

    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""

    general_key = re.search(r"일반\s*인증키\s*[:：]\s*([A-Za-z0-9%+/=_-]{20,})", text)
    if general_key:
        return general_key.group(1).strip()

    candidates = [line.strip() for line in text.splitlines() if line.strip()]
    for candidate in reversed(candidates):
        if len(candidate) >= 20 and " " not in candidate and ":" not in candidate:
            return candidate
    return candidates[-1] if candidates else ""


@lru_cache(maxsize=1)
def load_vworld_api_key():
    env_key = os.environ.get("VWORLD_API_KEY", "").strip()
    if env_key:
        return env_key

    for path in (VWORLD_KEY_FILE_PATH, DATA_LINK_FILE_PATH):
        key = _load_vworld_api_key_from_path(path)
        if key:
            return key
    return ""


def _load_vworld_api_key_from_path(path):
    if not path.exists():
        return ""

    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""

    keyed_patterns = [
        r"VWORLD_API_KEY\s*[:=]\s*([A-Za-z0-9-]{20,})",
        r"VWORLD_KEY\s*[:=]\s*([A-Za-z0-9-]{20,})",
        r"브이월드[^:\n]*키\s*[:=]\s*([A-Za-z0-9-]{20,})",
    ]
    for pattern in keyed_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()

    uuid_like = re.search(
        r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b",
        text,
    )
    return uuid_like.group(0).strip() if uuid_like else ""


@lru_cache(maxsize=1)
def load_kma_api_hub_key():
    env_key = os.environ.get("KMA_API_HUB_KEY", "").strip()
    if env_key:
        return env_key

    for path in (KMA_API_HUB_KEY_FILE_PATH, DATA_LINK_FILE_PATH):
        key = _load_kma_api_hub_key_from_path(path)
        if key:
            return key
    return load_public_service_key()


def _load_kma_api_hub_key_from_path(path):
    if not path.exists():
        return ""

    for encoding in ("utf-8", "utf-8-sig", "cp949", "euc-kr"):
        try:
            text = path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        return ""

    patterns = [
        r"KMA_API_HUB_KEY\s*[:=]\s*([A-Za-z0-9_-]{10,})",
        r"authKey\s*=\s*([A-Za-z0-9_-]{10,})",
        r"산악예보[^:\n]*키\s*[:=]\s*([A-Za-z0-9_-]{10,})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""
