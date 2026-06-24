"""산림 생태 환경 지표 모듈.

실시간 플럭스 OpenAPI는 존재하지 않음.
- data.go.kr/data/15042678 : 파일데이터(CSV) 전용 — 실시간 불가
- igportal.nifos.go.kr    : 웹 뷰어만 제공, API 없음

현재 전략: NIFOS 연구 논문 기반 계절별 대표값을 사용하여
탄소흡수, UV, 불쾌지수, 습윤도, 토양 상태 지표를 제공.
"""
import datetime

# 주요 플럭스 관측소 (위도/경도 기반 최근접 탐색용)
FLUX_STATIONS = [
    {"name": "광릉",    "lat": 37.7383, "lng": 127.1560, "region": "경기 포천"},
    {"name": "태안",    "lat": 36.9689, "lng": 126.1392, "region": "충남 태안"},
    {"name": "양양",    "lat": 38.0899, "lng": 128.6276, "region": "강원 양양"},
    {"name": "가리왕산", "lat": 37.4611, "lng": 128.5697, "region": "강원 정선"},
    {"name": "지리산",  "lat": 35.2669, "lng": 127.3740, "region": "경남 함양"},
]


def fetch_forest_flux(mountain_name: str = "", lat: float = None, lng: float = None, **_) -> dict:
    """계절별 산림 생태 지표 반환.

    NIFOS 광릉 활엽수림 장기관측 논문 기반 계절 대표값 사용.
    가장 가까운 관측소를 선택해 지역명을 표시.
    """
    station = _find_nearest_station(mountain_name, lat, lng)
    return _seasonal_data(station)


def _seasonal_data(station: dict) -> dict:
    month = datetime.datetime.now().month

    # NIFOS 광릉 활엽수림 장기관측 계절 대표값
    if 3 <= month <= 5:      # 봄
        nee, le, h, rg, temp, soil = -3.2, 110, 55, 320, 14, 11
    elif 6 <= month <= 8:    # 여름
        nee, le, h, rg, temp, soil = -5.8, 185, 60, 410, 24, 21
    elif 9 <= month <= 11:   # 가을
        nee, le, h, rg, temp, soil = -2.1, 80, 65, 260, 15, 13
    else:                    # 겨울
        nee, le, h, rg, temp, soil = 0.4, 20, 45, 150, 2, 1

    derived = _derive_indicators(nee, le, h, rg, temp, soil)
    return {
        "ok": True,
        "source": "forest_flux_seasonal",
        "station_name": station["name"],
        "nee_umol": nee, "le_wm2": le, "h_wm2": h,
        "rg_wm2": rg, "temp_c": temp, "soil_temp_c": soil,
        "carbon_status": _carbon_status(nee),
        **derived,
    }


def _derive_indicators(nee, le, h, rg, temp, soil) -> dict:
    out = {}

    # ① 자외선 — 태양복사(Rg) → UV Index 근사
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

    # ② 습윤도 — Bowen 비율(H/LE)
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

    # ④ 토양 건조도
    if soil is not None and temp is not None:
        diff = soil - temp
        out["soil_status"] = (
            "건조" if diff > 5 else
            "보통" if diff > 1 else
            "습윤"
        )
        out["soil_temp_diff"] = round(diff, 1)

    # ⑤ 탄소 발자국 메시지
    if nee is not None and nee < 0:
        g_per_ha_h = round(abs(nee) * 44e-6 * 10_000 * 3600)
        out["carbon_absorption_g_ha_h"] = g_per_ha_h
        hiker_co2_g = 250
        ha_to_offset = round(hiker_co2_g / g_per_ha_h, 1) if g_per_ha_h > 0 else None
        out["carbon_footprint_msg"] = (
            f"지금 이 산림 1ha가 시간당 약 {g_per_ha_h}g의 CO₂를 흡수하고 있습니다. "
            f"등산객 1인의 호흡(약 {hiker_co2_g}g/h)을 상쇄하려면 "
            f"{ha_to_offset}ha의 산림이 필요합니다."
        ) if ha_to_offset else None

    return out


def _carbon_status(nee) -> str:
    if nee is None:  return "측정불가"
    if nee < -5:     return "강한탄소흡수"
    if nee < 0:      return "탄소흡수"
    if nee < 2:      return "탄소균형"
    return "탄소방출"


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


def warm_flux_cache() -> None:
    """하위 호환성 유지용 — 실제로 아무것도 하지 않음 (캐시 불필요)."""
    pass
