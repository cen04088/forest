import json
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


MOUNTAIN_WEATHER_BASE_HOURS = (2, 5, 8, 11, 14, 17, 20, 23)


def resolve_base_datetime(now=None):
    current = now or datetime.now(ZoneInfo("Asia/Seoul"))
    available_at = current - timedelta(hours=1)
    for hour in reversed(MOUNTAIN_WEATHER_BASE_HOURS):
        if available_at.hour >= hour:
            base = available_at.replace(hour=hour, minute=0, second=0, microsecond=0)
            return base.strftime("%Y%m%d"), base.strftime("%H00")
    previous = (available_at - timedelta(days=1)).replace(hour=23, minute=0, second=0, microsecond=0)
    return previous.strftime("%Y%m%d"), previous.strftime("%H00")


def parse_mountain_weather_response(body: bytes, mountain_num="", base_date="", base_time="") -> dict:
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "Invalid mountain weather JSON", "items": []}

    items = (
        payload.get("response", {}).get("body", {}).get("items", {}).get("item")
        or payload.get("items")
        or []
    )
    if isinstance(items, dict):
        items = [items]

    values = {}
    first = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        if not first:
            first = item
        category = item.get("category")
        if category:
            values[category] = item.get("fcstValue")

    if not values:
        return {"ok": False, "error": "No mountain weather items", "items": []}

    return {
        "ok": True,
        "source": "mountain_weather",
        "mountain_num": mountain_num,
        "base_date": base_date,
        "base_time": base_time,
        "temperature_c": _float(values.get("TMP")),
        "rainfall_mm": _rainfall(values.get("PCP")),
        "wind_speed_ms": _float(values.get("WSD")),
        "lat": _float(first.get("lat")),
        "lng": _float(first.get("lon") or first.get("lng")),
        "altitude_m": _float(first.get("alt")),
        "station_name": first.get("stn_nm") or first.get("station_name") or "",
        "items": items,
    }


def _float(value, default=None):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def _rainfall(value):
    text = str(value or "").strip()
    if text in {"", "-", "no precipitation"}:
        return 0.0
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0
