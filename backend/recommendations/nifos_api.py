"""국립산림과학원(NIFOS) 산악기상정보 및 산림 미세먼지 관측 데이터 API.

산악기상정보(공공데이터포털): http://apis.data.go.kr/1400377/mtweather/mountListSearch
미세먼지관측시스템: aican.nifos.go.kr
"""
import json
import os
import urllib.parse
import urllib.request
from functools import lru_cache

from .loaders import load_public_service_key

# 공공데이터 포털 등록 엔드포인트 (산림청 국립산림과학원_산악기상정보)
NIFOS_MOUNTAIN_WEATHER_URL = "http://apis.data.go.kr/1400377/mtweather/mountListSearch"

NIFOS_FINE_DUST_URL = "http://aican.nifos.go.kr/openapi/dust/current"


def _load_nifos_key() -> str:
    return os.environ.get("NIFOS_API_KEY", "").strip()


# ── 산악기상 (공공데이터 포털) ─────────────────────────────────────────────────

def fetch_nifos_mountain_weather(mountain_name: str = "", timeout: int = 8) -> dict:
    """산림청 국립산림과학원_산악기상정보 API 조회.

    공공데이터포털(apis.data.go.kr/1400377/mtweather) 등록 서비스.
    PUBLIC_SERVICE_KEY 사용 — 별도 키 불필요 (신청 승인 후 활성화).

    Args:
        mountain_name: 산 이름 필터 (미입력 시 전체 목록)
        timeout: HTTP 타임아웃(초)
    """
    service_key = load_public_service_key()
    if not service_key:
        return {"ok": False, "source": "nifos_mountain_weather", "error": "PUBLIC_SERVICE_KEY 미설정", "items": []}
    return _cached_fetch_nifos_weather(mountain_name.strip(), service_key, timeout)


@lru_cache(maxsize=64)
def _cached_fetch_nifos_weather(mountain_name: str, service_key: str, timeout: int) -> dict:
    query: dict = {
        "serviceKey": service_key,
        "numOfRows": "10",
        "pageNo": "1",
        "_type": "json",
    }
    if mountain_name:
        query["mntnNm"] = mountain_name

    url = f"{NIFOS_MOUNTAIN_WEATHER_URL}?{urllib.parse.urlencode(query, safe='%')}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
    except Exception as exc:
        return {
            "ok": False,
            "source": "nifos_mountain_weather",
            "error": f"요청 실패: {str(exc)[:100]}",
            "items": [],
        }
    return _parse_nifos_weather(body)


def _parse_nifos_weather(body: bytes) -> dict:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "source": "nifos_mountain_weather", "error": "JSON 파싱 오류", "items": []}

    items_raw = (
        payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        or payload.get("items")
        or (payload if isinstance(payload, list) else None)
    ) or []
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    items = [_normalize_weather_item(item) for item in items_raw if isinstance(item, dict)]
    if not items:
        return {"ok": False, "source": "nifos_mountain_weather", "error": "데이터 없음", "items": []}

    first = items[0]
    return {
        "ok": True,
        "source": "nifos_mountain_weather",
        "station_name": first.get("station_name"),
        "obs_time": first.get("obs_time"),
        "temperature_c": first.get("temperature_c"),
        "precipitation_mm": first.get("precipitation_mm"),
        "wind_speed_ms": first.get("wind_speed_ms"),
        "humidity_pct": first.get("humidity_pct"),
        "snow_depth_cm": first.get("snow_depth_cm"),
        "altitude_m": first.get("altitude_m"),
        "items": items,
    }


def _normalize_weather_item(item: dict) -> dict:
    return {
        "station_id": item.get("stnId") or item.get("station_id", ""),
        "station_name": item.get("stnNm") or item.get("station_name", ""),
        "obs_time": item.get("obsTime") or item.get("obs_time", ""),
        "temperature_c": _to_float(item.get("ta") or item.get("temperature_c")),
        "precipitation_mm": _to_float(item.get("rn") or item.get("precipitation_mm")),
        "wind_speed_ms": _to_float(item.get("ws") or item.get("wind_speed_ms")),
        "humidity_pct": _to_float(item.get("hm") or item.get("humidity_pct")),
        "snow_depth_cm": _to_float(item.get("sd") or item.get("snow_depth_cm")),
        "altitude_m": _to_int(item.get("stnHt") or item.get("altitude_m")),
    }


# ── 산림 미세먼지 ─────────────────────────────────────────────────────────────

def fetch_nifos_fine_dust(station_code: str = "", timeout: int = 8) -> dict:
    """NIFOS 산림 미세먼지 관측시스템에서 PM10·PM2.5 데이터 조회.

    Args:
        station_code: 관측소 코드 (미입력 시 전체 조회)
        timeout: HTTP 타임아웃(초)

    Returns:
        ok=True 시 pm10_ugm3, pm25_ugm3, grade_pm10, grade_pm25 포함.
    """
    api_key = _load_nifos_key()
    if not api_key:
        return {"ok": False, "source": "nifos_fine_dust", "error": "NIFOS_API_KEY 미설정", "items": []}
    return _cached_fetch_nifos_dust(station_code, api_key, timeout)


@lru_cache(maxsize=64)
def _cached_fetch_nifos_dust(station_code: str, api_key: str, timeout: int) -> dict:
    query: dict = {"authKey": api_key, "_type": "json"}
    if station_code:
        query["stnId"] = station_code

    url = f"{NIFOS_FINE_DUST_URL}?{urllib.parse.urlencode(query)}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
    except Exception as exc:
        return {
            "ok": False,
            "source": "nifos_fine_dust",
            "error": f"요청 실패: {str(exc)[:100]}",
            "items": [],
        }
    return _parse_nifos_dust(body)


def _parse_nifos_dust(body: bytes) -> dict:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "source": "nifos_fine_dust", "error": "JSON 파싱 오류", "items": []}

    items_raw = (
        payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        or payload.get("items")
        or (payload if isinstance(payload, list) else None)
    ) or []
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    items = [_normalize_dust_item(item) for item in items_raw if isinstance(item, dict)]
    if not items:
        return {"ok": False, "source": "nifos_fine_dust", "error": "데이터 없음", "items": []}

    first = items[0]
    return {
        "ok": True,
        "source": "nifos_fine_dust",
        "station_name": first.get("station_name"),
        "obs_time": first.get("obs_time"),
        "pm10_ugm3": first.get("pm10_ugm3"),
        "pm25_ugm3": first.get("pm25_ugm3"),
        "grade_pm10": first.get("grade_pm10"),
        "grade_pm25": first.get("grade_pm25"),
        "items": items,
    }


def _normalize_dust_item(item: dict) -> dict:
    pm10 = _to_float(item.get("pm10") or item.get("PM10") or item.get("pm10_ugm3"))
    pm25 = _to_float(
        item.get("pm25") or item.get("PM25") or item.get("pm2p5") or item.get("pm25_ugm3")
    )
    return {
        "station_id": item.get("stnId") or item.get("station_id", ""),
        "station_name": item.get("stnNm") or item.get("station_name", ""),
        "obs_time": item.get("obsTime") or item.get("obs_time", ""),
        "pm10_ugm3": pm10,
        "pm25_ugm3": pm25,
        "grade_pm10": _dust_grade(pm10, "pm10"),
        "grade_pm25": _dust_grade(pm25, "pm25"),
    }


def _dust_grade(value: float | None, dust_type: str) -> str:
    if value is None:
        return "알수없음"
    if dust_type == "pm25":
        if value <= 15:
            return "좋음"
        if value <= 35:
            return "보통"
        if value <= 75:
            return "나쁨"
        return "매우나쁨"
    # pm10
    if value <= 30:
        return "좋음"
    if value <= 80:
        return "보통"
    if value <= 150:
        return "나쁨"
    return "매우나쁨"


def _to_float(value) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def _to_int(value) -> int | None:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError, AttributeError):
        return None
