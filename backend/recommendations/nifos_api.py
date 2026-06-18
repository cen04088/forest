"""국립산림과학원(NIFOS) 산악기상 및 산림 미세먼지 관측 데이터 API.

산악기상시스템  : mtweather.nifos.go.kr
미세먼지관측시스템: aican.nifos.go.kr
"""
import json
import os
import urllib.parse
import urllib.request
from functools import lru_cache

NIFOS_MOUNTAIN_WEATHER_URL = "http://mtweather.nifos.go.kr/openapi/obs/current"
NIFOS_FINE_DUST_URL = "http://aican.nifos.go.kr/openapi/dust/current"


def _load_nifos_key() -> str:
    return os.environ.get("NIFOS_API_KEY", "").strip()


# ── 산악기상 ──────────────────────────────────────────────────────────────────

def fetch_nifos_mountain_weather(station_code: str = "", timeout: int = 8) -> dict:
    """NIFOS 산악기상시스템에서 실시간 기상 데이터 조회.

    Args:
        station_code: 관측소 코드 (미입력 시 전체 조회)
        timeout: HTTP 타임아웃(초)

    Returns:
        ok=True 시 temperature_c, wind_speed_ms, precipitation_mm, humidity_pct 포함.
        API 키 미설정 또는 오류 시 ok=False 반환 (호출부가 폴백 처리).
    """
    api_key = _load_nifos_key()
    if not api_key:
        return {"ok": False, "source": "nifos_mountain_weather", "error": "NIFOS_API_KEY 미설정", "items": []}
    return _cached_fetch_nifos_weather(station_code, api_key, timeout)


@lru_cache(maxsize=64)
def _cached_fetch_nifos_weather(station_code: str, api_key: str, timeout: int) -> dict:
    query: dict = {"authKey": api_key, "_type": "json"}
    if station_code:
        query["stnId"] = station_code

    url = f"{NIFOS_MOUNTAIN_WEATHER_URL}?{urllib.parse.urlencode(query)}"
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
