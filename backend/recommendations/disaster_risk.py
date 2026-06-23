from .loaders import load_disaster_risk_zones, normalize_search_text


HIGH_RISK_KEYWORDS = ("추락", "낙석", "급경사", "붕괴", "고립", "범람")
CAUTION_RISK_KEYWORDS = ("위험", "사고", "미끄럼", "침수", "월파", "협곡")
GENERIC_MATCH_TERMS = {"탐방로", "국립공원", "지구", "구간", "코스"}

# district 이름 → 산 이름 매핑 (국립공원 코드명이 산 이름과 다를 때)
DISTRICT_TO_MOUNTAIN = {
    # 설악산
    "남창계곡": "설악산", "남창지구": "설악산",
    "백담": "설악산", "오색": "설악산",
    "외설악": "설악산", "장수대": "설악산",
    "구룡지구": "설악산",  # 사다리병창, 비로봉
    # 지리산
    "금대지구": "지리산", "노고단": "지리산",
    "뱀사골지구": "지리산", "산청지구": "지리산",
    "삼장지구": "지리산", "세석지구": "지리산",
    "청학지구": "지리산", "하동지구": "지리산",
    "함양지구": "지리산",
    # 북한산
    "구기": "북한산", "구기지구": "북한산",
    "북한산성지구": "북한산",
    "산성": "북한산", "산성분소": "북한산", "산성지구": "북한산",
    "새인봉 암장 남서벽": "북한산",
    "새인봉 하단 10m": "북한산", "새인봉 하단 200m": "북한산",
    "수유": "북한산", "우이지구": "북한산", "정릉지구": "북한산",
    # 덕유산
    "구천동지구": "덕유산", "영각지구": "덕유산",
    "용추봉 하단 70m": "덕유산",
    "적상지구": "덕유산", "종주능선 삼도봉": "덕유산",
    "황점지구": "덕유산",
    # 속리산
    "법주사지구": "속리산", "쌍곡지구": "속리산",
    "화북지구": "속리산", "화양지구": "속리산",
    # 무등산
    "백운동지구": "무등산",
    "서석대 전망대": "무등산", "서석대 전망대 하단 50m": "무등산",
    "약사바위": "무등산",
    "탑봉": "무등산", "탑봉 하단 160m": "무등산",
    # 오대산
    "소금강지구": "오대산", "월정지구": "오대산",
    # 월악산
    "송계지구": "월악산", "용하지구": "월악산",
    # 가야산
    "덕산지구": "가야산", "해인사지구": "가야산",
    # 내장산
    "내장지구": "내장산",
    "백양계곡": "내장산", "백양사 지구": "내장산",
    # 계방산
    "계방산지구": "계방산",
    "황골지구": "계방산", "황골(곧은재)": "계방산",
    # 팔영산 (오탈자 포함)
    "팔영산지구(12)": "팔영산", "팔영산지구(13)": "팔영산",
    "팔영산지구(14)": "팔영산", "팔영산지구(15)": "팔영산",
    "팔영산자구(16)": "팔영산", "팔영산지구(17)": "팔영산",
    "팔영산지구(18)": "팔영산", "팔영산지구(19)": "팔영산",
    # 계룡산
    "인계리지구": "계룡산",
    # 도락산
    "단양지구": "도락산",
    # 소백산·토함산 (기존 직접 매칭 보완)
    "소백산 도솔봉지구": "소백산",
    "토함산": "토함산",
}


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
    # 1. district→산 매핑 테이블 우선 체크
    district = zone.get("district", "")
    mapped = DISTRICT_TO_MOUNTAIN.get(district, "")
    if mapped:
        norm_mapped = normalize_search_text(mapped)
        if norm_mapped and norm_mapped in course_text:
            return True

    # 2. 기존 텍스트 매칭 (fallback)
    tokens = [district, zone.get("location", ""), zone.get("facility", "")]
    for token in tokens:
        normalized = normalize_search_text(token)
        if len(normalized) >= 3 and (normalized in course_text or course_text in normalized):
            return True

    district_words = [
        normalize_search_text(word)
        for word in str(district).split()
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
