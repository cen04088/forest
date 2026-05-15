MOUNTAIN_COORDINATES = {
    "관악산": {"lat": 37.442424, "lng": 126.963344, "region": "서울 관악구"},
    "북한산": {"lat": 37.658611, "lng": 126.977389, "region": "서울 강북구"},
    "도봉산": {"lat": 37.698056, "lng": 127.015278, "region": "서울 도봉구"},
    "인왕산": {"lat": 37.584722, "lng": 126.957778, "region": "서울 종로구"},
    "아차산": {"lat": 37.573056, "lng": 127.103333, "region": "서울 광진구"},
    "청계산": {"lat": 37.4275, "lng": 127.055, "region": "서울 서초구"},
    "수락산": {"lat": 37.699167, "lng": 127.083889, "region": "서울 노원구"},
    "불암산": {"lat": 37.663889, "lng": 127.095833, "region": "서울 노원구"},
    "남산": {"lat": 37.551169, "lng": 126.988227, "region": "서울 중구"},
    "용마산": {"lat": 37.587222, "lng": 127.095556, "region": "서울 중랑구"},
    "설악산": {"lat": 38.119444, "lng": 128.465556, "region": "강원 속초시"},
    "지리산": {"lat": 35.336944, "lng": 127.730556, "region": "경남 산청군"},
    "한라산": {"lat": 33.361667, "lng": 126.529167, "region": "제주 제주시"},
    "가리왕산": {"lat": 37.461944, "lng": 128.563611, "region": "강원 정선군"},
    "계룡산": {"lat": 36.342778, "lng": 127.205556, "region": "충남 공주시"},
    "내장산": {"lat": 35.478333, "lng": 126.8875, "region": "전북 정읍시"},
    "오대산": {"lat": 37.794444, "lng": 128.543611, "region": "강원 평창군"},
    "덕유산": {"lat": 35.859722, "lng": 127.746389, "region": "전북 무주군"},
    "소백산": {"lat": 36.957778, "lng": 128.484444, "region": "충북 단양군"},
    "월악산": {"lat": 36.889444, "lng": 128.105556, "region": "충북 제천시"},
    "속리산": {"lat": 36.543056, "lng": 127.870833, "region": "충북 보은군"},
    "주왕산": {"lat": 36.389444, "lng": 129.163611, "region": "경북 청송군"},
    "무등산": {"lat": 35.134167, "lng": 126.988889, "region": "광주 동구"},
    "가야산": {"lat": 35.823611, "lng": 128.120833, "region": "경남 합천군"},
    "치악산": {"lat": 37.365, "lng": 128.055556, "region": "강원 원주시"},
    "월출산": {"lat": 34.765, "lng": 126.704444, "region": "전남 영암군"},
    "마니산": {"lat": 37.612778, "lng": 126.431944, "region": "인천 강화군"},
    "감악산": {"lat": 37.941389, "lng": 126.97, "region": "경기 파주시"},
    "운악산": {"lat": 37.878333, "lng": 127.326389, "region": "경기 가평군"},
    "명지산": {"lat": 37.941389, "lng": 127.432778, "region": "경기 가평군"},
}

MOUNTAIN_ALIASES = {
    "설악산": ["권금성", "소공원", "비선대", "대청봉", "울산바위"],
    "북한산": ["도봉", "우이", "송추", "오봉"],
    "지리산": ["백무동", "중산리", "세석", "연하천"],
    "계룡산": ["갑사", "동학사", "신원사"],
    "내장산": ["백양", "구암사", "내장사"],
    "오대산": ["월정사", "상원사", "두로령"],
    "월악산": ["하늘재", "부봉", "마패봉"],
}

AMBIGUOUS_MOUNTAIN_NAMES = {"남산"}


def find_mountain_coordinates(*parts):
    raw_parts = [str(part or "") for part in parts]
    joined = " ".join(raw_parts).replace(" ", "")
    if "우이도" in joined:
        return None, None

    for mountain, data in MOUNTAIN_COORDINATES.items():
        if mountain in AMBIGUOUS_MOUNTAIN_NAMES and not any(part.strip() == mountain for part in raw_parts):
            continue
        if mountain.replace(" ", "") in joined:
            return mountain, data

    for mountain, aliases in MOUNTAIN_ALIASES.items():
        if any(alias.replace(" ", "") in joined for alias in aliases):
            return mountain, MOUNTAIN_COORDINATES[mountain]

    return None, None
