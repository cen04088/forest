"""국립산림과학원(NIFOS) 산림생태플럭스 관측 데이터 API.

산림생태플럭스시스템(igportal.nifos.go.kr):
- 광릉, 태안, 양양, 가리왕산, 지리산 등 전국 산림 플럭스 관측탑 운영
- 측정 항목: 탄소플럭스(NEE), 잠열(LE), 현열(H), 태양복사(Rg), 기온, 토양온도
- 목적: 산림 탄소흡수원 정량화, 탄소중립 정책 근거 데이터 제공

공공데이터포털 등록 서비스: APIs.data.go.kr/1400377/fluxObsrInfo
"""
import json
import os
import urllib.parse
import urllib.request
from functools import lru_cache

from .loaders import load_public_service_key

# 공공데이터 포털 산림청 산림생태플럭스 관측정보 엔드포인트
FOREST_FLUX_URL = "http://apis.data.go.kr/1400377/fluxObsrInfo/getFluxObsrInfo"

# 주요 플럭스 관측소 위치 (위도/경도 기반 최근접 탐색용)
FLUX_STATIONS = [
    {"code": "KOR-GCK", "name": "광릉", "lat": 37.7383, "lng": 127.1560, "region": "경기 포천"},
    {"code": "KOR-TAN", "name": "태안",  "lat": 36.9689, "lng": 126.1392, "region": "충남 태안"},
    {"code": "KOR-YAN", "name": "양양",  "lat": 38.0899, "lng": 128.6276, "region": "강원 양양"},
    {"code": "KOR-GRW", "name": "가리왕산", "lat": 37.4611, "lng": 128.5697, "region": "강원 정선"},
    {"code": "KOR-JRS", "name": "지리산", "lat": 35.2669, "lng": 127.3740, "region": "경남 함양"},
]


def _load_nifos_key() -> str:
    return os.environ.get("NIFOS_API_KEY", "").strip()


def fetch_forest_flux(mountain_name: str = "", lat: float = None, lng: float = None, timeout: int = 8) -> dict:
    """산림생태플럭스 실시간 관측 데이터 조회.

    산 이름 또는 위경도로 가장 가까운 플럭스 관측소 데이터를 반환합니다.
    NEE(탄소순흡수량), 잠열, 현열, 태양복사 등 산림 생태환경 지표 제공.

    Args:
        mountain_name: 산 이름 (관측소 매칭에 활용)
        lat: 산 위도 (최근접 관측소 탐색)
        lng: 산 경도 (최근접 관측소 탐색)
        timeout: HTTP 타임아웃(초)

    Returns:
        ok=True 시 nee_umol, le_wm2, h_wm2, rg_wm2, temp_c, soil_temp_c 포함
    """
    station = _find_nearest_station(mountain_name, lat, lng)
    service_key = load_public_service_key()
    if not service_key:
        return _fallback(station, "PUBLIC_SERVICE_KEY 미설정")

    return _cached_fetch_flux(station["code"], station["name"], service_key, timeout)


@lru_cache(maxsize=32)
def _cached_fetch_flux(station_code: str, station_name: str, service_key: str, timeout: int) -> dict:
    query = {
        "serviceKey": service_key,
        "stnId": station_code,
        "numOfRows": "1",
        "pageNo": "1",
        "_type": "json",
    }
    url = f"{FOREST_FLUX_URL}?{urllib.parse.urlencode(query, safe='%')}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
        return _parse_flux(body, station_name)
    except Exception as exc:
        return _fallback({"name": station_name, "code": station_code}, f"요청 실패: {str(exc)[:80]}")


def _parse_flux(body: bytes, station_name: str) -> dict:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "source": "forest_flux", "error": "JSON 파싱 오류"}

    items_raw = (
        payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        or payload.get("items")
        or (payload if isinstance(payload, list) else None)
    ) or []
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    if not items_raw:
        return {"ok": False, "source": "forest_flux", "error": "데이터 없음", "station_name": station_name}

    item = items_raw[0]
    nee = _to_float(item.get("nee") or item.get("NEE") or item.get("fc"))
    le  = _to_float(item.get("le") or item.get("LE"))
    h   = _to_float(item.get("h") or item.get("H"))
    rg  = _to_float(item.get("rg") or item.get("Rg") or item.get("sw_in"))
    temp = _to_float(item.get("ta") or item.get("temp") or item.get("air_temp"))
    soil = _to_float(item.get("ts") or item.get("soil_temp") or item.get("ts_5cm"))

    return {
        "ok": True,
        "source": "forest_flux",
        "station_name": item.get("stnNm") or station_name,
        "obs_time": item.get("obsTime") or item.get("date"),
        "nee_umol": nee,           # Net Ecosystem Exchange (μmol CO₂/m²/s) — 음수=흡수
        "le_wm2": le,              # 잠열플럭스 (W/m²)
        "h_wm2": h,                # 현열플럭스 (W/m²)
        "rg_wm2": rg,              # 태양복사 (W/m²)
        "temp_c": temp,            # 기온 (°C)
        "soil_temp_c": soil,       # 토양온도 (°C)
        "carbon_status": _carbon_status(nee),
    }


def _carbon_status(nee: float | None) -> str:
    """NEE 값 기반 산림 탄소 상태 해석."""
    if nee is None:
        return "측정불가"
    if nee < -5:
        return "강한탄소흡수"   # 광합성 활발 (낮, 맑은 날)
    if nee < 0:
        return "탄소흡수"
    if nee < 2:
        return "탄소균형"       # 호흡≈광합성
    return "탄소방출"           # 야간, 흐린 날


def _find_nearest_station(mountain_name: str, lat: float = None, lng: float = None) -> dict:
    """산 이름 또는 위경도로 가장 가까운 플럭스 관측소 탐색."""
    # 산 이름 직접 매칭
    name_lower = (mountain_name or "").lower()
    for s in FLUX_STATIONS:
        if s["name"] in (mountain_name or "") or (mountain_name or "") in s["name"]:
            return s

    # 위경도 기반 최근접 탐색
    if lat is not None and lng is not None:
        best, best_dist = FLUX_STATIONS[0], float("inf")
        for s in FLUX_STATIONS:
            dist = (s["lat"] - lat) ** 2 + (s["lng"] - lng) ** 2
            if dist < best_dist:
                best, best_dist = s, dist
        return best

    # 기본: 광릉 (국내 최장기 운영 플럭스 관측소)
    return FLUX_STATIONS[0]


def _fallback(station: dict, error: str) -> dict:
    return {
        "ok": False,
        "source": "forest_flux",
        "error": error,
        "station_name": station.get("name", ""),
    }


def _to_float(value) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None
