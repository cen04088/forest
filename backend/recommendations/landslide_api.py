import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from functools import lru_cache

from .loaders import load_public_service_key


LANDSLIDE_PREDICTION_URL = "http://apis.data.go.kr/1400000/predictionInfoService/predictionInfoList"


def fetch_landslide_prediction(sgg="", forecast_name="", page_no=1, num_of_rows=10, timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {
            "ok": False,
            "error": "public service key is missing",
            "items": [],
            "source": "mock",
        }

    return _cached_fetch_landslide_prediction(
        sgg.strip(),
        forecast_name.strip(),
        int(page_no),
        int(num_of_rows),
        service_key,
        timeout,
    )


@lru_cache(maxsize=128)
def _cached_fetch_landslide_prediction(sgg, forecast_name, page_no, num_of_rows, service_key, timeout):
    query = {
        "ServiceKey": service_key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "_type": "json",
    }
    if sgg:
        query["sgg"] = sgg
    if forecast_name:
        query["lndslFrcstNm"] = forecast_name

    url = f"{LANDSLIDE_PREDICTION_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:
        return {
            "ok": False,
            "error": f"landslide prediction API request failed: {exc}",
            "items": [],
            "source": "fallback",
        }

    parsed = parse_landslide_prediction_json(body)
    if parsed is not None:
        return parsed
    return parse_landslide_prediction_xml(body)


def parse_landslide_prediction_json(body):
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None

    response = payload.get("response", {})
    header = response.get("header", {})
    body_payload = response.get("body", {})
    items_payload = body_payload.get("items", {})
    raw_items = items_payload.get("item", []) if isinstance(items_payload, dict) else []
    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    return {
        "ok": str(header.get("resultCode", "")) in ("00", "0", ""),
        "result_code": str(header.get("resultCode", "")),
        "result_msg": header.get("resultMsg", ""),
        "total_count": parse_int(body_payload.get("totalCount")),
        "items": [normalize_landslide_item(item) for item in raw_items],
        "source": "forest_landslide_prediction",
    }


def parse_landslide_prediction_xml(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {
            "ok": False,
            "error": "landslide prediction API parse failed",
            "items": [],
            "source": "fallback",
        }

    result_code = text_of(root, ".//resultCode")
    items = []
    for item in root.findall(".//item"):
        items.append(
            normalize_landslide_item(
                {
                    "lndslFrcstNm": text_of(item, "lndslFrcstNm"),
                    "sgg": text_of(item, "sgg"),
                    "prctnInfoAnlssDt": text_of(item, "prctnInfoAnlssDt"),
                }
            )
        )

    return {
        "ok": result_code in ("00", "0", ""),
        "result_code": result_code,
        "result_msg": text_of(root, ".//resultMsg"),
        "total_count": parse_int(text_of(root, ".//totalCount")),
        "items": items,
        "source": "forest_landslide_prediction",
    }


def normalize_landslide_item(item):
    forecast_name = item.get("lndslFrcstNm") or item.get("forecastName") or ""
    return {
        "forecast_name": forecast_name,
        "risk": landslide_risk_label(forecast_name),
        "sigungu": item.get("sgg", ""),
        "analysis_time": item.get("prctnInfoAnlssDt", ""),
    }


def landslide_risk_label(forecast_name):
    if "경보" in str(forecast_name):
        return "danger"
    if "주의" in str(forecast_name):
        return "caution"
    return "low"


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def parse_int(value):
    try:
        return int(float(str(value or "0").replace(",", "").strip()))
    except ValueError:
        return 0
