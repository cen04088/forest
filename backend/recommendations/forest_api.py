import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from functools import lru_cache

from .coordinates import extract_forest_map_coordinates
from .loaders import load_public_service_key
from .mountain_coordinates import find_mountain_coordinates


FOREST_SPATIAL_URL = "http://api.forest.go.kr/openapi/service/trailInfoService/getforestspatialdataservice"


def fetch_forest_spatial_data(mountain_name="", page_no=1, num_of_rows=10, timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {
            "ok": False,
            "error": "공공데이터 일반 인증키를 찾을 수 없습니다.",
            "items": [],
        }

    return _cached_fetch_forest_spatial_data(mountain_name.strip(), int(page_no), int(num_of_rows), service_key, timeout)


@lru_cache(maxsize=128)
def _cached_fetch_forest_spatial_data(mountain_name, page_no, num_of_rows, service_key, timeout):
    query = {
        "ServiceKey": service_key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
    }
    if mountain_name:
        query["mntnNm"] = mountain_name

    url = f"{FOREST_SPATIAL_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:
        return {
            "ok": False,
            "error": f"산림공간정보 API 호출에 실패했습니다: {exc}",
            "items": [],
        }

    return parse_forest_spatial_xml(body)


def parse_forest_spatial_xml(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        text = body.decode("utf-8", errors="replace")
        return {
            "ok": False,
            "error": "산림공간정보 API XML 응답을 해석하지 못했습니다.",
            "raw_preview": text[:300],
            "items": [],
        }

    result_code = text_of(root, ".//resultCode")
    result_msg = text_of(root, ".//resultMsg")
    total_count = parse_int(text_of(root, ".//totalCount"))

    items = []
    for item in root.findall(".//item"):
        map_url = text_of(item, "mntninfourl")
        mountain = text_of(item, "mntnnm")
        coordinates = extract_forest_map_coordinates(map_url)
        coordinate_mountain, fallback_coordinates = find_mountain_coordinates(mountain)
        if not coordinates and fallback_coordinates:
            coordinates = {
                "lat": fallback_coordinates["lat"],
                "lng": fallback_coordinates["lng"],
            }
        item_payload = {
            "mountain": coordinate_mountain or mountain,
            "map_url": map_url,
            "file_url": text_of(item, "mntnfile"),
            "image_url": text_of(item, "mntnimg"),
            "coordinates": coordinates,
        }
        if coordinates:
            item_payload["lat"] = coordinates["lat"]
            item_payload["lng"] = coordinates["lng"]
        items.append(item_payload)

    return {
        "ok": result_code in ("00", "0", ""),
        "result_code": result_code,
        "result_msg": result_msg,
        "total_count": total_count,
        "items": items,
    }


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def parse_int(value):
    try:
        return int(value or 0)
    except ValueError:
        return 0


def safe_public_response(result):
    safe = json.loads(json.dumps(result, ensure_ascii=False))
    for item in safe.get("items", []):
        file_url = item.get("file_url") or ""
        if file_url:
            item["has_file"] = True
        item.pop("file_url", None)
    return safe


def forest_spatial_items_to_courses(result):
    courses = []
    for index, item in enumerate(result.get("items", []), start=1):
        coordinates = item.get("coordinates")
        if not coordinates:
            continue

        mountain = item.get("mountain") or "산림공간정보"
        courses.append(
            {
                "id": f"forest-spatial-{index}-{mountain}",
                "mountain": mountain,
                "name": f"{mountain} 산림공간정보 등산로",
                "region": "산림청 산림공간정보",
                "difficulty": "medium",
                "distance_km": 4.0,
                "duration_min": 130,
                "elevation_gain_m": 260,
                "lat": coordinates["lat"],
                "lng": coordinates["lng"],
                "crowding": 0.3,
                "highlights": [
                    "산림공간정보 좌표 연동",
                    "등산로 지도 URL 제공",
                    "현재 위치 기반 거리 계산 가능",
                ],
                "source": "산림청_산림공간정보_등산로정보",
                "map_url": item.get("map_url", ""),
                "image_url": item.get("image_url", ""),
            }
        )
    return courses
