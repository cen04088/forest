"""에어코리아(한국환경공단) 대기질 실시간 측정 데이터 API.

공공데이터 포털 대기오염정보: https://apis.data.go.kr/B552584/ArpltnInforInqireSvc
기존 PUBLIC_SERVICE_KEY 사용 — 별도 키 불필요.
"""
import json
import urllib.parse
import urllib.request
from functools import lru_cache

from .loaders import load_public_service_key

AIRQUALITY_URL = (
    "https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty"
)

# 산 이름 → 시도명 (에어코리아 API sidoName 파라미터)
_MOUNTAIN_TO_SIDO = {
    "북한산": "서울", "도봉산": "서울", "남산": "서울", "인왕산": "서울",
    "관악산": "서울", "아차산": "서울", "용마산": "서울", "청계산": "경기",
    "수락산": "경기", "불암산": "경기", "마니산": "인천",
    "설악산": "강원", "오대산": "강원", "태백산": "강원", "두타산": "강원",
    "함백산": "강원", "가리왕산": "강원",
    "지리산": "경남", "가야산": "경남", "덕유산": "전북",
    "한라산": "제주",
    "계룡산": "충남", "속리산": "충북", "월악산": "충북",
    "내장산": "전북", "조계산": "전남", "두륜산": "전남", "월출산": "전남",
    "팔공산": "경북", "주왕산": "경북",
    "무등산": "광주",
    "소백산": "충북",
}
_DEFAULT_SIDO = "서울"

_GRADE_LABEL = {"1": "좋음", "2": "보통", "3": "나쁨", "4": "매우나쁨"}


def sido_for_mountain(mountain_name: str) -> str:
    name = (mountain_name or "").strip()
    for key, sido in _MOUNTAIN_TO_SIDO.items():
        if key in name:
            return sido
    return _DEFAULT_SIDO


def fetch_air_quality(mountain_name: str = "", timeout: int = 8) -> dict:
    """에어코리아 API로 산 인근 시도의 실시간 대기질 데이터 조회.

    Args:
        mountain_name: 산 이름 (시도 매핑에 사용)
        timeout: HTTP 타임아웃(초)

    Returns:
        ok=True 시 pm10_ugm3, pm25_ugm3, grade_pm10, grade_pm25, sido, station_name 포함.
    """
    service_key = load_public_service_key()
    if not service_key:
        return {"ok": False, "source": "airkorea", "error": "PUBLIC_SERVICE_KEY 미설정", "items": []}

    sido = sido_for_mountain(mountain_name)
    return _cached_fetch_air_quality(sido, service_key, timeout)


@lru_cache(maxsize=32)
def _cached_fetch_air_quality(sido: str, service_key: str, timeout: int) -> dict:
    query = {
        "serviceKey": service_key,
        "returnType": "json",
        "numOfRows": "5",
        "pageNo": "1",
        "sidoName": sido,
        "ver": "1.0",
    }
    url = f"{AIRQUALITY_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read()
    except Exception as exc:
        return {
            "ok": False,
            "source": "airkorea",
            "error": f"요청 실패: {str(exc)[:100]}",
            "items": [],
        }

    return _parse_response(body, sido)


def _parse_response(body: bytes, sido: str) -> dict:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "source": "airkorea", "error": "JSON 파싱 오류", "items": []}

    items_raw = (
        payload.get("response", {}).get("body", {}).get("items")
        or payload.get("items")
        or []
    )
    if isinstance(items_raw, dict):
        items_raw = [items_raw]

    items = [_normalize(item) for item in items_raw if isinstance(item, dict)]
    if not items:
        return {"ok": False, "source": "airkorea", "error": "데이터 없음", "items": []}

    # PM2.5 값이 있는 첫 번째 관측소를 대표값으로 사용
    rep = next((it for it in items if it.get("pm25_ugm3") is not None), items[0])

    return {
        "ok": True,
        "source": "airkorea",
        "sido": sido,
        "station_name": rep.get("station_name"),
        "measured_at": rep.get("measured_at"),
        "pm10_ugm3": rep.get("pm10_ugm3"),
        "pm25_ugm3": rep.get("pm25_ugm3"),
        "grade_pm10": rep.get("grade_pm10"),
        "grade_pm25": rep.get("grade_pm25"),
        "items": items,
    }


def _normalize(item: dict) -> dict:
    pm10 = _to_float(item.get("pm10Value") or item.get("pm10Value24"))
    pm25 = _to_float(item.get("pm25Value") or item.get("pm25Value24"))
    return {
        "station_name": item.get("stationName", ""),
        "measured_at": item.get("dataTime", ""),
        "pm10_ugm3": pm10,
        "pm25_ugm3": pm25,
        "grade_pm10": _GRADE_LABEL.get(str(item.get("pm10Grade", "")), "알수없음"),
        "grade_pm25": _GRADE_LABEL.get(str(item.get("pm25Grade", "")), "알수없음"),
        "o3_value": _to_float(item.get("o3Value")),
        "no2_value": _to_float(item.get("no2Value")),
    }


def _to_float(value) -> float | None:
    try:
        v = str(value).strip()
        if v in ("-", "", "null", "None"):
            return None
        return float(v)
    except (TypeError, ValueError):
        return None
