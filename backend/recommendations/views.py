import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .landslide_api import fetch_landslide_prediction
from .loaders import load_public_service_key, load_public_trail_courses, load_disaster_risk_zones
from .mountain_coordinates import MOUNTAIN_COORDINATES
from .mountain_story_api import fetch_mountain_story
from .services import recommend_courses
from .mountain_recommend import recommend_mountains
from .mountain_data import MOUNTAINS
from .sun_api import fetch_sun_times
from .weather_api import fetch_current_weather
from .wildfire_api import fetch_wildfire_risk
from .vworld_api import fetch_vworld_trails
from . import safe_links as safe_link_store
from .osm_trail_api import fetch_osm_trails
from .local_road_api import fetch_local_road_trails


@require_GET
def health(request):
    key = load_public_service_key()
    return JsonResponse(
        {
            "status": "ok",
            "service": "올라 API",
            "public_trail_courses": len(load_public_trail_courses()),
            "public_service_key_loaded": bool(key),
            "public_service_key_prefix": (key[:6] + "...") if key else None,
            "fallback_mountain_coordinates": len(MOUNTAIN_COORDINATES),
        }
    )


@require_GET
def courses(request):
    return JsonResponse({"courses": load_public_trail_courses()})


@require_GET
def data_sources(request):
    key = load_public_service_key()
    return JsonResponse(
        {
            "connected_sources": [
                {
                    "id": "public_trails",
                    "name": "National park trail courses",
                    "status": "loaded",
                    "count": len(load_public_trail_courses()),
                },
                {
                    "id": "disaster_risk_zones",
                    "name": "Disaster risk zones",
                    "status": "loaded",
                    "count": len(load_disaster_risk_zones()),
                },
                {
                    "id": "weather",
                    "name": "KMA nowcast and public safety APIs",
                    "status": "configured" if key else "mock",
                },
            ],
            "service_key_loaded": bool(key),
        },
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def vworld_trails(request):
    mountain_name = request.GET.get("mountain", "")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_km = request.GET.get("radius", 5)
    page_no = request.GET.get("page", 1)
    num_of_rows = request.GET.get("size", 50)
    return JsonResponse(
        fetch_vworld_trails(lat, lng, mountain_name, radius_km, page_no, num_of_rows),
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def local_road_trails(request):
    mountain_name = request.GET.get("mountain", "")
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius_km = request.GET.get("radius", 8)
    size = request.GET.get("size", 80)
    return JsonResponse(
        fetch_local_road_trails(lat, lng, mountain_name, radius_km, size),
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def mountain_story(request):
    mountain_name = request.GET.get("mountain", "")
    page_no = request.GET.get("page", 1)
    num_of_rows = request.GET.get("size", 5)

    db_story = _get_db_mountain_story(mountain_name)
    if db_story:
        return JsonResponse(
            {
                "ok": True,
                "items": [db_story],
                "source": "database",
            },
            json_dumps_params={"ensure_ascii": False},
        )

    return JsonResponse(
        fetch_mountain_story(mountain_name, page_no, num_of_rows),
        json_dumps_params={"ensure_ascii": False},
    )


def _get_db_mountain_story(mountain_name):
    name = (mountain_name or "").strip()
    if not name:
        return None

    from .models import MountainIntro, MountainKnowledge

    intro = MountainIntro.objects.filter(mountain_name=name).first()
    knowledge = (
        MountainKnowledge.objects
        .filter(mountain_name=name)
        .order_by("source")
        .first()
    )

    if not intro and not knowledge:
        return None

    intro_text = intro.intro.strip() if intro else ""
    summary = intro_text or (knowledge.summary.strip() if knowledge and knowledge.summary else "")
    detail = (knowledge.detail.strip() if knowledge and knowledge.detail else "") or summary

    return {
        "mountain_id": f"db-{name}",
        "mountain": name,
        "height_m": knowledge.height_m if knowledge else None,
        "address": knowledge.region if knowledge else "",
        "manager": "",
        "summary": summary,
        "detail": detail,
        "intro": intro_text,
        "selection_reason": knowledge.selection_reason if knowledge else "",
        "source": "database",
    }


@require_GET
def weather(request):
    from django.core.cache import cache
    from .airquality_api import fetch_air_quality
    lat = float(request.GET.get("lat", 37.5665))
    lng = float(request.GET.get("lng", 126.978))
    mountain = request.GET.get("mountain", "")
    cache_key = f"weather:{round(lat, 2)}:{round(lng, 2)}:{mountain}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached, json_dumps_params={"ensure_ascii": False})
    result = fetch_current_weather(lat, lng)
    # 미세먼지 통합 (에러 시 무시)
    try:
        aq = fetch_air_quality(mountain, lat=lat, lng=lng)
        if aq.get("ok"):
            result["pm10_ugm3"] = aq.get("pm10_ugm3")
            result["pm25_ugm3"] = aq.get("pm25_ugm3")
            result["grade_pm10"] = aq.get("grade_pm10")
            result["grade_pm25"] = aq.get("grade_pm25")
            result["air_station"] = aq.get("station_name")
    except Exception:
        pass
    cache.set(cache_key, result, 600)
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


@require_GET
def sun_times(request):
    lat = float(request.GET.get("lat", 37.5665))
    lng = float(request.GET.get("lng", 126.978))
    return JsonResponse(fetch_sun_times(lat, lng), json_dumps_params={"ensure_ascii": False})


@require_GET
def wildfire(request):
    return JsonResponse(fetch_wildfire_risk(), json_dumps_params={"ensure_ascii": False})


@require_GET
def landslide(request):
    sgg = request.GET.get("sgg", "")
    forecast_name = request.GET.get("forecast", "")
    page_no = request.GET.get("page", 1)
    num_of_rows = request.GET.get("size", 10)
    return JsonResponse(
        fetch_landslide_prediction(sgg, forecast_name, page_no, num_of_rows),
        json_dumps_params={"ensure_ascii": False},
    )


@require_GET
def mountains(request):
    return JsonResponse({"mountains": _get_mountains()}, json_dumps_params={"ensure_ascii": False})


_NATIONAL_PARKS = {
    "설악산","지리산","한라산","북한산","오대산","소백산","태백산","치악산",
    "월악산","속리산","계룡산","덕유산","가야산","내장산","무등산","주왕산",
    "월출산","팔공산",
}
_CROWDING_MAP = {
    "북한산": 0.82, "도봉산": 0.78, "남산": 0.80, "인왕산": 0.72,
    "관악산": 0.75, "청계산": 0.65, "아차산": 0.70, "수락산": 0.38,
    "불암산": 0.42, "설악산": 0.68, "한라산": 0.70, "지리산": 0.55,
    "계룡산": 0.55, "내장산": 0.58, "오대산": 0.48, "덕유산": 0.45,
    "속리산": 0.52, "주왕산": 0.48, "가야산": 0.55, "치악산": 0.45,
    "소백산": 0.40, "무등산": 0.58, "월출산": 0.42, "월악산": 0.42,
    "팔공산": 0.60, "태백산": 0.40, "함백산": 0.32, "두타산": 0.35,
    "금정산": 0.55, "마이산": 0.50, "황매산": 0.35,
}
_HARD_NAMES = {
    "설악산","지리산","한라산","덕유산","치악산","두타산","함백산","점봉산",
    "방태산","가리왕산","민주지산","화악산","청옥산","대암산","백덕산",
    "황석산","운문산","재약산","신불산","가지산","응봉산",
}
_EASY_NAMES = {
    "인왕산","아차산","수리산","칠갑산","천성산","불암산","선자령","삼악산",
    "수락산","달마산","연화산","팔영산",
}
_HEALING_NAMES = {
    "오대산","내장산","두륜산","천관산","조계산","달마산","연화산","팔영산",
    "선자령","장안산","천성산",
}
_VIEW_NAMES = {
    "설악산","한라산","지리산","북한산","팔공산","무등산","월출산","마이산",
    "황매산","비슬산","팔영산","두타산","금정산",
}
_EASY_ACCESS = {
    "인왕산","아차산","수리산","선자령","삼악산","불암산","수락산","청계산",
    "달마산","두륜산","천관산","금정산","토함산","조계산","연화산","팔영산",
    "천성산","내장산","주왕산","공작산","천마산","도봉산","관악산",
}

_KW_MAP = [
    ("폭포", "폭포 경관"), ("단풍", "단풍 명소"), ("눈", "설경 명소"),
    ("설", "설경 명소"), ("암릉", "암릉 경관"), ("바위", "암릉 경관"),
    ("계곡", "계곡 트레킹"), ("사찰", "사찰 탐방"), ("절", "사찰 탐방"),
    ("전망", "정상 전망 우수"), ("조망", "정상 전망 우수"),
    ("철쭉", "철쭉 명소"), ("동백", "동백 명소"), ("억새", "억새 군락"),
]


def _infer_difficulty(height, name):
    if name in _HARD_NAMES or height >= 1400:
        return "hard"
    if name in _EASY_NAMES or height <= 400:
        return "easy"
    return "medium"


def _infer_companion_fit(difficulty, name):
    if name in _EASY_ACCESS or difficulty == "easy":
        return ["vulnerable", "family", "solo"]
    if difficulty == "medium":
        return ["family", "solo"]
    return ["solo"]


def _infer_purpose_fit(height, name):
    fits = ["balanced"]
    if name in _HEALING_NAMES:
        fits.append("healing")
    if name in _VIEW_NAMES:
        fits.append("view")
    if height >= 1200:
        fits.append("workout")
    if len(fits) == 1:
        fits.append("healing" if height < 800 else "view")
    return list(dict.fromkeys(fits))


def _infer_walk_time(height, difficulty):
    if difficulty == "easy":
        return (60, 180)
    if difficulty == "medium":
        return (90, 240) if height < 800 else (150, 360)
    if height >= 1700:
        return (360, 720)
    if height >= 1400:
        return (270, 540)
    return (200, 450)


def _infer_highlights(name, summary):
    tags = []
    if name in _NATIONAL_PARKS:
        tags.append("국립공원")
    seen = set()
    for kw, label in _KW_MAP:
        if kw in summary and label not in seen:
            tags.append(label)
            seen.add(label)
    if not tags:
        tags.append("자연 경관 우수")
    return tags[:4]


def _get_mountains():
    from .models import MountainIntro, MountainKnowledge
    from .mountain_data import MOUNTAINS as _STATIC

    intros = {obj.mountain_name: obj.intro for obj in MountainIntro.objects.all()}
    knowledge_by_name = {}
    for obj in MountainKnowledge.objects.order_by("mountain_name", "source"):
        knowledge_by_name.setdefault(obj.mountain_name, obj)

    static_mountains = []
    for mountain in _STATIC:
        item = dict(mountain)
        name = item["name"]
        intro = (intros.get(name) or "").strip()
        knowledge = knowledge_by_name.get(name)
        db_description = intro
        if not db_description and knowledge:
            db_description = (knowledge.summary or knowledge.detail or "").strip()

        if db_description:
            item["description"] = db_description
            item["intro"] = intro
            item["description_source"] = "database"
        else:
            item["description_source"] = "static"

        static_mountains.append(item)

    static_names = {m["name"] for m in static_mountains}

    # MountainKnowledge 중 좌표 있는 것을 동적으로 추가
    db_mountains = []
    seen = set(static_names)
    qs = (
        MountainKnowledge.objects
        .exclude(lat__isnull=True)
        .exclude(lng__isnull=True)
        .order_by("mountain_name", "source")
    )
    for mk in qs:
        name = mk.mountain_name
        if name in seen:
            continue
        seen.add(name)
        height = mk.height_m or 0
        difficulty = _infer_difficulty(height, name)
        walk_min, walk_max = _infer_walk_time(height, difficulty)
        db_mountains.append({
            "id": f"m-{name}",
            "name": name,
            "region": mk.region or "",
            "lat": mk.lat,
            "lng": mk.lng,
            "elevation_m": height if height > 0 else None,
            "difficulty": difficulty,
            "walk_time_min": walk_min,
            "walk_time_max": walk_max,
            "trail_count": 0,
            "companion_fit": _infer_companion_fit(difficulty, name),
            "purpose_fit": _infer_purpose_fit(height, name),
            "crowding": _CROWDING_MAP.get(name, 0.35),
            "national_park": name in _NATIONAL_PARKS,
            "highlights": _infer_highlights(name, mk.summary),
            "description": (intros.get(name) or mk.summary or mk.detail or f"{name} — {mk.region}").strip(),
            "intro": (intros.get(name) or "").strip(),
            "description_source": "database",
        })

    return static_mountains + db_mountains


@csrf_exempt
@require_POST
def recommend_mountains_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    # 일몰 시각 조회 — 위치 없으면 서울 기본좌표 사용 (채점에서 제외되면 안 됨)
    loc = payload.get("location") or {}
    lat = float(loc["lat"]) if loc.get("lat") else 37.5665
    lng = float(loc["lng"]) if loc.get("lng") else 126.978
    try:
        sun_data = fetch_sun_times(lat, lng) or {}
        payload["sun_times"] = sun_data
    except Exception:
        pass

    result = recommend_mountains(payload)

    # MountainIntro DB에서 설명을 일괄 조회해 각 산에 주입
    from .models import MountainIntro
    intros = {obj.mountain_name: obj.intro for obj in MountainIntro.objects.all()}
    for m in result.get("mountains", []) + result.get("alternatives", []):
        m["intro"] = intros.get(m["name"], "")

    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
@require_POST
def recommendations(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    return JsonResponse(recommend_courses(payload))


@require_GET
def osm_trails(request):
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    if not lat or not lng:
        return JsonResponse({"items": [], "error": "lat/lng required"}, status=400)
    mountain = request.GET.get("mountain", "")
    radius = int(request.GET.get("radius", 3000))
    result = fetch_osm_trails(float(lat), float(lng), mountain, radius)
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


@require_GET
def disaster_zones(request):
    mountain = request.GET.get("mountain", "").strip()
    zones = load_disaster_risk_zones()
    if mountain:
        from .loaders import normalize_search_text
        needle = normalize_search_text(mountain)
        zones = [z for z in zones if needle in z.get("search_text", "")]
    return JsonResponse({"zones": zones[:30]}, json_dumps_params={"ensure_ascii": False})


@require_GET
def safe_link_by_code(request):
    code = request.GET.get("code", "").strip().upper()
    if not code:
        return JsonResponse({"error": "코드를 입력해 주세요."}, status=400)
    try:
        session = safe_link_store.get_by_code(code)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("safe_link_by_code 오류: %s", exc, exc_info=True)
        return JsonResponse({"error": f"서버 오류: {exc}"}, status=500)
    if not session:
        return JsonResponse({"error": f"코드 '{code}'를 찾을 수 없습니다. (DB에 없음)"}, status=404)
    return JsonResponse(session, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
def safe_link_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    try:
        course = body.get("course", {})
        session = safe_link_store.create(course)
        return JsonResponse({"id": session["id"], "share_code": session.get("share_code", "")}, status=201)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("safe_link_create 오류: %s", exc, exc_info=True)
        return JsonResponse({"error": f"세이프 링크 생성 실패: {exc}"}, status=500)


@csrf_exempt
def safe_link_detail(request, session_id):
    if request.method == "GET":
        session = safe_link_store.get(session_id)
        if not session:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse(session, json_dumps_params={"ensure_ascii": False})

    if request.method == "POST":
        try:
            body = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        action = body.get("action")
        if action == "end":
            session = safe_link_store.end_session(session_id)
            return JsonResponse({"ok": True}) if session else JsonResponse({"error": "Not found"}, status=404)
        lat = body.get("lat")
        lng = body.get("lng")
        if lat is None or lng is None:
            return JsonResponse({"error": "lat and lng required"}, status=400)
        session = safe_link_store.update_location(session_id, float(lat), float(lng))
        if not session:
            return JsonResponse({"error": "Not found"}, status=404)
        return JsonResponse({"ok": True, "location_ts": session["location_ts"]})

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
@require_POST
def chat_view(request):
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid request body"}, status=400)

    messages = body.get("messages", [])
    context = body.get("context", {})
    if not messages:
        return JsonResponse({"error": "messages required"}, status=400)

    try:
        context = _enrich_chat_context(context)
        from .chat_ai import get_chat_response
        response_text = get_chat_response(messages, context)
        return JsonResponse({"response": response_text})
    except Exception as exc:
        import traceback, logging
        logging.getLogger(__name__).error("chat_view error: %s", traceback.format_exc())
        return JsonResponse({"error": str(exc), "response": "일시적인 오류가 발생했습니다."}, status=500)


def _enrich_chat_context(context: dict) -> dict:
    """실시간 안전 데이터(산불·산사태·NIFOS 기상·미세먼지)를 컨텍스트에 주입."""
    context = dict(context)

    try:
        context["wildfire"] = fetch_wildfire_risk()
    except Exception:
        pass

    try:
        mountain = context.get("mountain") or {}
        region = (mountain.get("region") or "").replace("국립공원", "").strip()
        if region:
            context["landslide"] = fetch_landslide_prediction(region, "", 1, 5)
    except Exception:
        pass

    try:
        from .nifos_api import fetch_nifos_mountain_weather, fetch_nifos_fine_dust
        mountain_name = (context.get("mountain") or {}).get("name", "")
        context["nifos_weather"] = fetch_nifos_mountain_weather(mountain_name)
        context["nifos_dust"] = fetch_nifos_fine_dust()
    except Exception:
        pass

    try:
        from .airquality_api import fetch_air_quality
        mountain = context.get("mountain") or {}
        mountain_name = mountain.get("name", "")
        m_lat = mountain.get("lat") or mountain.get("course_lat")
        m_lng = mountain.get("lng") or mountain.get("course_lng")
        context["air_quality"] = fetch_air_quality(mountain_name, lat=m_lat, lng=m_lng)
    except Exception:
        pass

    return context


@require_GET
def nifos_mountain_weather(request):
    station_code = request.GET.get("station", "")
    from .nifos_api import fetch_nifos_mountain_weather
    return JsonResponse(fetch_nifos_mountain_weather(station_code), json_dumps_params={"ensure_ascii": False})


@require_GET
def air_quality(request):
    mountain = request.GET.get("mountain", "")
    from .airquality_api import fetch_air_quality
    return JsonResponse(fetch_air_quality(mountain), json_dumps_params={"ensure_ascii": False})


@require_GET
def nifos_fine_dust(request):
    station_code = request.GET.get("station", "")
    from .nifos_api import fetch_nifos_fine_dust
    return JsonResponse(fetch_nifos_fine_dust(station_code), json_dumps_params={"ensure_ascii": False})


@csrf_exempt
@require_POST
def safety_advice_view(request):
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    mountain = body.get("mountain", {})
    weather = body.get("weather", {})
    profile = body.get("profile", {})

    # Fetch sun times from mountain coordinates
    sun_data = {}
    lat = mountain.get("lat") or mountain.get("latitude")
    lng = mountain.get("lng") or mountain.get("longitude")
    if lat and lng:
        try:
            sun_data = fetch_sun_times(lat, lng) or {}
        except Exception:
            pass

    from .safety_advice_ai import generate_safety_advice
    advice = generate_safety_advice(mountain, weather, profile, sun_data)
    return JsonResponse({"advice": advice or ""})


@csrf_exempt
@require_POST
def mountain_intro_view(request):
    """산 소개문 — DB 우선 반환, 없으면 AI 생성."""
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = (body.get("name") or "").strip()
    summary = (body.get("summary") or "").strip()
    reason = (body.get("selection_reason") or "").strip()

    if not name:
        return JsonResponse({"intro": ""})

    from .models import MountainIntro
    stored = MountainIntro.objects.filter(mountain_name=name).first()
    if stored:
        return JsonResponse({"intro": stored.intro}, json_dumps_params={"ensure_ascii": False})

    # DB에 없는 경우 — AI 생성 시도 (summary가 있을 때만)
    if not summary:
        return JsonResponse({"intro": ""})

    from .mountain_intro_ai import get_or_generate_intro
    intro = get_or_generate_intro(name, summary, reason)
    return JsonResponse({"intro": intro}, json_dumps_params={"ensure_ascii": False})
