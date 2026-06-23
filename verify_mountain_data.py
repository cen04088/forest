import os
import re
import sys
from collections import defaultdict
from pathlib import Path


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
    "경북": (35.55, 37.60, 128.00, 130.00),
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
}


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


def check_records(records):
    issues = []
    by_name = defaultdict(list)
    for rec in records:
        if rec["name"]:
            by_name[rec["name"]].append(rec)

    for name, items in sorted(by_name.items()):
        regions = {item["region"] for item in items if item["region"]}
        region_groups = {region_group(region) for region in regions if region_group(region)}
        if len(regions) > 1 and len(region_groups) > 1:
            add_issue(
                issues,
                "ERROR",
                name,
                "duplicate name with conflicting region",
                regions=sorted(regions),
                sources=sorted({item["source"] for item in items}),
            )

        data_items = [item for item in items if item["source"] == "mountain_data.py"]
        coord_items = [item for item in items if item["source"] == "mountain_coordinates.py"]
        for data in data_items:
            for coord in coord_items:
                if region_group(data["region"]) and region_group(coord["region"]):
                    if region_group(data["region"]) != region_group(coord["region"]):
                        add_issue(
                            issues,
                            "ERROR",
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
                            "ERROR",
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
                    "ERROR",
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
                        "ERROR",
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
                        "ERROR",
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
                        "ERROR",
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
                            "ERROR",
                            name,
                            "known expected coordinate mismatch",
                            lat_lng=(rec["lat"], rec["lng"]),
                            expected=(expected["lat"], expected["lng"]),
                            source=rec["source"],
                        )

    return issues, by_name


def print_issue(issue):
    print(f"[{issue['level']}] {issue['name']}")
    print(f"- reason: {issue['reason']}")
    for key, value in issue["details"].items():
        print(f"- {key}: {value}")
    print()


def main():
    records = load_sources()
    issues, by_name = check_records(records)
    duplicate_names = {
        name: items
        for name, items in by_name.items()
        if len({mountain_key(item["name"], item["region"]) for item in items if item["source"] in {"mountain_data.py", "mountain_coordinates.py"}}) > 1
    }

    for issue in issues:
        print_issue(issue)

    print("요약")
    print(f"- 총 산 레코드 개수: {len(records)}")
    print(f"- 중복 이름 개수: {len(duplicate_names)}")
    print(f"- 의심 오류 개수: {len(issues)}")
    names = sorted({issue["name"] for issue in issues})
    print(f"- 수정 필요 산 목록: {', '.join(names) if names else '없음'}")
    if duplicate_names:
        print("- 중복 이름 목록:")
        for name, items in sorted(duplicate_names.items()):
            compact = sorted({f"{item['source']}:{item['region']}:{item['lat']},{item['lng']}" for item in items})
            print(f"  - {name}: {compact}")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
