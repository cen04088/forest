import math
from .mountain_data import MOUNTAINS


def _haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _difficulty_score(mountain, companion):
    diff = mountain["difficulty"]
    if companion == "vulnerable":
        return {"easy": 1.0, "medium": 0.4, "hard": 0.0}[diff]
    if companion == "family":
        return {"easy": 0.9, "medium": 0.75, "hard": 0.2}[diff]
    return {"easy": 0.6, "medium": 0.9, "hard": 1.0}[diff]


def _duration_score(mountain, desired_min):
    lo, hi = mountain["walk_time_min"], mountain["walk_time_max"]
    mid = (lo + hi) / 2
    if lo <= desired_min <= hi:
        return 1.0
    if desired_min < lo:
        gap = lo - desired_min
        return max(0.0, 1.0 - gap / 120)
    gap = desired_min - hi
    return max(0.0, 1.0 - gap / 180)


def _purpose_score(mountain, purpose):
    fits = mountain.get("purpose_fit", [])
    if purpose in fits:
        return 1.0
    if purpose == "balanced":
        return 0.7
    return 0.4


def _distance_score(mountain, user_lat, user_lng):
    if user_lat is None or user_lng is None:
        return 0.5
    d = _haversine(user_lat, user_lng, mountain["lat"], mountain["lng"])
    if d <= 30:
        return 1.0
    if d <= 80:
        return 0.8
    if d <= 150:
        return 0.6
    if d <= 300:
        return 0.4
    return 0.2


def _weather_score(weather):
    if not weather:
        return 0.7
    score = 1.0
    rainfall = float(weather.get("rainfall_mm", 0) or 0)
    wind = float(weather.get("wind_speed_ms", 0) or 0)
    temp = float(weather.get("temperature_c", 15) or 15)
    if rainfall >= 10:
        score -= 0.5
    elif rainfall > 0:
        score -= 0.2
    if wind >= 8:
        score -= 0.3
    elif wind >= 5:
        score -= 0.15
    if temp <= 0 or temp >= 35:
        score -= 0.2
    return max(0.0, score)


def recommend_mountains(payload):
    profile = payload.get("profile", {})
    user_lat = None
    user_lng = None
    loc = payload.get("location") or {}
    if loc.get("lat") and loc.get("lng"):
        user_lat = float(loc["lat"])
        user_lng = float(loc["lng"])

    companion = profile.get("companion", "family")
    desired_min = int(profile.get("desiredHikingMinutes", 180))
    purpose = profile.get("purpose", "balanced")
    weather = payload.get("weather")

    w_weather = _weather_score(weather)

    results = []
    for m in MOUNTAINS:
        d_score = _difficulty_score(m, companion)
        t_score = _duration_score(m, desired_min)
        p_score = _purpose_score(m, purpose)
        dist_score = _distance_score(m, user_lat, user_lng)

        total = (
            d_score * 0.35
            + t_score * 0.25
            + dist_score * 0.20
            + p_score * 0.10
            + w_weather * 0.10
        )

        # 동반자 부적합 산 제외
        if d_score == 0.0:
            continue

        safety_score = round(total * 100)
        if safety_score >= 75:
            safety_label = "추천"
            safety_class = "safe"
        elif safety_score >= 45:
            safety_label = "주의"
            safety_class = "caution"
        else:
            safety_label = "비추천"
            safety_class = "danger"

        dist_km = None
        if user_lat is not None:
            dist_km = round(_haversine(user_lat, user_lng, m["lat"], m["lng"]))

        results.append({
            **m,
            "safety_score": safety_score,
            "safety_label": safety_label,
            "safety_class": safety_class,
            "distance_from_user_km": dist_km,
            "score_breakdown": {
                "difficulty": round(d_score, 2),
                "duration": round(t_score, 2),
                "distance": round(dist_score, 2),
                "purpose": round(p_score, 2),
                "weather": round(w_weather, 2),
            },
        })

    results.sort(key=lambda x: x["safety_score"], reverse=True)

    recommended = [r for r in results if r["safety_class"] == "safe"]
    others = [r for r in results if r["safety_class"] != "safe"]

    return {
        "mountains": recommended[:6],
        "alternatives": others[:3],
        "total": len(results),
    }
