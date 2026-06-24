"""국립산림과학원(NIFOS) 산림생태플럭스 관측 데이터 API.

산림생태플럭스시스템(igportal.nifos.go.kr):
- 광릉, 태안, 양양, 가리왕산, 지리산 등 전국 산림 플럭스 관측탑 운영
- 측정 항목: 탄소플럭스(NEE), 잠열(LE), 현열(H), 태양복사(Rg), 기온, 토양온도
- 목적: 산림 탄소흡수원 정량화, 탄소중립 정책 근거 데이터 제공

공공데이터포털 등록 서비스: apis.data.go.kr/1400377/fluxObsrInfo
"""
import json
import os
import time
import urllib.parse
import urllib.request

from .loaders import load_public_service_key

FOREST_FLUX_URL = "http://apis.data.go.kr/1400377/fluxObsrInfo/getFluxObsrInfo"

# 주요 플럭스 관측소 (위도/경도 기반 최근접 탐색용)
FLUX_STATIONS = [
    {"code": "KOR-GCK", "name": "광릉",    "lat": 37.7383, "lng": 127.1560, "region": "경기 포천"},
    {"code": "KOR-TAN", "name": "태안",    "lat": 36.9689, "lng": 126.1392, "region": "충남 태안"},
    {"code": "KOR-YAN", "name": "양양",    "lat": 38.0899, "lng": 128.6276, "region": "강원 양양"},
    {"code": "KOR-GRW", "name": "가리왕산", "lat": 37.4611, "lng": 128.5697, "region": "강원 정선"},
    {"code": "KOR-JRS", "name": "지리산",  "lat": 35.2669, "lng": 127.3740, "region": "경남 함양"},
]

_TTL = 1800  # 30분 캐시
_cache: dict = {}  # {station_code: (timestamp, result)}


def fetch_forest_flux(mountain_name: str = "", lat: float = None, lng: float = None, timeout: int = 4) -> dict:
    """산림생태플럭스 실시간 관측 데이터 조회 (30분 TTL 캐시).

    산 이름 또는 위경도로 가장 가까운 플럭스 관측소 데이터를 반환합니다.
    NEE, LE, H, Rg, 기온, 토양온도에서 UV·불쾌지수·탄소발자국 지표를 추가 계산합니다.
    """
    station = _find_nearest_station(mountain_name, lat, lng)
    service_key = load_public_service_key()
    if not service_key:
        return _fallback(station, "PUBLIC_SERVICE_KEY 미설정")
    return _fetch_with_ttl(station, service_key, timeout)


def _fetch_with_ttl(station: dict, service_key: str, timeout: int) -> dict:
    code = station["code"]
    now = time.time()
    if code in _cache:
        ts, cached = _cache[code]
        if now - ts < _TTL:
            return cached
    result = _call_api(station, service_key, timeout)
    _cache[code] = (now, result)
    return result


def _call_api(station: dict, service_key: str, timeout: int) -> dict:
    query = {
        "serviceKey": service_key,
        "stnId": station["code"],
        "numOfRows": "1",
        "pageNo": "1",
        "_type": "json",
    }
    url = f"{FOREST_FLUX_URL}?{urllib.parse.urlencode(query, safe='%')}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
        return _parse_flux(body, station["name"])
    except Exception as exc:
        return _fallback(station, f"요청 실패: {str(exc)[:80]}")


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
    nee      = _f(item.get("nee")  or item.get("NEE")    or item.get("fc"))
    le       = _f(item.get("le")   or item.get("LE"))
    h        = _f(item.get("h")    or item.get("H"))
    rg       = _f(item.get("rg")   or item.get("Rg")     or item.get("sw_in"))
    temp     = _f(item.get("ta")   or item.get("temp")   or item.get("air_temp"))
    soil     = _f(item.get("ts")   or item.get("soil_temp") or item.get("ts_5cm"))

    derived = _derive_indicators(nee, le, h, rg, temp, soil)

    return {
        "ok": True,
        "source": "forest_flux",
        "station_name": item.get("stnNm") or station_name,
        "obs_time": item.get("obsTime") or item.get("date"),
        # 원시 측정값
        "nee_umol": nee,
        "le_wm2": le,
        "h_wm2": h,
        "rg_wm2": rg,
        "temp_c": temp,
        "soil_temp_c": soil,
        # 탄소 상태
        "carbon_status": _carbon_status(nee),
        # 도출 지표 (1순위 개선)
        **derived,
    }


# ── 지표 도출 ────────────────────────────────────────────────────────────────

def _derive_indicators(nee, le, h, rg, temp, soil) -> dict:
    out = {}

    # ① 자외선 위험도 — 태양복사(Rg) → UV Index 근사
    if rg is not None:
        uv = round(rg / 230, 1)
        out["uv_index"] = uv
        out["uv_risk"] = (
            "극단적" if uv >= 11 else
            "매우높음" if uv >= 8 else
            "높음"    if uv >= 6 else
            "보통"    if uv >= 3 else
            "낮음"
        )
        out["uv_advice"] = (
            "외출 자제 권고 수준 — 자외선 차단제 SPF50+ 필수, 모자·긴 소매 착용" if uv >= 8 else
            "자외선 주의 — 차단제·모자 착용 권장" if uv >= 6 else
            "보통 수준 — 차단제 권장" if uv >= 3 else
            "자외선 낮음"
        )

    # ② 산림 습윤도 — Bowen 비율(H/LE)로 산림 건조·습윤 상태 판단
    if le is not None and h is not None and le > 0:
        bowen = h / le
        out["bowen_ratio"] = round(bowen, 2)
        out["humidity_level"] = (
            "높음(습윤)" if bowen < 0.3 else
            "보통"       if bowen < 0.8 else
            "낮음(건조)"
        )

    # ③ 불쾌지수 — 기온 + 잠열/현열 기반 상대습도 추정
    if temp is not None and le is not None and h is not None:
        total = le + h
        ef = (le / total) if total > 0 else 0.5
        rh_est = min(95, max(20, ef * 100 + 30))
        out["rh_estimate_pct"] = round(rh_est)
        di = 0.81 * temp + 0.01 * rh_est * (0.99 * temp - 14.99) + 46.3
        out["discomfort_index"] = round(di, 1)
        out["discomfort_label"] = (
            "매우불쾌" if di >= 80 else
            "불쾌"     if di >= 75 else
            "약간불쾌" if di >= 68 else
            "쾌적"
        )

    # ④ 토양 건조도 — 토양온도와 기온 차이로 추정
    if soil is not None and temp is not None:
        diff = soil - temp
        out["soil_status"] = (
            "건조" if diff > 5 else
            "보통" if diff > 1 else
            "습윤"
        )
        out["soil_temp_diff"] = round(diff, 1)

    # ⑤ 탄소 발자국 교육 메시지
    if nee is not None and nee < 0:
        # μmol CO₂/m²/s → gCO₂/ha/h
        g_per_ha_h = round(abs(nee) * 44e-6 * 10_000 * 3600)
        out["carbon_absorption_g_ha_h"] = g_per_ha_h
        hiker_co2_g = 250  # 등산 시 1인 호흡 약 250 g CO₂/h
        ha_to_offset = round(hiker_co2_g / g_per_ha_h, 1) if g_per_ha_h > 0 else None
        out["carbon_footprint_msg"] = (
            f"지금 이 산림 1ha가 시간당 약 {g_per_ha_h}g의 CO₂를 흡수하고 있습니다. "
            f"등산객 1인의 호흡(약 {hiker_co2_g}g/h)을 상쇄하려면 "
            f"{ha_to_offset}ha의 산림이 필요합니다."
        ) if ha_to_offset else None

    return out


def _carbon_status(nee) -> str:
    if nee is None:   return "측정불가"
    if nee < -5:      return "강한탄소흡수"
    if nee < 0:       return "탄소흡수"
    if nee < 2:       return "탄소균형"
    return "탄소방출"


# ── 관측소 탐색 ──────────────────────────────────────────────────────────────

def _find_nearest_station(mountain_name: str, lat=None, lng=None) -> dict:
    for s in FLUX_STATIONS:
        if s["name"] in (mountain_name or "") or (mountain_name or "") in s["name"]:
            return s
    if lat is not None and lng is not None:
        best, best_dist = FLUX_STATIONS[0], float("inf")
        for s in FLUX_STATIONS:
            dist = (s["lat"] - lat) ** 2 + (s["lng"] - lng) ** 2
            if dist < best_dist:
                best, best_dist = s, dist
        return best
    return FLUX_STATIONS[0]


def _fallback(station: dict, error: str) -> dict:
    return {"ok": False, "source": "forest_flux", "error": error,
            "station_name": station.get("name", "")}


def _f(value) -> float | None:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def warm_flux_cache() -> None:
    """서버 시작 시 5개 관측소 데이터를 백그라운드로 미리 조회."""
    import threading
    service_key = load_public_service_key()
    if not service_key:
        return
    def _warm():
        for station in FLUX_STATIONS:
            try:
                _fetch_with_ttl(station, service_key, timeout=4)
            except Exception:
                pass
    threading.Thread(target=_warm, daemon=True).start()
