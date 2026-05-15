import csv
import re
from functools import lru_cache
from pathlib import Path

from django.conf import settings

from .data import COURSES
from .mountain_coordinates import find_mountain_coordinates


TRAIL_CSV_PATH = settings.BASE_DIR.parent / "국립공원공단_탐방로_20240911.csv"
KEY_FILE_PATH = settings.BASE_DIR.parent / "key.txt"
DATA_LINK_FILE_PATH = settings.BASE_DIR.parent / "data" / "데이터 링크.txt"


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
    courses = []
    seen_keys = set()
    with Path(path).open(encoding=encoding, newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for index, row in enumerate(reader, start=1):
            course = normalize_trail_row(index, row)
            if course and course["dedupe_key"] not in seen_keys:
                seen_keys.add(course["dedupe_key"])
                course.pop("dedupe_key")
                courses.append(course)

    return courses or COURSES


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
        "dedupe_key": dedupe_key,
    }


def clean_text(value):
    return (value or "").strip()


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
