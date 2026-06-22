"""
MountainKnowledge 레코드에 VWorld Search API로 좌표를 채워 넣습니다.

사용법:
    python manage.py geocode_mountains            # 좌표 없는 것만
    python manage.py geocode_mountains --force    # 전체 재조회
    python manage.py geocode_mountains --limit 50 # 최대 50개만
"""
import time
import json
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand

from recommendations.loaders import load_vworld_api_key
from recommendations.models import MountainKnowledge
from recommendations.mountain_coordinates import MOUNTAIN_COORDINATES

VWORLD_SEARCH_URL = "https://api.vworld.kr/req/search"
REQUEST_DELAY = 0.3  # 초당 ~3건


class Command(BaseCommand):
    help = "VWorld Search API로 MountainKnowledge 좌표를 자동 채움"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="이미 좌표 있는 것도 재조회")
        parser.add_argument("--limit", type=int, default=0, help="최대 처리 수 (0=전체)")

    def handle(self, *args, **options):
        force = options["force"]
        limit = options["limit"]

        api_key = load_vworld_api_key()
        if not api_key:
            self.stdout.write(self.style.ERROR("VWORLD_API_KEY 미설정 - 중단"))
            return

        # 대상 선정: source 중복 제거를 위해 mountain_name 기준으로 deduplicate
        qs = MountainKnowledge.objects.all()
        if not force:
            qs = qs.filter(lat__isnull=True)

        # 산 이름별로 하나의 대표 레코드만 처리 (중복 저장 방지)
        seen_names = set()
        targets = []
        for obj in qs.order_by("mountain_name"):
            if obj.mountain_name not in seen_names:
                seen_names.add(obj.mountain_name)
                targets.append(obj.mountain_name)
        if limit:
            targets = targets[:limit]

        total = len(targets)
        self.stdout.write(f"지오코딩 대상: {total}개 산")

        ok_count = fail_count = skip_count = preset_count = 0

        for i, name in enumerate(targets, 1):
            # 기존 MOUNTAIN_COORDINATES 우선 사용 (API 호출 절약)
            preset = MOUNTAIN_COORDINATES.get(name)
            if preset:
                lat, lng = preset["lat"], preset["lng"]
                MountainKnowledge.objects.filter(mountain_name=name).update(lat=lat, lng=lng)
                preset_count += 1
                if i % 50 == 0 or i == total:
                    self.stdout.write(f"  [{i}/{total}] preset {name}: {lat}, {lng}")
                continue

            # VWorld Search API 호출
            lat, lng = _search_vworld(name, api_key)
            if lat is not None:
                MountainKnowledge.objects.filter(mountain_name=name).update(lat=lat, lng=lng)
                ok_count += 1
                self.stdout.write(f"  [{i}/{total}] OK  {name}: {lat:.5f}, {lng:.5f}")
            else:
                fail_count += 1
                if fail_count <= 20 or i == total:
                    self.stdout.write(self.style.WARNING(f"  [{i}/{total}] FAIL {name}"))

            time.sleep(REQUEST_DELAY)

        with_coords = MountainKnowledge.objects.exclude(lat__isnull=True).values("mountain_name").distinct().count()
        self.stdout.write(self.style.SUCCESS(
            f"\n=== 완료 ===\n"
            f"  preset: {preset_count}개  VWorld OK: {ok_count}개  실패: {fail_count}개\n"
            f"  좌표 보유 산 수: {with_coords}개"
        ))


def _search_vworld(mountain_name: str, api_key: str) -> tuple[float | None, float | None]:
    """VWorld Search API로 산 이름 → (lat, lng) 반환. 실패 시 (None, None)."""
    query = {
        "service": "search",
        "request": "search",
        "version": "2.0",
        "crs": "EPSG:4326",
        "size": "5",
        "page": "1",
        "query": mountain_name,
        "type": "PLACE",
        "category": "MT",
        "format": "json",
        "errorFormat": "json",
        "key": api_key,
    }
    url = f"{VWORLD_SEARCH_URL}?{urllib.parse.urlencode(query)}"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            body = resp.read()
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        return None, None

    response = payload.get("response", {})
    if response.get("status") != "OK":
        return None, None

    items = response.get("result", {}).get("items", [])
    if not items:
        return None, None

    # 이름이 정확히 일치하는 항목 우선
    best = None
    for item in items:
        title = item.get("title", "").replace(" ", "")
        if title == mountain_name:
            best = item
            break
    if best is None:
        best = items[0]

    point = best.get("point", {})
    try:
        lng = float(point.get("x", 0))
        lat = float(point.get("y", 0))
        if 33.0 <= lat <= 38.7 and 124.0 <= lng <= 132.0:
            return lat, lng
    except (TypeError, ValueError):
        pass
    return None, None
