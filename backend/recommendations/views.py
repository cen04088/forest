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
def mountain_story(request):
    mountain_name = request.GET.get("mountain", "")
    page_no = request.GET.get("page", 1)
    num_of_rows = request.GET.get("size", 5)
    return JsonResponse(
        fetch_mountain_story(mountain_name, page_no, num_of_rows),
        json_dumps_params={"ensure_ascii": False},
    )


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
        aq = fetch_air_quality(mountain)
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
    return JsonResponse({"mountains": MOUNTAINS}, json_dumps_params={"ensure_ascii": False})


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

    return JsonResponse(recommend_mountains(payload), json_dumps_params={"ensure_ascii": False})


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
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    messages = body.get("messages", [])
    context = body.get("context", {})
    if not messages:
        return JsonResponse({"error": "messages required"}, status=400)

    context = _enrich_chat_context(context)
    from .chat_ai import get_chat_response
    return JsonResponse({"response": get_chat_response(messages, context)})


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
        mountain_name = (context.get("mountain") or {}).get("name", "")
        context["air_quality"] = fetch_air_quality(mountain_name)
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
    """산 소개문 AI 변환 — DB에 저장하여 재사용."""
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    name = (body.get("name") or "").strip()
    summary = (body.get("summary") or "").strip()
    reason = (body.get("selection_reason") or "").strip()

    if not name or not summary:
        return JsonResponse({"intro": ""})

    from .mountain_intro_ai import get_or_generate_intro
    intro = get_or_generate_intro(name, summary, reason)
    return JsonResponse({"intro": intro}, json_dumps_params={"ensure_ascii": False})
