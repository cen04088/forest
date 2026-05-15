from .loaders import load_disaster_risk_zones, normalize_search_text


HIGH_RISK_KEYWORDS = ("추락", "낙석", "급경사", "붕괴", "고립", "범람")
CAUTION_RISK_KEYWORDS = ("위험", "사고", "미끄럼", "침수", "월파", "협곡")
GENERIC_MATCH_TERMS = {"탐방로", "국립공원", "지구", "구간", "코스"}


def find_course_disaster_risks(course, zones=None, limit=3):
    zones = zones if zones is not None else load_disaster_risk_zones()
    course_text = normalize_course_text(course)
    if not course_text:
        return []

    matches = []
    for zone in zones:
        if zone_matches_course(zone, course_text):
            matches.append(zone)
            if len(matches) >= limit:
                break
    return matches


def normalize_course_text(course):
    parts = [
        course.get("mountain", ""),
        course.get("name", ""),
        course.get("region", ""),
        " ".join(course.get("highlights", []) or []),
    ]
    return normalize_search_text(" ".join(str(part) for part in parts if part))


def zone_matches_course(zone, course_text):
    tokens = [
        zone.get("district", ""),
        zone.get("location", ""),
        zone.get("facility", ""),
    ]
    for token in tokens:
        normalized = normalize_search_text(token)
        if len(normalized) >= 3 and (normalized in course_text or course_text in normalized):
            return True

    district_words = [
        normalize_search_text(word)
        for word in str(zone.get("district", "")).split()
        if normalize_search_text(word) not in GENERIC_MATCH_TERMS
    ]
    return any(len(word) >= 3 and word in course_text for word in district_words)


def disaster_risk_level(zones):
    joined = " ".join(zone.get("risk_factor", "") for zone in zones)
    if any(keyword in joined for keyword in HIGH_RISK_KEYWORDS):
        return "high"
    if any(keyword in joined for keyword in CAUTION_RISK_KEYWORDS):
        return "caution"
    return "low" if zones else "none"


def disaster_risk_messages(zones):
    messages = []
    for zone in zones:
        location = zone.get("location") or zone.get("facility") or zone.get("district")
        factor = zone.get("risk_factor") or "재난위험지구"
        messages.append(f"{location}: {factor}")
    return messages
