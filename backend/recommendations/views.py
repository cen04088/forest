import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .data_sources import data_source_status
from .forest_api import fetch_forest_spatial_data, safe_public_response
from .landslide_api import fetch_landslide_prediction
from .loaders import load_public_service_key, load_public_trail_courses, load_disaster_risk_zones
from .mountain_coordinates import MOUNTAIN_COORDINATES
from .mountain_story_api import fetch_mountain_story
from .services import recommend_courses
from .sun_api import fetch_sun_times
from .weather_api import fetch_current_weather
from .mountain_weather_api import fetch_mountain_weather
from .wildfire_api import fetch_wildfire_risk
from .vworld_api import fetch_vworld_trails
from . import safe_links as safe_link_store


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
def data_sources(request):
    return JsonResponse(data_source_status(), json_dumps_params={"ensure_ascii": False})


@require_GET
def courses(request):
    return JsonResponse({"courses": load_public_trail_courses()})


@require_GET
def forest_spatial(request):
    mountain_name = request.GET.get("mountain", "")
    page_no = request.GET.get("page", 1)
    num_of_rows = request.GET.get("size", 10)
    result = fetch_forest_spatial_data(mountain_name, page_no, num_of_rows)
    return JsonResponse(safe_public_response(result), json_dumps_params={"ensure_ascii": False})


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
    lat = float(request.GET.get("lat", 37.5665))
    lng = float(request.GET.get("lng", 126.978))
    cache_key = f"weather:{round(lat, 2)}:{round(lng, 2)}"
    cached = cache.get(cache_key)
    if cached:
        return JsonResponse(cached, json_dumps_params={"ensure_ascii": False})
    result = fetch_current_weather(lat, lng)
    cache.set(cache_key, result, 600)
    return JsonResponse(result, json_dumps_params={"ensure_ascii": False})


@require_GET
def mountain_weather(request):
    mountain_name = request.GET.get("mountain", "")
    mountain_num = request.GET.get("mountainNum", "")
    base_date = request.GET.get("base_date", "")
    base_time = request.GET.get("base_time", "")
    return JsonResponse(
        fetch_mountain_weather(mountain_name, mountain_num or None, base_date, base_time),
        json_dumps_params={"ensure_ascii": False},
    )


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


@csrf_exempt
@require_POST
def recommendations(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)

    return JsonResponse(recommend_courses(payload))


@require_GET
def disaster_zones(request):
    mountain = request.GET.get("mountain", "").strip()
    zones = load_disaster_risk_zones()
    if mountain:
        from .loaders import normalize_search_text
        needle = normalize_search_text(mountain)
        zones = [z for z in zones if needle in z.get("search_text", "")]
    return JsonResponse({"zones": zones[:30]}, json_dumps_params={"ensure_ascii": False})


@csrf_exempt
def safe_link_create(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        body = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    course = body.get("course", {})
    session = safe_link_store.create(course)
    return JsonResponse({"id": session["id"]}, status=201)


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
