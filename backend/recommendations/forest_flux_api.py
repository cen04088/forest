"""산행 환경 지수 모듈.

실시간 데이터 조합:
- 기상청 초단기실황 → 기온(T1H), 습도(REH) → 불쾌지수 실측
- 에어코리아 대기질  → PM2.5, PM10 실측
- 산불위험 API      → 산불 위험도 실측
- UV               → 기온·강수·월 기반 추정 (UV OpenAPI 미인증 시 대체)
- 탄소 상태        → NIFOS 계절 대표값 (실측 API 없음)
"""
import datetime

FLUX_STATIONS = [
    {"name": "광릉",    "lat": 37.7383, "lng": 127.1560},
    {"name": "태안",    "lat": 36.9689, "lng": 126.1392},
    {"name": "양양",    "lat": 38.0899, "lng": 128.6276},
    {"name": "가리왕산", "lat": 37.4611, "lng": 128.5697},
    {"name": "지리산",  "lat": 35.2669, "lng": 127.3740},
]


def fetch_forest_flux(
    mountain_name: str = "",
    lat: float = None,
    lng: float = None,
    weather: dict = None,
    air_quality: dict = None,
    wildfire: dict = None,
    **_,
) -> dict:
    """실시간 산행 환경 지수 반환.

    weather / air_quality / wildfire 딕셔너리를 받아 지표를 계산.
    없으면 계절 대표값으로 폴백.
    """
    station = _find_nearest_station(mountain_name, lat, lng)
    w = weather or {}
    aq = air_quality or {}
    wf = wildfire or {}

    result: dict = {
        "ok": True,
        "source": "realtime",
        "station_name": station["name"],
    }

    # ① 불쾌지수 — 실제 기온 + 실제 습도
    temp = _f(w.get("temperature_c"))
    humidity = _f(w.get("humidity_pct"))
    rainfall = _f(w.get("rainfall_mm")) or 0.0
    precip = w.get("precipitation_type", "없음") or "없음"

    if temp is not None:
        result["temp_c"] = temp
    if humidity is not None:
        result["humidity_pct"] = humidity

    if temp is not None and humidity is not None:
        di = 0.81 * temp + 0.01 * humidity * (0.99 * temp - 14.99) + 46.3
        result["discomfort_index"] = round(di, 1)
        result["discomfort_label"] = (
            "매우불쾌" if di >= 80 else
            "불쾌"     if di >= 75 else
            "약간불쾌" if di >= 68 else
            "쾌적"
        )
    else:
        # 폴백: 계절 기온으로 추정
        result.update(_seasonal_discomfort())

    # ② UV 지수 추정 — 강수/구름 여부 + 월
    uv = _estimate_uv(temp, rainfall, precip)
    result["uv_index"] = uv
    result["uv_risk"] = (
        "극단적" if uv >= 11 else
        "매우높음" if uv >= 8 else
        "높음"    if uv >= 6 else
        "보통"    if uv >= 3 else
        "낮음"
    )
    result["uv_advice"] = (
        "외출 자제 권고 수준 — 자외선 차단제 SPF50+ 필수, 모자·긴 소매 착용" if uv >= 8 else
        "자외선 주의 — 차단제·모자 착용 권장" if uv >= 6 else
        "보통 수준 — 차단제 권장" if uv >= 3 else
        "자외선 낮음"
    )

    # ③ 대기질 — 에어코리아 실측
    if aq.get("ok") and aq.get("pm25_ugm3") is not None:
        result["pm25_ugm3"] = aq["pm25_ugm3"]
        result["pm10_ugm3"] = aq.get("pm10_ugm3")
        result["grade_pm25"] = aq.get("grade_pm25", "알수없음")
        result["grade_pm10"] = aq.get("grade_pm10", "알수없음")
        result["aq_station"] = aq.get("station_name", "")

    # ④ 산불 위험도
    wf_risk = wf.get("risk", "low") or "low"
    result["wildfire_risk"] = wf_risk
    result["wildfire_index"] = wf.get("max_index")
    result["wildfire_label"] = {
        "very_high": "매우높음",
        "high": "높음",
        "medium": "보통",
        "low": "낮음",
    }.get(wf_risk, "알수없음")

    # ⑤ 탄소 상태 — NIFOS 논문 계절 대표값 (실측 API 없음)
    result["carbon_status"] = _seasonal_carbon_status()
    result["carbon_source"] = "seasonal"

    return result


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _estimate_uv(temp, rainfall, precip) -> float:
    """기온·강수·현재 월 기반 UV 지수 추정."""
    month = datetime.datetime.now().month
    # 계절 기본 UV (청명한 날 정오 기준)
    base = {1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 8,
            7: 9, 8: 9, 9: 6, 10: 4, 11: 3, 12: 2}.get(month, 4)
    # 강수/흐림이면 감소
    if rainfall and rainfall > 0:
        base = max(1, base - 5)
    elif precip and precip not in ("없음", ""):
        base = max(1, base - 4)
    return float(base)


def _seasonal_discomfort() -> dict:
    month = datetime.datetime.now().month
    if 6 <= month <= 8:
        temp, rh = 26, 75
    elif 3 <= month <= 5 or 9 <= month <= 11:
        temp, rh = 16, 60
    else:
        temp, rh = 3, 55
    di = 0.81 * temp + 0.01 * rh * (0.99 * temp - 14.99) + 46.3
    return {
        "discomfort_index": round(di, 1),
        "discomfort_label": (
            "매우불쾌" if di >= 80 else
            "불쾌"     if di >= 75 else
            "약간불쾌" if di >= 68 else
            "쾌적"
        ),
    }


def _seasonal_carbon_status() -> str:
    month = datetime.datetime.now().month
    if 3 <= month <= 5:   return "탄소흡수"
    if 6 <= month <= 8:   return "강한탄소흡수"
    if 9 <= month <= 11:  return "탄소흡수"
    return "탄소균형"


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


def _f(v) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError, AttributeError):
        return None


def warm_flux_cache() -> None:
    pass
