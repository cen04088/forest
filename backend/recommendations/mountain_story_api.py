import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from functools import lru_cache

from .loaders import load_public_service_key


MOUNTAIN_STORY_URL = "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice"


def fetch_mountain_story(mountain_name="", page_no=1, num_of_rows=5, timeout=8):
    service_key = load_public_service_key()
    if not service_key:
        return {
            "ok": False,
            "error": "public service key is missing",
            "items": [],
            "source": "mock",
        }

    return _cached_fetch_mountain_story(
        mountain_name.strip(),
        int(page_no),
        int(num_of_rows),
        service_key,
        timeout,
    )


@lru_cache(maxsize=128)
def _cached_fetch_mountain_story(mountain_name, page_no, num_of_rows, service_key, timeout):
    query = {
        "ServiceKey": service_key,
        "pageNo": page_no,
        "numOfRows": num_of_rows,
    }
    if mountain_name:
        query["mntnNm"] = mountain_name

    url = f"{MOUNTAIN_STORY_URL}?{urllib.parse.urlencode(query, safe='%')}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            body = response.read()
    except Exception as exc:
        return {
            "ok": False,
            "error": f"mountain story API request failed: {exc}",
            "items": [],
            "source": "fallback",
        }

    return parse_mountain_story_xml(body)


def parse_mountain_story_xml(body):
    try:
        root = ET.fromstring(body)
    except ET.ParseError:
        return {
            "ok": False,
            "error": "mountain story API XML parse failed",
            "items": [],
        }

    result_code = text_of(root, ".//resultCode")
    total_count = parse_int(text_of(root, ".//totalCount"))
    items = []

    for item in root.findall(".//item"):
        items.append(
            {
                "mountain_id": text_of(item, "mntnid") or text_of(item, "mntlistno"),
                "mountain": text_of(item, "mntnnm") or text_of(item, "Mntiname"),
                "height_m": parse_int(text_of(item, "mntninfohght") or text_of(item, "mntihigh")),
                "address": text_of(item, "mntninfopoflc") or text_of(item, "mntiadd"),
                "manager": text_of(item, "mntninfomngmemnbdnm") or text_of(item, "mntiadmin"),
                "summary": clean_html(text_of(item, "mntninfodscrt") or text_of(item, "mntisummary")),
                "detail": clean_html(text_of(item, "mntninfodtlinfocont") or text_of(item, "mntidetails")),
                "selection_reason": clean_html(text_of(item, "hndfmsmtnslctnrson") or text_of(item, "mntitop")),
            }
        )

    return {
        "ok": result_code in ("00", "0", ""),
        "result_code": result_code,
        "total_count": total_count,
        "items": items,
        "source": "forest_mountain_story",
    }


def clean_html(value):
    text = re.sub(r"<br\s*/?>", "\n", str(value or ""), flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def text_of(node, path):
    found = node.find(path)
    return (found.text or "").strip() if found is not None else ""


def parse_int(value):
    try:
        return int(float(str(value or "0").replace(",", "").strip()))
    except ValueError:
        return 0
