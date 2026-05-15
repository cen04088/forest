import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

from .loaders import load_kma_api_hub_key, load_public_service_key


KMA_MOUNTAIN_WEATHER_URL = "https://apihub.kma.go.kr/api/typ08/getMountainWeather"
DEFAULT_MOUNTAIN_NUM = "5"
MOUNTAIN_NUMBERS = {
    "북한산": "5",
}
CATEGORY_MAP = {
    "TMP": "temperature_c",
    "TMN": "min_temperature_c",
    "TMX": "max_temperature_c",
    "PCP": "precipitation",
    "SNO": "snow",
    "POP": "precipitation_probability",
    "WSD": "wind_speed_ms",
    "REH": "humidity_pct",
    "SKY": "sky",
    "PTY": "precipitation_type",
    "SRT": "sunrise",
    "SST": "sunset",
}


def fetch_mountain_weather(mountain_name="", mountain_num=None, base_date="", base_time="", timeout=8):
    auth_keys = [key for key in (load_kma_api_hub_key(), load_public_service_key()) if key]
    auth_keys = list(dict.fromkeys(auth_keys))
    if not auth_keys:
        return {"ok": False, "source": "kma_mountain_weather", "error": "Missing KMA API Hub auth key", "items": []}

    resolved_num = str(mountain_num or mountain_num_for_name(mountain_name) or DEFAULT_MOUNTAIN_NUM)
    date, time = resolve_base_datetime(base_date, base_time)
    last_result = None
    for auth_key in auth_keys:
        result = _cached_fetch_mountain_weather(resolved_num, date, time, auth_key, timeout)
        last_result = result
        if result.get("ok") or "401" not in result.get("error", ""):
            return result
    return last_result or {"ok": False, "source": "kma_mountain_weather", "error": "KMA mountain weather request failed", "items": []}


@lru_cache(maxsize=128)
def _cached_fetch_mountain_weather(mountain_num, base_date, base_time, auth_key, timeout):
    query = {
        "mountainNum": mountain_num,
        "base_date": base_date,
        "base_time": base_time,
        "authKey": auth_key,
    }
    url = f"{KMA_MOUNTAIN_WEATHER_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:
        return {
            "ok": False,
            "source": "kma_mountain_weather",
            "error": f"KMA mountain weather request failed: {exc}",
            "items": [],
        }

    return parse_mountain_weather_response(body, mountain_num, base_date, base_time)


def resolve_base_datetime(base_date="", base_time="", now=None):
    if base_date and base_time:
        return str(base_date), str(base_time).zfill(4)

    current = now or datetime.now(ZoneInfo("Asia/Seoul"))
    slots = [2, 5, 8, 11, 14, 17, 20, 23]
    hour = max((slot for slot in slots if current.hour >= slot), default=23)
    if current.hour < 2:
        current -= timedelta(days=1)
    return current.strftime("%Y%m%d"), f"{hour:02d}00"


def mountain_num_for_name(mountain_name):
    normalized = str(mountain_name or "").replace(" ", "")
    for name, number in MOUNTAIN_NUMBERS.items():
        if name.replace(" ", "") in normalized:
            return number
    return None


def parse_mountain_weather_response(body, mountain_num="", base_date="", base_time=""):
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return {"ok": False, "source": "kma_mountain_weather", "error": "Empty KMA mountain weather response", "items": []}

    if text[0] in "[{":
        return parse_mountain_weather_json(text, mountain_num, base_date, base_time)
    if text[0] == "<":
        return parse_mountain_weather_xml(text.encode("utf-8"), mountain_num, base_date, base_time)
    return parse_mountain_weather_text(text, mountain_num, base_date, base_time)


def parse_mountain_weather_json(text, mountain_num, base_date, base_time):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"ok": False, "source": "kma_mountain_weather", "error": "Invalid KMA mountain weather JSON", "items": []}

    items = extract_items_from_json(payload)
    return summarize_items(items, mountain_num, base_date, base_time)


def parse_mountain_weather_xml(body, mountain_num, base_date, base_time):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {"ok": False, "source": "kma_mountain_weather", "error": "Invalid KMA mountain weather XML", "items": []}

    items = []
    for item in root.findall(".//item"):
        items.append({child.tag: (child.text or "").strip() for child in item})
    return summarize_items(items, mountain_num, base_date, base_time)


def parse_mountain_weather_text(text, mountain_num, base_date, base_time):
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if len(lines) < 2:
        return {"ok": False, "source": "kma_mountain_weather", "error": text[:160], "items": []}

    header = [part.strip() for part in lines[0].replace(",", " ").split()]
    items = []
    for line in lines[1:]:
        values = [part.strip() for part in line.replace(",", " ").split()]
        if len(values) == len(header):
            items.append(dict(zip(header, values)))
    return summarize_items(items, mountain_num, base_date, base_time)


def extract_items_from_json(payload):
    if isinstance(payload, list):
        return payload
    for path in (
        ("response", "body", "items", "item"),
        ("response", "result", "items"),
        ("items",),
        ("data",),
    ):
        value = payload
        for key in path:
            value = value.get(key, {}) if isinstance(value, dict) else {}
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
    return []


def summarize_items(items, mountain_num, base_date, base_time):
    normalized = [normalize_item(item) for item in items if isinstance(item, dict)]
    latest = {}
    station_name = ""
    lat = None
    lng = None
    altitude_m = None

    for item in normalized:
        station_name = station_name or item.get("station_name", "")
        lat = lat if lat is not None else item.get("lat")
        lng = lng if lng is not None else item.get("lng")
        altitude_m = altitude_m if altitude_m is not None else item.get("altitude_m")
        key = CATEGORY_MAP.get(item.get("category"))
        if key and key not in latest:
            latest[key] = item.get("value")

    weather = {
        "ok": bool(normalized),
        "source": "kma_mountain_weather",
        "mountain_num": str(mountain_num),
        "base_date": base_date,
        "base_time": base_time,
        "station_name": station_name,
        "lat": lat,
        "lng": lng,
        "altitude_m": altitude_m,
        "items": normalized[:80],
        **latest,
    }
    coerce_weather_numbers(weather)
    return weather


def normalize_item(item):
    return {
        "mountain_num": get_value(item, "mountainNum", "mountain_num"),
        "base_date": get_value(item, "baseDate", "base_date"),
        "base_time": get_value(item, "baseTime", "base_time"),
        "category": get_value(item, "category"),
        "forecast_date": get_value(item, "fcstDate", "forecast_date"),
        "forecast_time": get_value(item, "fcstTime", "forecast_time"),
        "value": get_value(item, "fcstValue", "value"),
        "nx": to_int(get_value(item, "nx")),
        "ny": to_int(get_value(item, "ny")),
        "lat": to_float(get_value(item, "lat")),
        "lng": to_float(get_value(item, "lon", "lng")),
        "altitude_m": to_int(get_value(item, "alt")),
        "station_name": get_value(item, "stn_nm", "station_name"),
    }


def get_value(item, *keys):
    lowered = {str(key).lower(): value for key, value in item.items()}
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value).strip()
        value = lowered.get(str(key).lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def coerce_weather_numbers(weather):
    for key in ("temperature_c", "min_temperature_c", "max_temperature_c", "wind_speed_ms"):
        weather[key] = to_float(weather.get(key), weather.get(key))
    weather["humidity_pct"] = to_float(weather.get("humidity_pct"), weather.get("humidity_pct"))
    weather["precipitation_probability"] = to_int(weather.get("precipitation_probability"), weather.get("precipitation_probability"))
    weather["rainfall_mm"] = parse_precipitation_mm(weather.get("precipitation"))


def parse_precipitation_mm(value):
    if value in (None, "", "강수없음", "없음"):
        return 0
    text = str(value)
    if "mm" in text:
        text = text.replace("mm", "")
    try:
        return float(text)
    except ValueError:
        return 0


def to_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def to_int(value, default=None):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default
