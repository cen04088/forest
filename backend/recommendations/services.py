from datetime import datetime, timedelta
from math import asin, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo

from .disaster_risk import disaster_risk_level, disaster_risk_messages, find_course_disaster_risks
from .forest_api import fetch_forest_spatial_data, forest_spatial_items_to_courses
from .loaders import load_public_trail_courses, load_disaster_risk_zones
from .local_road_api import fetch_local_road_trails
from .weather_api import fetch_current_weather, merge_mountain_weather
from .vworld_api import fetch_vworld_trails


DIFFICULTY_LEVEL = {"easy": 1, "medium": 2, "hard": 3}
EXPERIENCE_LEVEL = {"beginner": 1, "intermediate": 2, "advanced": 3}
INTENSITY_LEVEL = {"light": 1, "moderate": 2, "strong": 3}
GENERIC_COURSE_NAMES = {"탐방로", "주등산로", "자연관찰로"}


def haversine_km(lat1, lng1, lat2, lng2):
    radius = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def weather_safety_score(weather):
    score = 100
    rainfall = float(weather.get("rainfall_mm") or 0)
    wind = float(weather.get("wind_speed_ms") or 0)
    temp = float(weather.get("temperature_c") or 15)

    if rainfall >= 10:
        score -= 45
    elif rainfall > 0:
        score -= 20

    if wind >= 8:
        score -= 30
    elif wind >= 5:
        score -= 15

    if temp <= 0 or temp >= 32:
        score -= 20

    # 복합 위험: 비+강풍 동시 발생은 단순 합산보다 훨씬 위험
    if rainfall >= 5 and wind >= 5:
        score -= 20
    # 영하권 강수: 결빙/블랙아이스 위험
    if temp <= 2 and rainfall > 0:
        score -= 15
    # 폭염+무풍: 열사병 위험
    if temp >= 30 and wind < 2:
        score -= 10

    return max(score, 0)


def fitness_score(course, profile):
    experience = EXPERIENCE_LEVEL.get(profile.get("experience"), 1)
    intensity = INTENSITY_LEVEL.get(profile.get("intensity"), 1)
    condition = int(profile.get("condition", 3))
    target = round((experience + intensity + max(condition - 1, 1)) / 3)
    gap = abs(DIFFICULTY_LEVEL[course["difficulty"]] - target)
    return max(100 - gap * 28 - course["elevation_gain_m"] / 25, 35)


def accessibility_score(course, lat, lng, profile=None):
    if course.get("lat") is None or course.get("lng") is None:
        return 70, None

    distance = haversine_km(lat, lng, course["lat"], course["lng"])
    score = max(100 - distance * 3.2, 20)

    max_distance = int((profile or {}).get("maxDistanceKm", 30))
    if distance > max_distance:
        score -= min((distance - max_distance) * 3, 35)

    return score, round(distance, 1)


def time_fit_score(course, profile, weather=None):
    available = int(profile.get("availableMinutes", 180))
    desired = int(profile.get("desiredHikingMinutes") or available)
    score = 100
    if course["duration_min"] > available:
        overtime = course["duration_min"] - available
        score = max(100 - overtime * 1.8, 15)

    lower, upper = time_buffer_range(desired, profile)
    duration = int(course.get("duration_min", 0))
    if duration < lower:
        score -= min((lower - duration) * 0.5, 15)
    elif duration > upper:
        score -= min((duration - upper) * 0.8, 25)

    daylight_margin = daylight_margin_minutes(
        course,
        weather,
        departure_date=profile.get("departureDate"),
        departure_time=profile.get("departureTime"),
    )
    if daylight_margin is not None:
        if daylight_margin < 0:
            score -= 45
        elif daylight_margin < 30:
            score -= 25
        elif daylight_margin < 60:
            score -= 10

    return max(score, 15)


def time_buffer_range(minutes, profile=None):
    lower = max(0, int(minutes) - 30)
    upper_buffer = 15 if is_vulnerable_companion(profile or {}) else 30
    return lower, int(minutes) + upper_buffer


def safety_grade(score):
    if score >= 80:
        return "safe"
    if score >= 55:
        return "caution"
    return "danger"


def is_vulnerable_companion(profile):
    return profile.get("companion") in {"family", "vulnerable"}


def compute_weights(profile):
    """맥락(취약자 동반·산행 목적)에 따라 점수 가중치를 동적으로 결정한다."""
    vulnerable = is_vulnerable_companion(profile)
    purpose = profile.get("purpose", "balanced")
    if vulnerable:
        # 취약자 동반: 체력 적합성·시간 여유 최우선, 접근성 비중 축소
        return {"fit": 0.45, "weather": 0.25, "time": 0.25, "access": 0.05}
    if purpose == "healing":
        # 힐링: 기상·접근성 중시, 체력 소모 최소화
        return {"fit": 0.25, "weather": 0.35, "access": 0.25, "time": 0.15}
    if purpose == "workout":
        # 운동: 체력 적합성 최우선
        return {"fit": 0.40, "weather": 0.25, "access": 0.20, "time": 0.15}
    # 기본(balanced·전망 등)
    return {"fit": 0.35, "weather": 0.30, "access": 0.20, "time": 0.15}


def safety_decision_for_course(course, profile, weather, weather_score, fit_score, time_score, daylight_margin):
    red_flags = []
    yellow_flags = []

    rainfall = float(weather.get("rainfall_mm", 0) or 0)
    wind = float(weather.get("wind_speed_ms", 0) or 0)
    wildfire = weather.get("wildfire_risk", "low")
    vulnerable = is_vulnerable_companion(profile)
    disaster_zones = course.get("disaster_risk_zones", [])
    disaster_level = disaster_risk_level(disaster_zones)

    if disaster_level == "high":
        red_flags.extend(disaster_risk_messages(disaster_zones)[:2])
    elif disaster_level == "caution":
        yellow_flags.extend(disaster_risk_messages(disaster_zones)[:2])

    if rainfall >= 10:
        red_flags.append("강수량이 높아 미끄럼 위험이 큽니다")
    elif rainfall > 0:
        yellow_flags.append("비 또는 젖은 노면으로 미끄럼 주의가 필요합니다")

    if wind >= 8:
        red_flags.append("강풍으로 능선부 보행 위험이 높습니다")
    elif wind >= 5:
        yellow_flags.append("풍속이 다소 높아 노출 구간 주의가 필요합니다")

    if daylight_margin is not None:
        if daylight_margin < 30:
            red_flags.append("일몰 전 하산 여유가 30분 미만입니다")
        elif daylight_margin < 60:
            yellow_flags.append("일몰 전 하산 여유가 충분하지 않습니다")

    if wildfire == "very_high":
        red_flags.append("산불 위험 단계가 높습니다")
    elif wildfire in {"medium", "high"}:
        yellow_flags.append("산불 위험을 확인하고 입산 안내를 따라야 합니다")

    if vulnerable:
        if course.get("difficulty") == "hard":
            red_flags.append("어린이·노약자 동반 산행에 난이도가 높습니다")
        elif course.get("difficulty") == "medium":
            yellow_flags.append("어린이·노약자 동반 시 일부 구간에서 보호자 확인이 필요합니다")
        if int(course.get("duration_min", 0)) > 120:
            yellow_flags.append("어린이·노약자 동반 산행에 코스 시간이 길 수 있습니다")
        elif int(course.get("duration_min", 0)) > int(profile.get("availableMinutes", 180)) + 15:
            yellow_flags.append("선택한 시간보다 코스가 길어 피로 누적 가능성이 있습니다")

    elevation = int(course.get("elevation_gain_m", 0))
    if vulnerable:
        elev_red, elev_yellow = 400, 250
    else:
        elev_red, elev_yellow = 900, 500
    if elevation >= elev_red:
        red_flags.append("누적 고도 상승량이 큽니다")
    elif elevation >= elev_yellow:
        yellow_flags.append("고도 상승 구간이 있어 체력 안배가 필요합니다")

    if red_flags:
        return {
            "safety_decision": "not_recommended",
            "safety_label": "비추천",
            "safety_color": "red",
            "risk_factors": red_flags + yellow_flags[:2],
            "safe_for_vulnerable": False,
        }

    # 취약자 동반 시 '주의' 발동 기준을 강화
    caution_yellow = 1 if vulnerable else 2
    caution_weather = 85 if vulnerable else 80
    caution_fit = 75 if vulnerable else 65
    caution_time = 75 if vulnerable else 70
    if len(yellow_flags) >= caution_yellow or weather_score < caution_weather or fit_score < caution_fit or time_score < caution_time:
        return {
            "safety_decision": "caution",
            "safety_label": "주의",
            "safety_color": "yellow",
            "risk_factors": yellow_flags or ["기상, 시간, 체력 조건 확인이 필요합니다"],
            "safe_for_vulnerable": not vulnerable or fit_score >= caution_fit,
        }

    return {
        "safety_decision": "recommend",
        "safety_label": "추천",
        "safety_color": "green",
        "risk_factors": ["현재 조건에서 안정적으로 이용 가능한 코스입니다"],
        "safe_for_vulnerable": True,
    }


def safety_rank(decision):
    return {"recommend": 3, "caution": 2, "not_recommended": 1}.get(decision, 0)


def recommend_courses(payload):
    profile = payload.get("profile", {})
    location = payload.get("location") or {"lat": 37.5665, "lng": 126.978}
    weather = fetch_current_weather(location["lat"], location["lng"])
    courses = [dict(course) for course in load_public_trail_courses()]

    mountain_name = (profile.get("mountainName") or "").strip()
    query_lat = location.get("lat")
    query_lng = location.get("lng")

    if mountain_name:
        weather = merge_mountain_weather(weather, mountain_name, profile.get("mountainNum"))
        from .mountain_coordinates import find_mountain_coordinates
        _, mtn_coords = find_mountain_coordinates(mountain_name)
        if mtn_coords:
            query_lat = mtn_coords["lat"]
            query_lng = mtn_coords["lng"]

    weather_score = weather_safety_score(weather)
    all_disaster_zones = load_disaster_risk_zones()  # lru_cache — 한 번만 IO 발생
    if mountain_name:
        local_road_result = fetch_local_road_trails(
            query_lat,
            query_lng,
            mountain_name,
            radius_km=max(int(profile.get("maxDistanceKm", 30)) / 2, 8),
            size=40,
        )
        courses = local_road_result.get("items", []) + courses
        vworld_result = fetch_vworld_trails(
            lat=query_lat,
            lng=query_lng,
            mountain_name=mountain_name,
            radius_km=max(int(profile.get("maxDistanceKm", 30)) / 2, 5),
            size=40,
        )
        courses = vworld_result.get("items", []) + courses
        forest_result = fetch_forest_spatial_data(mountain_name, 1, 10)
        courses = forest_spatial_items_to_courses(forest_result) + courses

    recommendations = []
    for course in courses:
        course["disaster_risk_zones"] = find_course_disaster_risks(course, all_disaster_zones)
        fit = fitness_score(course, profile)
        access, distance = accessibility_score(course, location["lat"], location["lng"], profile)
        time_fit = time_fit_score(course, profile, weather)
        daylight_margin = daylight_margin_minutes(
            course,
            weather,
            departure_date=profile.get("departureDate"),
            departure_time=profile.get("departureTime"),
        )
        safety = safety_decision_for_course(course, profile, weather, weather_score, fit, time_fit, daylight_margin)
        w = compute_weights(profile)
        total = fit * w["fit"] + weather_score * w["weather"] + access * w["access"] + time_fit * w["time"]
        total -= course["crowding"] * 8
        total -= disaster_zone_penalty(course)
        total += mountain_preference_bonus(course, mountain_name)
        total += purpose_bonus(course, profile)
        total += transport_bonus(course, distance, profile)
        total += data_quality_adjustment(course)

        recommendations.append(
            {
                **course,
                **safety,
                "score": round(min(total, 100), 1),
                "scores": {
                    "fitness": round(fit, 1),
                    "weather": round(weather_score, 1),
                    "accessibility": round(access, 1),
                    "time": round(time_fit, 1),
                },
                "distance_from_user_km": distance,
                "daylight_margin_min": daylight_margin,
                "safety_grade": safety_grade(weather_score),
                "reason": build_reason(course, profile, weather_score, distance, daylight_margin),
                "agent_briefing": build_agent_briefing(course, safety, daylight_margin, weather),
                "safe_link_preview": build_safe_link_preview(course, safety),
                "weather": weather,
            }
        )

    recommendations.sort(key=lambda item: (safety_rank(item["safety_decision"]), item["score"]), reverse=True)
    if mountain_name and not is_generic_mountain_name(mountain_name):
        matched = [
            item
            for item in recommendations
            if mountain_name.replace(" ", "") in str(item.get("mountain", "")).replace(" ", "")
            or mountain_name.replace(" ", "") in str(item.get("name", "")).replace(" ", "")
        ]
        others = [item for item in recommendations if item not in matched]
        recommendations = matched + others
    top3 = recommendations[:3]
    alternatives = select_alternatives(recommendations, top3, profile)
    no_safe_course = bool(recommendations) and all(item["safety_decision"] == "not_recommended" for item in recommendations[:8])

    return {
        "result_state": "no_safe_course" if no_safe_course else "has_recommendations",
        "recommendations": top3,
        "alternatives": alternatives,
        "weather": weather,
        "agent_summary": build_no_safe_course_message(weather) if no_safe_course else top3[0]["agent_briefing"] if top3 else "",
        "alternative_actions": (
            ["다른 날짜로 다시 보기", "검색 반경 넓히기", "쉬운 산책 코스만 보기", "실내 대체 활동 보기"]
            if no_safe_course
            else []
        ),
    }


def build_agent_briefing(course, safety, daylight_margin=None, weather=None):
    from .llm_briefing import generate_briefing
    llm = generate_briefing(course, safety, weather or {}, daylight_margin)
    if llm:
        return llm
    factors = ", ".join(safety["risk_factors"][:2])
    if safety["safety_decision"] == "recommend":
        return f"{course['name']}은 현재 기상과 하산 시간을 고려했을 때 안정적으로 이용 가능한 코스입니다."
    if safety["safety_decision"] == "caution":
        return f"{course['name']}은 주의가 필요합니다. {factors}"
    return f"{course['name']}은 현재 조건에서 비추천입니다. {factors}"


def build_safe_link_preview(course, safety):
    return {
        "enabled": True,
        "status": "정상 이동" if safety["safety_decision"] == "recommend" else "주의 모니터링",
        "last_sync": "방금 전",
        "alerts": [
            {
                "type": "risk_zone",
                "label": "보행 주의 구간 진입",
                "message": safety["risk_factors"][0],
            }
        ]
        if safety["safety_decision"] != "recommend"
        else [],
    }


def build_no_safe_course_message(weather):
    return (
        "현재 조건에서 안전하게 추천할 수 있는 코스가 없습니다. "
        f"강수 {weather.get('rainfall_mm', 0)}mm, 풍속 {weather.get('wind_speed_ms', 0)}m/s, "
        "일몰 여유를 고려해 산행을 연기하거나 쉬운 산책 코스를 확인하세요."
    )


def build_reason(course, profile, weather_score, distance, daylight_margin=None):
    condition = int(profile.get("condition", 3))
    companion = profile.get("companion", "solo")

    reasons = []
    if condition <= 2:
        reasons.append("오늘 컨디션을 고려해 무리 없는 난이도를 우선했습니다")
    elif course["difficulty"] != "easy":
        reasons.append("현재 컨디션과 활동 강도에 맞춰 운동량이 있는 코스를 골랐습니다")
    else:
        reasons.append("안전하게 다녀오기 좋은 짧은 코스를 우선했습니다")

    if weather_score >= 80:
        reasons.append("강수와 풍속 위험이 낮아 날씨 안전도가 좋습니다")
    else:
        reasons.append("날씨 위험을 반영해 하산 부담이 낮은 코스를 우선했습니다")

    if companion in ["family", "friend"]:
        reasons.append("동반 산행에 맞춰 접근성과 완만한 구간을 함께 반영했습니다")

    purpose = profile.get("purpose")
    if purpose == "healing":
        reasons.append("힐링 목적에 맞춰 짧고 부담이 낮은 코스를 우선했습니다")
    elif purpose == "workout":
        reasons.append("운동 목적에 맞춰 적당한 활동량을 확보했습니다")
    elif purpose == "view":
        reasons.append("전망과 지도 확인이 쉬운 코스를 우선했습니다")

    if distance is None:
        reasons.append("좌표 데이터가 보강되면 현재 위치 기준 접근성을 더 정확히 반영할 수 있습니다")
    else:
        reasons.append(f"현재 위치에서 약 {distance}km 떨어져 있습니다")

    if daylight_margin is not None:
        if daylight_margin < 0:
            reasons.append("예상 하산 시간이 일몰 이후라 더 짧은 코스를 권장합니다")
        elif daylight_margin < 60:
            reasons.append("일몰 전 하산 여유가 크지 않아 출발 시간을 앞당기는 것이 좋습니다")
        else:
            reasons.append(f"일몰 전 약 {daylight_margin}분의 하산 여유가 있습니다")
    return " ".join(reasons) + "."


def mountain_preference_bonus(course, mountain_name):
    if not mountain_name:
        return 0
    if is_generic_mountain_name(mountain_name):
        return 0

    target = mountain_name.replace(" ", "")
    mountain = str(course.get("mountain", "")).replace(" ", "")
    name = str(course.get("name", "")).replace(" ", "")
    if target and (target in mountain or target in name):
        return 45
    return 0


def purpose_bonus(course, profile):
    purpose = profile.get("purpose", "balanced")
    difficulty = course.get("difficulty")
    duration = int(course.get("duration_min", 0))
    has_coordinates = course.get("lat") is not None and course.get("lng") is not None

    if purpose == "healing":
        return (10 if difficulty == "easy" else 0) + (8 if duration <= 90 else 0)
    if purpose == "workout":
        return 12 if difficulty in {"medium", "hard"} and duration >= 90 else 0
    if purpose == "view":
        return 10 if has_coordinates or course.get("map_url") else 0
    return 0


def transport_bonus(course, distance, profile):
    transport = profile.get("transport", "public")
    if distance is None:
        return -8 if transport == "public" else -4
    if transport == "public" and distance <= 15:
        return 6
    if transport == "car" and distance <= 45:
        return 5
    return 0


def data_quality_adjustment(course):
    adjustment = 0
    name = str(course.get("name", "")).strip()
    mountain = str(course.get("mountain", "")).strip()
    distance_km = float(course.get("distance_km") or 0)

    if name in GENERIC_COURSE_NAMES:
        adjustment -= 18
    if mountain == "국립공원":
        adjustment -= 10
    if distance_km and distance_km < 0.3:
        adjustment -= 35
    elif distance_km and distance_km < 0.8:
        adjustment -= 15
    if course.get("lat") is None or course.get("lng") is None:
        adjustment -= 28
    else:
        adjustment += 5
    return adjustment


def is_generic_mountain_name(name):
    return str(name or "").replace(" ", "") in {"국립공원", "등산로", "브이월드등산로"}


def disaster_zone_penalty(course):
    """매칭된 재난위험지구 수·위험도에 따른 총점 감점."""
    zones = course.get("disaster_risk_zones") or []
    if not zones:
        return 0
    high_risk_keywords = {"추락", "낙석", "급경사", "붕괴", "고립"}
    high = sum(1 for z in zones if any(kw in (z.get("risk_factor") or "") for kw in high_risk_keywords))
    caution = len(zones) - high
    return high * 6 + caution * 2


def select_alternatives(recommendations, top_courses, profile=None):
    profile = profile or {}
    purpose = profile.get("purpose", "balanced")
    available = int(profile.get("availableMinutes", 180))
    top_ids = {course["id"] for course in top_courses}
    candidates = [course for course in recommendations if course["id"] not in top_ids]

    # 목적별 난이도 선호도 — 기존처럼 항상 easy를 선호하지 않음
    purpose_difficulty = {
        "workout": {"hard": 40, "medium": 30, "easy": 10},
        "healing": {"easy": 40, "medium": 20, "hard": 0},
        "view":    {"easy": 30, "medium": 30, "hard": 15},
    }.get(purpose, {"easy": 30, "medium": 25, "hard": 10})

    def alternative_rank(course):
        daylight = course.get("daylight_margin_min")
        daylight_score = max(0, daylight) if daylight is not None else 0
        distance = course.get("distance_from_user_km")
        access_score = max(0, 80 - distance * 2) if distance is not None else 40
        difficulty_score = purpose_difficulty.get(course.get("difficulty"), 20)
        duration = int(course.get("duration_min", 0))
        time_fit = max(0, 50 - abs(duration - available) * 0.5)
        return difficulty_score + time_fit + daylight_score * 0.25 + access_score

    candidates.sort(key=alternative_rank, reverse=True)
    return candidates[:2]


def daylight_margin_minutes(course, weather, now=None, departure_date=None, departure_time=None):
    if not weather or not weather.get("sunset"):
        return None

    current = parse_departure_datetime(departure_date, departure_time, now)
    current = current or now or datetime.now(ZoneInfo("Asia/Seoul"))
    sunset = parse_departure_datetime(departure_date, weather["sunset"], current)
    if not sunset:
        return None

    finish = current + timedelta(minutes=int(course.get("duration_min", 0)))
    return round((sunset - finish).total_seconds() / 60)


def parse_departure_datetime(date_value=None, time_value=None, now=None):
    try:
        hour, minute = [int(part) for part in str(time_value).split(":")[:2]]
    except (TypeError, ValueError):
        return None

    current = now or datetime.now(ZoneInfo("Asia/Seoul"))
    date = current.date()
    if date_value:
        try:
            date = datetime.strptime(str(date_value), "%Y-%m-%d").date()
        except ValueError:
            date = current.date()
    return datetime.combine(date, datetime.min.time(), tzinfo=current.tzinfo).replace(hour=hour, minute=minute)


def parse_today_time(value, now=None):
    return parse_departure_datetime(None, value, now)
