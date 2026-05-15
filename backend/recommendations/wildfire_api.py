import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from functools import lru_cache

from .loaders import load_public_service_key


WILDFIRE_NATIONWIDE_URL = "http://apis.data.go.kr/1400377/forestPointV2/forestPointListGeongugSearchV2"


def fetch_wildfire_risk(timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {"risk": "low", "source": "mock"}

    return _cached_fetch_wildfire_risk(service_key, timeout) or {"risk": "low", "source": "mock"}


@lru_cache(maxsize=32)
def _cached_fetch_wildfire_risk(service_key, timeout):
    query = {
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 1,
        "type": "json",
    }
    url = f"{WILDFIRE_NATIONWIDE_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception:
        return None

    return parse_wildfire_risk_response(body)


def parse_wildfire_risk_response(body):
    text = body.decode("utf-8", errors="replace").strip()
    if text.startswith("{") or text.startswith("["):
        return parse_wildfire_risk_json(text)
    return parse_wildfire_risk_xml(body)


def parse_wildfire_risk_json(text):
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    item = first_item(payload)
    if not item:
        return None

    mean_index = parse_int(value_of(item, "meanavg", "meanAvg", "mean"))
    max_index = parse_int(value_of(item, "maxi", "max", "maxIndex"))
    risk = wildfire_risk_label(max(mean_index, max_index))

    return {
        "risk": risk,
        "mean_index": mean_index,
        "max_index": max_index,
        "analysis_time": value_of(item, "analdate", "analDate"),
        "region": value_of(item, "doname", "doName", "region") or "전국",
        "source": "산림청_산불위험예보정보",
    }


def parse_wildfire_risk_xml(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return None

    result_code = text_of(root, ".//resultCode")
    if result_code not in ("00", "0", ""):
        return None

    item = root.find(".//item")
    if item is None:
        return None

    mean_index = parse_int(text_of(item, "meanavg"))
    max_index = parse_int(text_of(item, "maxi"))
    risk = wildfire_risk_label(max(mean_index, max_index))

    return {
        "risk": risk,
        "mean_index": mean_index,
        "max_index": max_index,
        "analysis_time": text_of(item, "analdate"),
        "region": text_of(item, "doname") or "전국",
        "source": "산림청_산불위험예보",
    }


def wildfire_risk_label(index):
    if index >= 86:
        return "very_high"
    if index >= 66:
        return "high"
    if index >= 51:
        return "medium"
    return "low"


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def parse_int(value):
    try:
        return int(float(str(value or "0").replace(",", "").strip()))
    except ValueError:
        return 0


def first_item(payload):
    if isinstance(payload, list):
        return payload[0] if payload else None
    if not isinstance(payload, dict):
        return None

    candidates = [
        payload.get("response", {}).get("body", {}).get("items", {}).get("item"),
        payload.get("response", {}).get("body", {}).get("items"),
        payload.get("items"),
        payload.get("item"),
        payload.get("data"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate[0] if candidate else None
        if isinstance(candidate, dict):
            return candidate
    return None


def value_of(item, *keys):
    lowered = {str(key).lower(): value for key, value in item.items()}
    for key in keys:
        value = item.get(key)
        if value not in (None, ""):
            return str(value).strip()
        value = lowered.get(str(key).lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""
