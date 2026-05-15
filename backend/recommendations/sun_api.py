import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from .loaders import load_public_service_key


RISE_SET_URL = "https://apis.data.go.kr/B090041/openapi/service/RiseSetInfoService/getLCRiseSetInfo"


def fetch_sun_times(lat, lng, locdate=None, timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {}

    date = locdate or datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
    return _cached_fetch_sun_times(round(float(lat), 4), round(float(lng), 4), date, service_key, timeout)


@lru_cache(maxsize=256)
def _cached_fetch_sun_times(lat, lng, locdate, service_key, timeout):
    query = {
        "ServiceKey": service_key,
        "locdate": locdate,
        "longitude": lng,
        "latitude": lat,
        "dnYn": "Y",
    }
    url = f"{RISE_SET_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception:
        return {}

    return parse_sun_times_xml(body)


def parse_sun_times_xml(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {}

    result_code = text_of(root, ".//resultCode")
    if result_code not in ("00", "0", ""):
        return {}

    item = root.find(".//item")
    if item is None:
        return {}

    return {
        "sunrise": format_hhmm(text_of(item, "sunrise")),
        "sunset": format_hhmm(text_of(item, "sunset")),
        "civil_twilight_evening": format_hhmm(text_of(item, "civile")),
        "location": text_of(item, "locdate"),
        "source": "한국천문연구원_출몰시각",
    }


def format_hhmm(value):
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if len(digits) < 4:
        return ""
    digits = digits[-4:]
    return f"{digits[:2]}:{digits[2:]}"


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""
