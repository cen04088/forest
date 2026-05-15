import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from functools import lru_cache
from math import cos, floor, log, pow, radians, sin, sqrt, tan
from zoneinfo import ZoneInfo

from .data import MOCK_WEATHER
from .loaders import load_public_service_key
from .mountain_weather_api import fetch_mountain_weather
from .sun_api import fetch_sun_times
from .wildfire_api import fetch_wildfire_risk


KMA_ULTRA_SHORT_NOWCAST_URL = (
    "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
)


def fetch_current_weather(lat, lng, timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {**MOCK_WEATHER, "source": "mock"}

    nx, ny = lat_lng_to_kma_grid(lat, lng)
    base_date, base_time = kma_nowcast_base_datetime()
    result = _cached_fetch_current_weather(nx, ny, base_date, base_time, service_key, timeout)
    weather = result if result else {**MOCK_WEATHER, "source": "mock"}
    sun_times = fetch_sun_times(lat, lng, timeout=timeout)
    if sun_times.get("sunset"):
        weather["sunset"] = sun_times["sunset"]
        weather["sunrise"] = sun_times.get("sunrise", "")
        weather["civil_twilight_evening"] = sun_times.get("civil_twilight_evening", "")
        weather["sun_source"] = sun_times.get("source", "")

    wildfire = fetch_wildfire_risk(timeout=timeout)
    weather["wildfire_risk"] = wildfire.get("risk", weather.get("wildfire_risk", "low"))
    weather["wildfire"] = wildfire
    return weather


def merge_mountain_weather(weather, mountain_name="", mountain_num=None, timeout=8):
    mountain_weather = fetch_mountain_weather(mountain_name, mountain_num, timeout=timeout)
    if not mountain_weather.get("ok"):
        weather["mountain_weather"] = mountain_weather
        return weather

    merged = {**weather}
    for key in ("temperature_c", "rainfall_mm", "wind_speed_ms", "humidity_pct", "sunrise", "sunset"):
        value = mountain_weather.get(key)
        if value not in (None, ""):
            merged[key] = value
    merged["mountain_weather"] = mountain_weather
    merged["source"] = f"{weather.get('source', 'weather')}+kma_mountain_weather"
    return merged


@lru_cache(maxsize=256)
def _cached_fetch_current_weather(nx, ny, base_date, base_time, service_key, timeout):
    query = {
        "ServiceKey": service_key,
        "pageNo": 1,
        "numOfRows": 20,
        "dataType": "XML",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }
    url = f"{KMA_ULTRA_SHORT_NOWCAST_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception:
        return None

    return parse_kma_nowcast_xml(body, nx=nx, ny=ny, base_date=base_date, base_time=base_time)


def parse_kma_nowcast_xml(body, nx=None, ny=None, base_date="", base_time=""):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None

    result_code = text_of(root, ".//resultCode")
    if result_code not in ("00", "0", ""):
        return None

    values = {}
    for item in root.findall(".//item"):
        category = text_of(item, "category")
        value = text_of(item, "obsrValue")
        values[category] = value

    if not values:
        return None

    rainfall = parse_float(values.get("RN1"), 0)
    return {
        "temperature_c": parse_float(values.get("T1H"), MOCK_WEATHER["temperature_c"]),
        "rainfall_mm": rainfall,
        "wind_speed_ms": parse_float(values.get("WSD"), MOCK_WEATHER["wind_speed_ms"]),
        "humidity_pct": parse_float(values.get("REH"), MOCK_WEATHER["humidity_pct"]),
        "precipitation_type": precipitation_label(values.get("PTY")),
        "sunset": MOCK_WEATHER["sunset"],
        "wildfire_risk": MOCK_WEATHER["wildfire_risk"],
        "source": "기상청_초단기실황",
        "base_date": base_date,
        "base_time": base_time,
        "grid": {"nx": nx, "ny": ny},
    }


def kma_nowcast_base_datetime(now=None):
    current = now or datetime.now(ZoneInfo("Asia/Seoul"))
    if current.minute < 45:
        current -= timedelta(hours=1)
    return current.strftime("%Y%m%d"), current.strftime("%H00")


def lat_lng_to_kma_grid(lat, lng):
    re = 6371.00877
    grid = 5.0
    slat1 = radians(30.0)
    slat2 = radians(60.0)
    olon = radians(126.0)
    olat = radians(38.0)
    xo = 43
    yo = 136

    sn = tan(3.141592653589793 * 0.25 + slat2 * 0.5) / tan(3.141592653589793 * 0.25 + slat1 * 0.5)
    sn = log(cos(slat1) / cos(slat2)) / log(sn)
    sf = tan(3.141592653589793 * 0.25 + slat1 * 0.5)
    sf = pow(sf, sn) * cos(slat1) / sn
    ro = tan(3.141592653589793 * 0.25 + olat * 0.5)
    ro = re / grid * sf / pow(ro, sn)

    ra = tan(3.141592653589793 * 0.25 + radians(lat) * 0.5)
    ra = re / grid * sf / pow(ra, sn)
    theta = radians(lng) - olon
    if theta > 3.141592653589793:
        theta -= 2.0 * 3.141592653589793
    if theta < -3.141592653589793:
        theta += 2.0 * 3.141592653589793
    theta *= sn

    x = floor(ra * sin(theta) + xo + 0.5)
    y = floor(ro - ra * cos(theta) + yo + 0.5)
    return x, y


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def parse_float(value, default):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def precipitation_label(value):
    labels = {
        "0": "없음",
        "1": "비",
        "2": "비/눈",
        "3": "눈",
        "5": "빗방울",
        "6": "빗방울눈날림",
        "7": "눈날림",
    }
    return labels.get(str(value or "0"), "없음")
