import os

from .loaders import (
    DATA_LINK_FILE_PATH,
    DISASTER_RISK_CSV_PATH,
    KEY_FILE_PATH,
    KMA_API_HUB_KEY_FILE_PATH,
    TRAIL_CSV_PATH,
    VWORLD_KEY_FILE_PATH,
    load_public_service_key,
    load_kma_api_hub_key,
    load_vworld_api_key,
)
from .local_road_api import ROAD_SHP_PATH


def data_source_status():
    service_key_loaded = bool(load_public_service_key())
    kma_api_hub_key_loaded = bool(load_kma_api_hub_key())
    vworld_key_loaded = bool(load_vworld_api_key())
    nifos_key_loaded = bool(os.environ.get("NIFOS_API_KEY", "").strip())
    return {
        "service_key_loaded": service_key_loaded,
        "files": {
            "trail_csv": {
                "configured": str(TRAIL_CSV_PATH.name),
                "exists": TRAIL_CSV_PATH.exists(),
            },
            "disaster_risk_csv": {
                "configured": str(DISASTER_RISK_CSV_PATH.name),
                "exists": DISASTER_RISK_CSV_PATH.exists(),
            },
            "key_txt": {
                "configured": str(KEY_FILE_PATH.name),
                "exists": KEY_FILE_PATH.exists(),
            },
            "data_links": {
                "configured": str(DATA_LINK_FILE_PATH.relative_to(DATA_LINK_FILE_PATH.parents[1])),
                "exists": DATA_LINK_FILE_PATH.exists(),
            },
            "vworld_key": {
                "configured": str(VWORLD_KEY_FILE_PATH.name),
                "exists": VWORLD_KEY_FILE_PATH.exists(),
            },
            "kma_api_hub_key": {
                "configured": str(KMA_API_HUB_KEY_FILE_PATH.name),
                "exists": KMA_API_HUB_KEY_FILE_PATH.exists(),
            },
            "local_road_shp": {
                "configured": "road/WG_MT_WAY/WG_MT_WAY.shp",
                "exists": ROAD_SHP_PATH.exists(),
            },
        },
        "connected_sources": [
            {
                "id": "trail_courses",
                "name": "National park trail courses",
                "status": "connected" if TRAIL_CSV_PATH.exists() else "fallback",
                "endpoint": "local_csv",
                "provider": "국립공원공단",
            },
            {
                "id": "disaster_risk_zones",
                "name": "National park disaster risk zones",
                "status": "connected" if DISASTER_RISK_CSV_PATH.exists() else "missing_file",
                "endpoint": "local_csv",
                "provider": "국립공원공단",
            },
            {
                "id": "local_road_shp",
                "name": "Local hiking trail geometry SHP",
                "status": "connected" if ROAD_SHP_PATH.exists() else "missing_file",
                "endpoint": "road/WG_MT_WAY/WG_MT_WAY.shp",
                "provider": "산림청",
            },
            {
                "id": "vworld_trails",
                "name": "VWorld hiking trail geometry",
                "status": "ready" if vworld_key_loaded else "missing_key",
                "endpoint": "https://api.vworld.kr/req/data",
                "provider": "국토교통부",
            },
            {
                "id": "kma_mountain_weather",
                "name": "KMA mountain weather forecast",
                "status": "ready" if kma_api_hub_key_loaded else "missing_key",
                "endpoint": "https://apihub.kma.go.kr/api/typ08/getMountainWeather",
                "provider": "기상청",
            },
            {
                "id": "weather_nowcast",
                "name": "KMA ultra short nowcast",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst",
                "provider": "기상청",
            },
            {
                "id": "sun_times",
                "name": "KASI rise/set time",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getLCRiseSetInfo",
                "provider": "한국천문연구원",
            },
            {
                "id": "wildfire",
                "name": "Forest fire risk forecast",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/1400377/forestPointV2/forestPointListGeongugSearchV2",
                "provider": "국립산림과학원",
            },
            {
                "id": "forest_spatial",
                "name": "Forest trail spatial data",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://api.forest.go.kr/openapi/service/trailInfoService/getforestspatialdataservice",
                "provider": "산림청",
            },
            {
                "id": "mountain_story",
                "name": "Forest mountain story",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice",
                "provider": "산림청",
            },
            {
                "id": "landslide",
                "name": "Forest landslide prediction",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://apis.data.go.kr/1400000/predictionInfoService/predictionInfoList",
                "provider": "산림청",
            },
            {
                "id": "nifos_mountain_weather",
                "name": "NIFOS 산악기상시스템 (실시간 관측)",
                "status": "ready" if nifos_key_loaded else "missing_key",
                "endpoint": "http://mtweather.nifos.go.kr/openapi/obs/current",
                "provider": "국립산림과학원",
            },
            {
                "id": "nifos_fine_dust",
                "name": "NIFOS 산림 미세먼지 관측시스템",
                "status": "ready" if nifos_key_loaded else "missing_key",
                "endpoint": "http://aican.nifos.go.kr/openapi/dust/current",
                "provider": "국립산림과학원",
            },
        ],
        "mock_first_sources": [
            "DEM/slope raster",
            "mountain accident history",
            "route-level risk polygons",
            "Safe Link location sharing events",
            "B2G hotspot statistics",
        ],
    }
