"""
OSM 한국 전체 산 정상 데이터로 mountain_coordinates.py 좌표를 교정합니다.
안전 장치: 기존 좌표에서 MAX_DIST_DEG(0.25도 ≈ 25km) 이내 후보만 사용.

실행: python fix_coords_from_osm.py [--dry-run]
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
KOREA_BBOX = "33.0,124.0,38.7,132.0"
MAX_DIST_DEG = 0.16   # 이 거리 이상이면 다른 산으로 간주하고 무시 (~18km)
MIN_DIST_DEG = 0.001  # 이미 정확한 경우 건너뜀

QUERY = f"""[out:json][timeout:120];
(
  node["natural"="peak"]({KOREA_BBOX});
  node["natural"="hill"]({KOREA_BBOX});
);
out body;"""


def fetch_osm_peaks():
    print("OSM 한국 산 정상 데이터 조회 중...")
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(
        OVERPASS_URL, data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "MountainCoordFixer/1.0 (educational non-commercial)",
        }
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=150) as resp:
                result = json.loads(resp.read())
            elems = result.get("elements", [])
            print(f"  조회 완료: {len(elems)}개 노드")
            return elems
        except Exception as e:
            print(f"  시도 {attempt+1} 실패: {e}")
            if attempt < 2:
                time.sleep(10)
    return []


def build_lookup(elements):
    """이름 → [(lat, lng, ele)] 목록 구축."""
    lookup: dict[str, list] = {}
    for el in elements:
        tags = el.get("tags", {})
        for key in ("name", "name:ko"):
            name = (tags.get(key) or "").strip()
            if name:
                try:
                    ele = int(float(tags.get("ele", 0) or 0))
                except (ValueError, TypeError):
                    ele = 0
                lookup.setdefault(name, []).append((el["lat"], el["lon"], ele))
    return lookup


def dist(lat1, lng1, lat2, lng2):
    return ((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5


def pick_nearest_high(candidates, ref_lat, ref_lng):
    """기준 좌표에서 MAX_DIST_DEG 이내 후보 중 고도 최고값 반환."""
    nearby = [(lat, lng, ele) for lat, lng, ele in candidates
              if dist(lat, lng, ref_lat, ref_lng) <= MAX_DIST_DEG]
    if not nearby:
        return None, None
    with_ele = [(lat, lng, ele) for lat, lng, ele in nearby if ele > 0]
    if with_ele:
        best = max(with_ele, key=lambda x: x[2])
    else:
        best = min(nearby, key=lambda x: dist(x[0], x[1], ref_lat, ref_lng))
    return best[0], best[1]


def main():
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        print("[DRY-RUN - 파일 수정 안 함]")

    elements = fetch_osm_peaks()
    if not elements:
        print("데이터 없음 - 중단")
        return

    lookup = build_lookup(elements)
    print(f"  고유 이름: {len(lookup)}개")

    coord_file = Path(__file__).parent / "recommendations" / "mountain_coordinates.py"
    text = coord_file.read_text(encoding="utf-8")

    # 현재 좌표 가져오기
    from recommendations.mountain_coordinates import MOUNTAIN_COORDINATES

    updated = skipped_far = skipped_close = not_found = 0
    changes = []

    for name, data in MOUNTAIN_COORDINATES.items():
        old_lat, old_lng = data["lat"], data["lng"]

        if name not in lookup:
            not_found += 1
            continue

        new_lat, new_lng = pick_nearest_high(lookup[name], old_lat, old_lng)
        if new_lat is None:
            skipped_far += 1
            print(f"  SKIP(너무 멀음) [{name}] 기존=({old_lat:.4f},{old_lng:.4f})")
            continue

        d = dist(new_lat, new_lng, old_lat, old_lng)
        if d < MIN_DIST_DEG:
            skipped_close += 1
            continue

        print(f"  UPDATE [{name}] ({old_lat:.5f},{old_lng:.5f}) -> ({new_lat:.5f},{new_lng:.5f})  diff={d:.4f}")
        changes.append((name, old_lat, old_lng, new_lat, new_lng))

        if not dry_run:
            # 정밀 교체: 해당 이름의 lat/lng 값만 교체
            old_str = f'"lat": {old_lat}'
            new_str = f'"lat": {new_lat}'
            # 이름이 포함된 줄 근처에서만 교체하기 위해 블록 패턴 사용
            pattern = re.compile(
                r'("' + re.escape(name) + r'"[^{]*\{"lat":\s*)' +
                re.escape(str(old_lat)) +
                r'(\s*,\s*"lng":\s*)' + re.escape(str(old_lng)),
            )
            new_text, n = re.subn(
                pattern,
                lambda m: f'{m.group(1)}{new_lat}{m.group(2)}{new_lng}',
                text
            )
            if n > 0:
                text = new_text
                updated += 1
            else:
                # fallback: 단순 문자열 교체
                old_block = f'"lat": {old_lat}, "lng": {old_lng}'
                new_block = f'"lat": {new_lat}, "lng": {new_lng}'
                if old_block in text:
                    text = text.replace(old_block, new_block, 1)
                    updated += 1
                else:
                    print(f"    -> 패턴 매칭 실패, 수동 확인 필요: {name}")

    if not dry_run and updated > 0:
        coord_file.write_text(text, encoding="utf-8")
        print(f"\n파일 저장 완료: {coord_file}")

    print(f"\n=== 완료 ===")
    print(f"  업데이트: {updated}개")
    print(f"  이미 정확: {skipped_close}개")
    print(f"  25km 초과(다른 산): {skipped_far}개")
    print(f"  OSM 미매칭: {not_found}개")


if __name__ == "__main__":
    main()
