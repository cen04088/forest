from .loaders import DATA_LINK_FILE_PATH, KEY_FILE_PATH, TRAIL_CSV_PATH, load_public_service_key


def data_source_status():
    service_key_loaded = bool(load_public_service_key())
    return {
        "service_key_loaded": service_key_loaded,
        "files": {
            "trail_csv": {
                "configured": str(TRAIL_CSV_PATH.name),
                "exists": TRAIL_CSV_PATH.exists(),
            },
            "key_txt": {
                "configured": str(KEY_FILE_PATH.name),
                "exists": KEY_FILE_PATH.exists(),
            },
            "data_links": {
                "configured": str(DATA_LINK_FILE_PATH.relative_to(DATA_LINK_FILE_PATH.parents[1])),
                "exists": DATA_LINK_FILE_PATH.exists(),
            },
        },
        "connected_sources": [
            {
                "id": "trail_courses",
                "name": "National park trail courses",
                "status": "connected" if TRAIL_CSV_PATH.exists() else "fallback",
                "endpoint": "local_csv",
            },
            {
                "id": "weather_nowcast",
                "name": "KMA ultra short nowcast",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst",
            },
            {
                "id": "sun_times",
                "name": "KASI rise/set time",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getLCRiseSetInfo",
            },
            {
                "id": "wildfire",
                "name": "Forest fire risk forecast",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "https://apis.data.go.kr/1400377/forestPointV2/forestPointListGeongugSearchV2",
            },
            {
                "id": "forest_spatial",
                "name": "Forest trail spatial data",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://api.forest.go.kr/openapi/service/trailInfoService/getforestspatialdataservice",
            },
            {
                "id": "mountain_story",
                "name": "Forest mountain story",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice",
            },
            {
                "id": "landslide",
                "name": "Forest landslide prediction",
                "status": "ready" if service_key_loaded else "missing_key",
                "endpoint": "http://apis.data.go.kr/1400000/predictionInfoService/predictionInfoList",
            },
        ],
        "mock_first_sources": [
            "DEM/slope raster",
            "mountain accident history",
            "route-level risk polygons",
            "Safe Link moving track events",
            "B2G hotspot statistics",
        ],
    }
