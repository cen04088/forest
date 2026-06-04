"""
OpenStreetMap Overpass API를 통해 등산로 경로(route_geometry) 조회.
VWorld에 데이터가 없는 코스의 경로선 보완에 사용한다.
"""
import logging

import requests
from django.core.cache import cache

logger = logging.getLogger(__name__)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 22  # Overpass 서버 처리 + 네트워크
OSM_CACHE_SECONDS = 86400  # 24시간 캐시 (등산로는 자주 바뀌지 않음)
MAX_POINTS = 80  # 지도 렌더링에 충분한 최대 포인트 수


def _build_query(lat: float, lng: float, radius_m: int) -> str:
    return f"""
[out:json][timeout:20];
(
  way["highway"~"^(path|footway|track)$"]["name"](around:{radius_m},{lat},{lng});
  relation["route"="hiking"](around:{radius_m * 2},{lat},{lng});
);
out geom;
"""


def _simplify(coords: list, max_pts: int = MAX_POINTS) -> list:
    """균등 간격으로 포인트 수를 줄여 용량을 제한한다."""
    if len(coords) <= max_pts:
        return coords
    step = (len(coords) - 1) / (max_pts - 1)
    return [coords[round(i * step)] for i in range(max_pts)]


def _extract_geometry_from_element(element: dict) -> list:
    etype = element.get("type")
    if etype == "way":
        return [
            {"lat": p["lat"], "lng": p["lon"]}
            for p in element.get("geometry", [])
            if "lat" in p and "lon" in p
        ]
    if etype == "relation":
        pts = []
        for member in element.get("members", []):
            if member.get("type") == "way":
                for p in member.get("geometry", []):
                    if "lat" in p and "lon" in p:
                        pts.append({"lat": p["lat"], "lng": p["lon"]})
        return pts
    return []


def fetch_osm_trails(lat: float, lng: float, mountain_name: str = "", radius_m: int = 3000) -> dict:
    """
    좌표 주변 OSM 등산로를 조회해 route_geometry 배열 목록을 반환한다.

    반환 형식:
        {"items": [{"name": str, "route_geometry": [{lat, lng}, ...], "source": "OSM"}, ...]}
    """
    if not lat or not lng:
        return {"items": []}

    cache_key = f"osm_trails:{round(lat, 3)}:{round(lng, 3)}:{radius_m}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": _build_query(lat, lng, radius_m)},
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "OllaHikingApp/1.0 (contact: olla@example.com)"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        logger.warning("Overpass API 오류: %s", exc)
        return {"items": []}

    items = []
    mountain_norm = mountain_name.replace(" ", "").lower() if mountain_name else ""

    for element in data.get("elements", []):
        tags = element.get("tags", {})
        name = tags.get("name:ko") or tags.get("name") or ""

        geometry = _extract_geometry_from_element(element)
        if len(geometry) < 2:
            continue

        geometry = _simplify(geometry)

        # 산 이름 관련성 점수 (이름에 산명 포함 시 가점)
        name_norm = name.replace(" ", "").lower()
        relevance = 2 if (mountain_norm and mountain_norm in name_norm) else 1

        items.append({
            "name": name or f"OSM #{element.get('id', '')}",
            "source": "OSM",
            "osm_id": element.get("id"),
            "highway": tags.get("highway", ""),
            "sac_scale": tags.get("sac_scale", ""),
            "route_geometry": geometry,
            "_relevance": relevance,
            "_length": len(geometry),
        })

    # 관련성 우선, 같으면 경로 길이(포인트 수) 내림차순
    items.sort(key=lambda x: (x["_relevance"], x["_length"]), reverse=True)

    # 내부 정렬용 필드 제거
    for item in items:
        item.pop("_relevance", None)
        item.pop("_length", None)

    result = {"items": items[:15]}
    cache.set(cache_key, result, OSM_CACHE_SECONDS)
    return result
