import os
import re
import sys
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "forestrx.settings")


REGION_GROUP_ALIASES = {
    "서울": ("서울", "서울특별시"),
    "부산": ("부산", "부산광역시"),
    "대구": ("대구", "대구광역시"),
    "인천": ("인천", "인천광역시"),
    "광주": ("광주", "광주광역시"),
    "대전": ("대전", "대전광역시"),
    "울산": ("울산", "울산광역시"),
    "세종": ("세종", "세종특별자치시"),
    "경기": ("경기", "경기도"),
    "강원": ("강원", "강원도", "강원특별자치도"),
    "충북": ("충북", "충청북도"),
    "충남": ("충남", "충청남도"),
    "전북": ("전북", "전라북도", "전북특별자치도"),
    "전남": ("전남", "전라남도"),
    "경북": ("경북", "경상북도"),
    "경남": ("경남", "경상남도"),
    "제주": ("제주", "제주도", "제주특별자치도"),
}


PROVINCE_BOUNDS = {
    "서울": (37.40, 37.72, 126.75, 127.20),
    "경기": (36.85, 38.35, 126.35, 127.85),
    "강원": (37.00, 38.65, 127.50, 129.40),
    "충북": (36.00, 37.35, 127.25, 128.75),
    "충남": (35.95, 37.10, 126.05, 127.65),
    "전북": (35.30, 36.20, 126.30, 127.90),
    "전남": (33.90, 35.45, 125.90, 127.65),
    "경북": (35.55, 37.60, 127.75, 130.00),
    "경남": (34.55, 35.95, 127.55, 129.40),
    "부산": (35.00, 35.40, 128.75, 129.35),
    "대구": (35.60, 36.05, 128.30, 128.80),
    "인천": (37.00, 37.85, 124.60, 126.85),
    "광주": (35.00, 35.30, 126.70, 127.05),
    "대전": (36.20, 36.50, 127.25, 127.55),
    "울산": (35.35, 35.75, 129.00, 129.50),
    "세종": (36.35, 36.75, 127.10, 127.45),
    "제주": (33.10, 33.65, 126.10, 126.95),
}


KNOWN_EXPECTED = {
    "박달산": {
        "region_group": "충북",
        "region_hint": "괴산",
        "lat": 36.836526,
        "lng": 127.920915,
        "elevation_m": 825,
    },
    "상원산": {
        "region_group": "강원",
        "region_hint": "정선",
        "lat": 37.5083548,
        "lng": 128.6767948,
        "elevation_m": 1421,
    },
    "제암산": {
        "region_group": "전남",
        "region_hint": "보성",
        "lat": 34.7097468,
        "lng": 126.9773090,
        "elevation_m": 807,
    },
}


OSM_PEAK_REFERENCES = {
    "박달산": {
        "lat": 36.836526,
        "lng": 127.920915,
        "source": "OSM Nominatim natural=peak",
        "display_name": "박달산, 장연면, 괴산군, 충청북도, 대한민국",
    },
    "상원산": {
        "lat": 37.5083548,
        "lng": 128.6767948,
        "source": "OSM Nominatim natural=peak",
        "display_name": "상원산, 북평면, 정선군, 강원특별자치도, 대한민국",
    },
    "광려산": {
        "lat": 35.187804,
        "lng": 128.478888,
        "source": "OSM Nominatim natural=peak",
        "display_name": "광려산, 내서읍, 창원시, 경상남도, 대한민국",
    },
    "신어산": {
        "lat": 35.2701011,
        "lng": 128.9204059,
        "source": "OSM Nominatim natural=peak",
        "display_name": "신어산, 김해시, 경상남도, 대한민국",
    },
    "제암산": {
        "lat": 34.7097468,
        "lng": 126.9773090,
        "source": "OSM Nominatim natural=peak",
        "display_name": "제암산, 하산리, 장흥군, 전라남도, 대한민국",
    },
}

CACHE_PATH = ROOT / "data" / "osm_peak_cache.json"


def region_group(text):
    haystack = str(text or "")
    for group, aliases in REGION_GROUP_ALIASES.items():
        if any(haystack.startswith(alias) for alias in aliases):
            return group
    for group, aliases in REGION_GROUP_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            return group
    return ""


def region_groups_in_text(text):
    haystack = str(text or "")
    found = set()
    for group, aliases in REGION_GROUP_ALIASES.items():
        for alias in aliases:
            if len(alias) >= 4 and alias in haystack:
                found.add(group)
            elif re.search(rf"{re.escape(alias)}\s*[가-힣]+(?:시|군|구|면|읍)", haystack):
                found.add(group)
    return found


def region_groups_for_field(text):
    return region_groups_in_text(text) or ({region_group(text)} if region_group(text) else set())


def extract_height(text):
    haystack = str(text or "")
    patterns = (
        r"해발\s*(?:약\s*)?((?:\d{1,3}(?:,\d{3})+|\d{2,4})(?:\.\d+)?)\s*(?:m|미터)",
        r"(?<![\d,])((?:\d{1,3}(?:,\d{3})+|\d{2,4})(?:\.\d+)?)\s*(?:m|미터)의\s*산",
    )
    for pattern in patterns:
        match = re.search(pattern, haystack, re.I)
        if match:
            return float(match.group(1).replace(",", ""))
    return None


def in_region_bounds(region, lat, lng):
    group = region_group(region)
    if not group or group not in PROVINCE_BOUNDS or lat is None or lng is None:
        return True
    min_lat, max_lat, min_lng, max_lng = PROVINCE_BOUNDS[group]
    return min_lat <= float(lat) <= max_lat and min_lng <= float(lng) <= max_lng


def mountain_key(name, region):
    compact = re.sub(r"\s+", "", f"{name}_{region or ''}")
    return compact or str(name or "")


def add_issue(issues, level, name, reason, **details):
    issues.append({"level": level, "name": name, "reason": reason, "details": details})


def haversine_m(lat1, lng1, lat2, lng2):
    radius_m = 6371000
    dlat = math.radians(float(lat2) - float(lat1))
    dlng = math.radians(float(lng2) - float(lng1))
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(float(lat1)))
        * math.cos(math.radians(float(lat2)))
        * math.sin(dlng / 2) ** 2
    )
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def coord_offset_level(distance_m):
    if distance_m >= 2000:
        return "HIGH_ERROR"
    if distance_m >= 800:
        return "ERROR"
    if distance_m >= 300:
        return "WARNING"
    return ""


def load_peak_references():
    refs = dict(OSM_PEAK_REFERENCES)
    if CACHE_PATH.exists():
        try:
            cached = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
            for name, peak in cached.items():
                if peak.get("lat") is not None and peak.get("lng") is not None:
                    refs[name] = peak
        except Exception as exc:
            print(f"[WARN] OSM peak cache 읽기 실패: {exc}")
    return refs


def fetch_osm_peak(name, region=""):
    results = fetch_nominatim(f"{name} {region}".strip())
    peak = select_peak_candidate(results, region)
    if peak:
        return peak

    # Some Korean peaks are indexed in OSM by name only. If the name-only search
    # yields a single peak in the same province, use it; otherwise leave it for
    # manual review to avoid homonymous mountain mix-ups.
    name_only_results = fetch_nominatim(name)
    return select_peak_candidate(name_only_results, region, require_unique=True)


def fetch_nominatim(query):
    params = urlencode({"format": "jsonv2", "limit": 5, "q": query})
    request = Request(
        f"https://nominatim.openstreetmap.org/search?{params}",
        headers={"User-Agent": "forest-data-verifier/1.0"},
    )
    with urlopen(request, timeout=12) as response:
        return json.loads(response.read().decode("utf-8"))


def select_peak_candidate(results, region="", require_unique=False):
    group = region_group(region)
    peaks = [item for item in results if item.get("type") == "peak" or item.get("category") == "natural"]
    if group:
        grouped = [item for item in peaks if group in item.get("display_name", "")]
        if grouped:
            peaks = grouped
        elif require_unique:
            return None
    if require_unique and len(peaks) != 1:
        return None
    if not peaks:
        return None
    item = peaks[0]
    return {
        "lat": float(item["lat"]),
        "lng": float(item["lon"]),
        "source": "OSM Nominatim natural=peak",
        "display_name": item.get("display_name", ""),
    }


def refresh_osm_peak_cache(records):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    refs = load_peak_references()
    static = [rec for rec in records if rec["source"] == "mountain_data.py" and rec["name"]]
    for rec in static:
        if rec["name"] in refs:
            continue
        try:
            peak = fetch_osm_peak(rec["name"], rec["region"])
            if peak:
                refs[rec["name"]] = peak
                print(f"[OSM] {rec['name']}: {peak['lat']}, {peak['lng']} {peak.get('display_name', '')}")
            else:
                print(f"[OSM] {rec['name']}: peak 후보 없음")
            time.sleep(1.1)
        except Exception as exc:
            print(f"[WARN] {rec['name']} OSM 조회 실패: {exc}")
    CACHE_PATH.write_text(json.dumps(refs, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return refs


def load_sources():
    from recommendations.mountain_coordinates import MOUNTAIN_COORDINATES
    from recommendations.mountain_data import MOUNTAINS
    from recommendations.management.commands.seed_mountain_descriptions import DESCRIPTIONS

    records = []
    for item in MOUNTAINS:
        records.append({
            "source": "mountain_data.py",
            "name": item.get("name", ""),
            "region": item.get("region", ""),
            "lat": item.get("lat"),
            "lng": item.get("lng"),
            "elevation_m": item.get("elevation_m"),
            "description": item.get("description", ""),
        })

    for name, coords in MOUNTAIN_COORDINATES.items():
        records.append({
            "source": "mountain_coordinates.py",
            "name": name,
            "region": coords.get("region", ""),
            "lat": coords.get("lat"),
            "lng": coords.get("lng"),
            "elevation_m": None,
            "description": "",
        })

    for name, description in DESCRIPTIONS.items():
        records.append({
            "source": "seed_mountain_descriptions.py",
            "name": name,
            "region": "",
            "lat": None,
            "lng": None,
            "elevation_m": extract_height(description),
            "description": description,
        })

    try:
        import django
        django.setup()
        from recommendations.models import MountainIntro, MountainKnowledge

        for obj in MountainKnowledge.objects.all():
            records.append({
                "source": f"db:MountainKnowledge:{obj.source}",
                "name": obj.mountain_name,
                "region": obj.region,
                "lat": obj.lat,
                "lng": obj.lng,
                "elevation_m": obj.height_m,
                "description": " ".join(part for part in (obj.summary, obj.detail) if part),
            })
        for obj in MountainIntro.objects.all():
            records.append({
                "source": "db:MountainIntro",
                "name": obj.mountain_name,
                "region": "",
                "lat": None,
                "lng": None,
                "elevation_m": extract_height(obj.intro),
                "description": obj.intro,
            })
    except Exception as exc:
        print(f"[WARN] DB 검사 건너뜀: {exc}")

    return records


def check_records(records, peak_references=None):
    peak_references = peak_references or {}
    issues = []
    by_name = defaultdict(list)
    for rec in records:
        if rec["name"]:
            by_name[rec["name"]].append(rec)

    for name, items in sorted(by_name.items()):
        regions = {item["region"] for item in items if item["region"]}
        region_sets = [region_groups_for_field(region) for region in regions]
        has_disjoint_region = any(
            left and right and not (left & right)
            for idx, left in enumerate(region_sets)
            for right in region_sets[idx + 1:]
        )
        if len(regions) > 1 and has_disjoint_region:
            add_issue(
                issues,
                "DUPLICATE_NAME_ERROR",
                name,
                "duplicate name with conflicting region",
                regions=sorted(regions),
                sources=sorted({item["source"] for item in items}),
            )

        data_items = [item for item in items if item["source"] == "mountain_data.py"]
        coord_items = [item for item in items if item["source"] == "mountain_coordinates.py"]
        seed_items = [item for item in items if item["source"] == "seed_mountain_descriptions.py"]
        for data in data_items:
            for coord in coord_items:
                data_region_groups = region_groups_for_field(data["region"])
                coord_region_groups = region_groups_for_field(coord["region"])
                if data_region_groups and coord_region_groups:
                    if not (data_region_groups & coord_region_groups):
                        add_issue(
                            issues,
                            "DATA_CONFLICT_ERROR",
                            name,
                            "mountain_data.py and mountain_coordinates.py region mismatch",
                            data_region=data["region"],
                            coordinate_region=coord["region"],
                            data_lat_lng=(data["lat"], data["lng"]),
                            coordinate_lat_lng=(coord["lat"], coord["lng"]),
                        )
                if data["lat"] and coord["lat"]:
                    if abs(float(data["lat"]) - float(coord["lat"])) > 0.15 or abs(float(data["lng"]) - float(coord["lng"])) > 0.15:
                        add_issue(
                            issues,
                            "DATA_CONFLICT_ERROR",
                            name,
                            "mountain_data.py and mountain_coordinates.py coordinate mismatch",
                            data_lat_lng=(data["lat"], data["lng"]),
                            coordinate_lat_lng=(coord["lat"], coord["lng"]),
                        )

        for rec in items:
            desc_groups = region_groups_in_text(rec["description"])
            field_group = region_group(rec["region"])
            if field_group and desc_groups and field_group not in desc_groups:
                add_issue(
                    issues,
                    "REGION_MISMATCH_ERROR",
                    name,
                    "description/region mismatch",
                    description_region=sorted(desc_groups),
                    region_field=rec["region"],
                    source=rec["source"],
                )

            desc_height = extract_height(rec["description"])
            if desc_height and rec["elevation_m"]:
                if abs(float(desc_height) - float(rec["elevation_m"])) > 120:
                    add_issue(
                        issues,
                        "DATA_CONFLICT_ERROR",
                        name,
                        "description/elevation mismatch",
                        description_elevation=desc_height,
                        elevation_m=rec["elevation_m"],
                        source=rec["source"],
                    )

            if rec["lat"] is not None and rec["lng"] is not None and rec["region"]:
                if not in_region_bounds(rec["region"], rec["lat"], rec["lng"]):
                    add_issue(
                        issues,
                        "REGION_MISMATCH_ERROR",
                        name,
                        "lat/lng outside region bounds",
                        region_field=rec["region"],
                        lat_lng=(rec["lat"], rec["lng"]),
                            source=rec["source"],
                        )

            expected = KNOWN_EXPECTED.get(name)
            if expected and rec["source"] in {"mountain_data.py", "mountain_coordinates.py"}:
                if region_group(rec["region"]) != expected["region_group"] or expected["region_hint"] not in rec["region"]:
                    add_issue(
                        issues,
                        "REGION_MISMATCH_ERROR",
                        name,
                        "known expected region mismatch",
                        region_field=rec["region"],
                        expected=f"{expected['region_group']} {expected['region_hint']}",
                        source=rec["source"],
                    )
                if rec["lat"] and rec["lng"]:
                    if abs(float(rec["lat"]) - expected["lat"]) > 0.05 or abs(float(rec["lng"]) - expected["lng"]) > 0.05:
                        add_issue(
                            issues,
                            "COORD_OFFSET_ERROR",
                            name,
                            "known expected coordinate mismatch",
                            lat_lng=(rec["lat"], rec["lng"]),
                            expected=(expected["lat"], expected["lng"]),
                            source=rec["source"],
                        )

            peak = peak_references.get(name)
            if peak and rec["source"] in {"mountain_data.py", "mountain_coordinates.py"} and rec["lat"] is not None and rec["lng"] is not None:
                distance = haversine_m(rec["lat"], rec["lng"], peak["lat"], peak["lng"])
                offset_level = coord_offset_level(distance)
                if offset_level:
                    add_issue(
                        issues,
                        "COORD_OFFSET_ERROR",
                        name,
                        "marker is far from actual mountain peak",
                        severity=offset_level,
                        current_lat_lng=(rec["lat"], rec["lng"]),
                        expected_peak_lat_lng=(peak["lat"], peak["lng"]),
                        distance_m=round(distance),
                        threshold="WARNING>=300m, ERROR>=800m, HIGH_ERROR>=2000m",
                        peak_source=peak.get("source", ""),
                        peak_display_name=peak.get("display_name", ""),
                        source=rec["source"],
                    )

        for data in data_items:
            data_groups = region_groups_in_text(data["region"]) or {region_group(data["region"])}
            data_groups = {group for group in data_groups if group}
            for seed in seed_items:
                seed_groups = region_groups_in_text(seed["description"])
                if data_groups and seed_groups and not (data_groups & seed_groups):
                    add_issue(
                        issues,
                        "REGION_MISMATCH_ERROR",
                        name,
                        "seed description/region mismatch",
                        description_region=sorted(seed_groups),
                        region_field=data["region"],
                        data_source=data["source"],
                        seed_source=seed["source"],
                    )
                if seed["elevation_m"] and data["elevation_m"]:
                    if abs(float(seed["elevation_m"]) - float(data["elevation_m"])) > 120:
                        add_issue(
                            issues,
                            "DATA_CONFLICT_ERROR",
                            name,
                            "seed description/elevation mismatch",
                            description_elevation=seed["elevation_m"],
                            elevation_m=data["elevation_m"],
                            data_source=data["source"],
                            seed_source=seed["source"],
                        )

    return issues, by_name


def print_issue(issue):
    print(f"[{issue['level']}] {issue['name']}")
    print(f"- reason: {issue['reason']}")
    for key, value in issue["details"].items():
        print(f"- {key}: {value}")
    print()


def has_conflicting_static_regions(items):
    static_regions = [
        region_groups_for_field(item["region"])
        for item in items
        if item["source"] in {"mountain_data.py", "mountain_coordinates.py"} and item["region"]
    ]
    return any(
        left and right and not (left & right)
        for idx, left in enumerate(static_regions)
        for right in static_regions[idx + 1:]
    )


def main():
    records = load_sources()
    peak_references = load_peak_references()
    if "--refresh-osm" in sys.argv:
        peak_references = refresh_osm_peak_cache(records)

    issues, by_name = check_records(records, peak_references)
    duplicate_names = {
        name: items
        for name, items in by_name.items()
        if has_conflicting_static_regions(items)
    }
    static_names = sorted({item["name"] for item in records if item["source"] == "mountain_data.py" and item["name"]})
    missing_peak_refs = [name for name in static_names if name not in peak_references]
    coord_issues = [issue for issue in issues if issue["level"] == "COORD_OFFSET_ERROR"]

    for issue in issues:
        print_issue(issue)

    print("요약")
    print(f"- 총 산 레코드 개수: {len(records)}")
    print(f"- 중복 이름 개수: {len(duplicate_names)}")
    print(f"- 의심 오류 개수: {len(issues)}")
    print(f"- 좌표 오류 개수: {len(coord_issues)}")
    print(f"- peak 기준 좌표 보유 산 개수: {len([name for name in static_names if name in peak_references])}")
    print(f"- peak 기준 수동 확인 필요 산 개수: {len(missing_peak_refs)}")
    names = sorted({issue["name"] for issue in issues})
    print(f"- 수정 필요 산 목록: {', '.join(names) if names else '없음'}")
    if coord_issues:
        print("- 좌표 오류 목록:")
        for issue in coord_issues:
            details = issue["details"]
            print(
                f"  - {issue['name']}: {details.get('severity')} "
                f"{details.get('distance_m')}m "
                f"{details.get('current_lat_lng')} -> {details.get('expected_peak_lat_lng')}"
            )
    if missing_peak_refs:
        preview = ", ".join(missing_peak_refs[:30])
        suffix = " ..." if len(missing_peak_refs) > 30 else ""
        print(f"- 수동/OSM 확인 필요 산 목록: {preview}{suffix}")
        print("- OSM 갱신 실행: python verify_mountain_data.py --refresh-osm")
    if duplicate_names:
        print("- 중복 이름 목록:")
        for name, items in sorted(duplicate_names.items()):
            compact = sorted({f"{item['source']}:{item['region']}:{item['lat']},{item['lng']}" for item in items})
            print(f"  - {name}: {compact}")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
