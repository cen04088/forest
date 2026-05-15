import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .data_sources import data_source_status
from .forest_api import fetch_forest_spatial_data, safe_public_response
from .landslide_api import fetch_landslide_prediction
from .loaders import load_public_service_key, load_public_trail_courses
from .mountain_coordinates import MOUNTAIN_COORDINATES
from .mountain_story_api import fetch_mountain_story
from .services import recommend_courses
from .sun_api import fetch_sun_times
from .weather_api import fetch_current_weather
from .mountain_weather_api import fetch_mountain_weather
from .wildfire_api import fetch_wildfire_risk
from .vworld_api import fetch_vworld_trails


@require_GET
def health(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "ForestRx API",
            "public_trail_courses": len(load_public_trail_courses()),
            "public_service_key_loaded": bool(load_public_service_key()),
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
    lat = float(request.GET.get("lat", 37.5665))
    lng = float(request.GET.get("lng", 126.978))
    return JsonResponse(fetch_current_weather(lat, lng), json_dumps_params={"ensure_ascii": False})


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
