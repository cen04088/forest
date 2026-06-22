import xml.etree.ElementTree as ET

from .coordinates import extract_forest_map_coordinates


FOREST_SPATIAL_SOURCE = "산림청_산림공간정보_등산로정보"


def parse_forest_spatial_xml(body: bytes) -> dict:
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {"ok": False, "error": "Invalid forest spatial XML", "items": [], "total_count": 0}

    result_code = _text(root, ".//resultCode")
    if result_code and result_code not in {"00", "0"}:
        return {
            "ok": False,
            "error": _text(root, ".//resultMsg") or "Forest spatial API returned an error",
            "items": [],
            "total_count": 0,
        }

    items = []
    for item in root.findall(".//item"):
        map_url = _text(item, "mntninfourl")
        coords = extract_forest_map_coordinates(map_url)
        normalized = {
            "mountain": _text(item, "mntnnm"),
            "map_url": map_url,
            "file_url": _text(item, "mntnfile"),
            "image_url": _text(item, "mntnimg"),
        }
        if coords:
            normalized["coordinates"] = coords
            normalized["lat"] = coords["lat"]
            normalized["lng"] = coords["lng"]
        items.append(normalized)

    return {"ok": True, "total_count": _int(_text(root, ".//totalCount"), len(items)), "items": items}


def forest_spatial_items_to_courses(result: dict) -> list[dict]:
    courses = []
    for index, item in enumerate(result.get("items") or [], start=1):
        coords = item.get("coordinates") or {}
        lat = item.get("lat", coords.get("lat"))
        lng = item.get("lng", coords.get("lng"))
        mountain = item.get("mountain") or "Forest trail"
        courses.append(
            {
                "id": f"forest-spatial-{index}-{mountain}",
                "mountain": mountain,
                "name": item.get("name") or f"{mountain} trail",
                "region": item.get("region") or "Forest spatial data",
                "difficulty": item.get("difficulty") or "easy",
                "distance_km": item.get("distance_km") or 1.5,
                "duration_min": item.get("duration_min") or 50,
                "elevation_gain_m": item.get("elevation_gain_m") or 55,
                "lat": lat,
                "lng": lng,
                "crowding": item.get("crowding", 0.3),
                "highlights": item.get("highlights") or ["Forest spatial trail data"],
                "map_url": item.get("map_url", ""),
                "file_url": item.get("file_url", ""),
                "source": FOREST_SPATIAL_SOURCE,
            }
        )
    return courses


def _text(node, path: str) -> str:
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def _int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
