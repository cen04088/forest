import math
from datetime import datetime
from .mountain_data import MOUNTAINS
from .mountain_identity import with_mountain_identity
from .accident_model import predict_accident_risk
from .landslide_api import fetch_landslide_prediction


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def _parse_hhmm(s):
    """'HH:MM' → 분 단위 정수. 파싱 실패 시 None."""
    if not s:
        return None
    try:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


# ── 개별 점수 함수 ────────────────────────────────────────────────────────────


def _duration_score(mountain, desired_min):
    lo, hi = mountain["walk_time_min"], mountain["walk_time_max"]
    if lo <= desired_min <= hi:
        return 1.0
    if desired_min < lo:
        return max(0.0, 1.0 - (lo - desired_min) / 120)
    return max(0.0, 1.0 - (desired_min - hi) / 180)



def _distance_score(mountain, user_lat, user_lng):
    if user_lat is None or user_lng is None:
        return 0.5
    d = _haversine(user_lat, user_lng, mountain["lat"], mountain["lng"])
    if d <= 30:
        return 1.0
    if d <= 80:
        return 0.85
    if d <= 150:
        return 0.65
    if d <= 300:
        return 0.4
    return 0.2


def _weather_score(weather):
    """날씨 + 대기질 통합 점수 (0.0~1.0)."""
    if not weather:
        return 0.7
    score = 1.0
    rainfall = float(weather.get("rainfall_mm", 0) or 0)
    wind = float(weather.get("wind_speed_ms", 0) or 0)
    temp = float(weather.get("temperature_c", 15) or 15)
    humidity = float(weather.get("humidity_pct", 50) or 50)
    wildfire = weather.get("wildfire_risk", "low") or "low"

    # 강수
    if rainfall >= 20:
        score -= 0.6
    elif rainfall >= 10:
        score -= 0.4
    elif rainfall > 0:
        score -= 0.15

    # 풍속
    if wind >= 12:
        score -= 0.35
    elif wind >= 8:
        score -= 0.2
    elif wind >= 5:
        score -= 0.1

    # 기온
    if temp <= -5 or temp >= 38:
        score -= 0.3
    elif temp <= 0 or temp >= 35:
        score -= 0.15

    # 불쾌지수 (기온+습도 복합 열스트레스 — 기존 단순 습도 페널티 대체)
    if temp >= 25 and humidity >= 60:
        di = 0.81 * temp + 0.01 * humidity * (0.99 * temp - 14.99) + 46.3
        if di >= 80:
            score -= 0.12   # 매우불쾌 — 열사병 위험
        elif di >= 75:
            score -= 0.06   # 불쾌
        elif di >= 68:
            score -= 0.02   # 약간불쾌

    # 대기질 PM2.5 (에어코리아 실측 연계 — 없으면 무시)
    pm25 = float(weather.get("pm25_ugm3") or 0)
    if pm25 >= 75:
        score -= 0.18   # 매우나쁨
    elif pm25 >= 35:
        score -= 0.09   # 나쁨
    elif pm25 >= 15:
        score -= 0.04   # 보통

    # 산불 위험
    wildfire_pen = {"low": 0.0, "medium": 0.1, "high": 0.25, "very_high": 0.45}.get(wildfire, 0.0)
    score -= wildfire_pen

    return max(0.0, score)


def _sunset_score(mountain, departure_time_str, sun_times):
    """
    일몰 전에 하산 가능한지 평가.
    반환값: (score 0.0~1.0, margin_min: 일몰까지 여유분 or None)
    - 여유 > 60분: 1.0
    - 여유 30~60분: 0.75
    - 여유 0~30분: 0.5  (아슬아슬)
    - 여유 -60~0분: 0.2  (일몰 후 하산)
    - 여유 < -60분: 0.0  (심각)
    """
    sunset_str = (sun_times or {}).get("sunset")
    sunset_min = _parse_hhmm(sunset_str)
    if sunset_min is None:
        return 0.7, None  # 데이터 없으면 중립

    dep_min = _parse_hhmm(departure_time_str)
    if dep_min is None:
        # 출발 시각 없으면 현재 시각 사용
        now = datetime.now()
        dep_min = now.hour * 60 + now.minute

    # 산행 최대 소요 시간 기준으로 하산 완료 시각 추정
    walk_max = mountain.get("walk_time_max", 180)
    finish_min = dep_min + walk_max

    margin = sunset_min - finish_min  # 양수: 일몰 전, 음수: 일몰 후

    if margin > 90:
        score = 1.0
    elif margin > 60:
        score = 0.9
    elif margin > 30:
        score = 0.75
    elif margin > 0:
        score = 0.5
    elif margin > -60:
        score = 0.2
    else:
        score = 0.0

    return score, margin


def _season_score(mountain):
    """
    계절별 패널티.
    - 겨울(12, 1, 2)에 해발 1000m 이상 고산: 감점
    - 여름(6, 7, 8)에 해발 1500m 이상: 오히려 선호 (더위 회피)
    """
    month = datetime.now().month
    elev = mountain.get("elevation_m", 500) or 500
    score = 1.0

    if month in (12, 1, 2):
        if elev >= 1500:
            score -= 0.25
        elif elev >= 1000:
            score -= 0.1
    elif month in (6, 7, 8):
        if elev >= 1000:
            score += 0.05  # 여름엔 고산 약간 선호

    return min(1.0, max(0.0, score))


# ── 산사태 위험 ──────────────────────────────────────────────────────────────────


def _build_landslide_risk_map():
    """현재 산사태 예보를 시군구→위험도 맵으로 반환. 실패하면 빈 딕셔너리."""
    try:
        result = fetch_landslide_prediction(sgg="", page_no=1, num_of_rows=100, timeout=3)
        risk_map = {}
        for item in result.get("items", []):
            sigungu = (item.get("sigungu") or "").strip()
            risk = item.get("risk", "low")
            if sigungu and risk != "low":
                existing = risk_map.get(sigungu, "low")
                if risk == "danger" or existing == "low":
                    risk_map[sigungu] = risk
        return risk_map
    except Exception:
        return {}


def _landslide_multiplier(mountain, risk_map):
    """산의 지역이 산사태 경보/주의 지역과 겹치면 감점 배수 반환."""
    region = mountain.get("region") or ""
    for sigungu, risk in risk_map.items():
        if sigungu and sigungu in region:
            return 0.3 if risk == "danger" else 0.7
    return 1.0


# ── 메인 추천 함수 ─────────────────────────────────────────────────────────────

# 가중치 합계 = 1.0 (ML 제거 후 비례 재배분)
WEIGHTS = {
    "duration":  0.27,
    "sunset":    0.21,
    "distance":  0.20,
    "weather":   0.26,
    "season":    0.06,
}


def recommend_mountains(payload):
    profile = payload.get("profile", {})
    loc = payload.get("location") or {}
    user_lat = float(loc["lat"]) if loc.get("lat") else None
    user_lng = float(loc["lng"]) if loc.get("lng") else None

    desired_min = int(profile.get("desiredHikingMinutes", 180))
    difficulty_filter = profile.get("difficultyFilter", "all")
    departure_time = profile.get("departureTime", "")
    weather = payload.get("weather")
    sun_times = payload.get("sun_times") or {}

    w_weather = _weather_score(weather)

    # 산사태 예보 (한 번만 조회)
    landslide_risk_map = _build_landslide_risk_map()

    # ML 위험 예측: 출발 시각 기반 (없으면 현재 시각)
    dep_hhmm = departure_time or ""
    try:
        dep_hour = int(dep_hhmm.split(":")[0]) if dep_hhmm else datetime.now().hour
    except Exception:
        dep_hour = datetime.now().hour
    now = datetime.now()
    ml_risk = predict_accident_risk(month=now.month, hour=dep_hour, weekday=now.weekday())

    results = []
    for m in MOUNTAINS:
        # 난이도 하드 필터
        if difficulty_filter != "all" and m["difficulty"] != difficulty_filter:
            continue

        t_score = _duration_score(m, desired_min)
        dist_score = _distance_score(m, user_lat, user_lng)
        sun_score, margin_min = _sunset_score(m, departure_time, sun_times)
        season_score = _season_score(m)
        ls_mult = _landslide_multiplier(m, landslide_risk_map)

        # 산사태 위험 지역 식별
        landslide_risk = "low"
        for sg, r in landslide_risk_map.items():
            if sg and sg in (m.get("region") or ""):
                landslide_risk = r
                break

        base = (
            t_score      * WEIGHTS["duration"]
            + sun_score  * WEIGHTS["sunset"]
            + dist_score * WEIGHTS["distance"]
            + w_weather  * WEIGHTS["weather"]
            + season_score * WEIGHTS["season"]
        )
        # 산사태 경보(0.3) / 주의(0.7): 곱셈 패널티 유지
        total = base * ls_mult

        safety_score = round(total * 100)

        # 산사태 경보 지역은 점수 무관 비추천 강제
        if landslide_risk == "danger":
            safety_label = "비추천"
            safety_class = "danger"
        elif safety_score >= 72:
            safety_label = "추천"
            safety_class = "safe"
        elif safety_score >= 42:
            safety_label = "주의"
            safety_class = "caution"
        else:
            safety_label = "비추천"
            safety_class = "danger"

        dist_km = None
        if user_lat is not None:
            dist_km = round(_haversine(user_lat, user_lng, m["lat"], m["lng"]))

        # 일몰 여유 설명 문자열
        sunset_note = None
        if margin_min is not None:
            if margin_min >= 0:
                h, mn = divmod(int(margin_min), 60)
                sunset_note = f"일몰 {h}시간 {mn}분 전 하산 완료 예상" if h else f"일몰 {mn}분 전 하산 완료 예상"
            else:
                over = abs(int(margin_min))
                h, mn = divmod(over, 60)
                sunset_note = f"⚠️ 일몰 후 {h}시간 {mn}분 초과 예상" if h else f"⚠️ 일몰 {mn}분 후 하산 완료 예상"

        results.append(with_mountain_identity({
            **m,
            "safety_score": safety_score,
            "safety_label": safety_label,
            "safety_class": safety_class,
            "distance_from_user_km": dist_km,
            "sunset_note": sunset_note,
            "landslide_risk": landslide_risk,
            "score_breakdown": {
                "duration":  round(t_score, 2),
                "sunset":    round(sun_score, 2),
                "distance":  round(dist_score, 2),
                "weather":   round(w_weather, 2),
                "season":    round(season_score, 2),
                "landslide": round(ls_mult, 2),
            },
            "ml_risk_info": ml_risk,
        }))

    results.sort(key=lambda x: x["safety_score"], reverse=True)

    recommended = [r for r in results if r["safety_class"] == "safe"]
    others = [r for r in results if r["safety_class"] != "safe"]

    return {
        "mountains": recommended[:6],
        "alternatives": others[:3],
        "total": len(results),
    }
