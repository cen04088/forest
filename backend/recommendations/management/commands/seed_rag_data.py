"""
RAG 데이터를 DB에 사전 수집합니다.

  산림청 산정보 서비스 (cultureInfoService2)  → MountainKnowledge
  산림청 산이야기 서비스 (getforeststoryservice) → MountainKnowledge
  국립공원 탐방로 CSV                          → TrailCourse
  국립공원 재난위험지구 CSV                     → DisasterRiskZone

사용법:
    python manage.py seed_rag_data            # 전체 실행
    python manage.py seed_rag_data --skip-api # CSV만 (API 호출 없이)
    python manage.py seed_rag_data --skip-csv # API만
    python manage.py seed_rag_data --force    # 기존 데이터 덮어쓰기
"""
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import json

from django.core.management.base import BaseCommand

from recommendations.loaders import (
    load_public_service_key,
    load_public_trail_courses,
    load_disaster_risk_zones,
)
from recommendations.models import MountainKnowledge, TrailCourse, DisasterRiskZone

CULTURE_INFO_URL = "https://apis.data.go.kr/1400000/service/cultureInfoService2"
MOUNTAIN_STORY_URL = "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice"
PAGE_SIZE = 100
REQUEST_DELAY = 0.5


class Command(BaseCommand):
    help = "산림청 API + 국립공원 CSV 데이터를 DB에 적재 (RAG용)"

    def add_arguments(self, parser):
        parser.add_argument("--skip-api", action="store_true", help="API 수집 건너뜀")
        parser.add_argument("--skip-csv", action="store_true", help="CSV 이식 건너뜀")
        parser.add_argument("--force", action="store_true", help="기존 레코드 덮어쓰기")

    def handle(self, *args, **options):
        force = options["force"]

        if not options["skip_api"]:
            service_key = load_public_service_key()
            if not service_key:
                self.stdout.write(self.style.ERROR("PUBLIC_SERVICE_KEY 미설정 -API 수집 건너뜀"))
            else:
                self._fetch_mountain_story(service_key, force)

        if not options["skip_csv"]:
            self._seed_trail_courses(force)
            self._seed_disaster_zones(force)

        self.stdout.write(self.style.SUCCESS("\n=== seed_rag_data 완료 ==="))
        self.stdout.write(f"  MountainKnowledge: {MountainKnowledge.objects.count()}개")
        self.stdout.write(f"  TrailCourse:       {TrailCourse.objects.count()}개")
        self.stdout.write(f"  DisasterRiskZone:  {DisasterRiskZone.objects.count()}개")

    # ── 산림청 산정보 (cultureInfoService2) ─────────────────────────────────

    def _fetch_culture_info(self, service_key, force):
        self.stdout.write("\n[1/2] 산림청 산정보 서비스 수집 중...")
        page, total_saved, total_skipped = 1, 0, 0

        while True:
            items, is_last = self._request_culture_page(service_key, page)
            if items is None:
                self.stdout.write(self.style.ERROR(f"  페이지 {page} 요청 실패 -중단"))
                break

            for item in items:
                name = _text(item, "mntnNm") or _text(item, "mntnnm") or _text(item, "name")
                if not name:
                    continue
                summary = _clean(_text(item, "mntnDesc") or _text(item, "desc") or _text(item, "summary"))
                defaults = {
                    "height_m": _int(_text(item, "mntnHigh") or _text(item, "height")),
                    "region": _text(item, "mntnAddress") or _text(item, "address") or _text(item, "location"),
                    "summary": summary[:2000],
                    "detail": _clean(_text(item, "mntnDtlDesc") or _text(item, "detail"))[:2000],
                }
                obj, created = MountainKnowledge.objects.get_or_create(
                    mountain_name=name, source="culture_info", defaults=defaults
                )
                if not created and force:
                    for k, v in defaults.items():
                        setattr(obj, k, v)
                    obj.save()
                    created = True
                if created:
                    total_saved += 1
                else:
                    total_skipped += 1

            self.stdout.write(f"  페이지 {page} 처리 (저장:{total_saved} 건너뜀:{total_skipped})")
            if is_last:
                break
            page += 1
            time.sleep(REQUEST_DELAY)

        self.stdout.write(self.style.SUCCESS(f"  완료 -저장 {total_saved}개 / 건너뜀 {total_skipped}개"))

    def _request_culture_page(self, service_key, page_no):
        query = {
            "ServiceKey": service_key,
            "pageNo": page_no,
            "numOfRows": PAGE_SIZE,
            "_type": "json",
        }
        url = f"{CULTURE_INFO_URL}?{urllib.parse.urlencode(query, safe='%')}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                body = resp.read()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  HTTP 오류: {exc}"))
            return None, True

        # JSON 우선 시도
        try:
            payload = json.loads(body.decode("utf-8", errors="replace"))
            body_payload = payload.get("response", {}).get("body", {})
            items_raw = body_payload.get("items", {})
            if isinstance(items_raw, dict):
                items_raw = items_raw.get("item", [])
            if isinstance(items_raw, dict):
                items_raw = [items_raw]
            total_count = int(body_payload.get("totalCount", 0))
            is_last = (page_no * PAGE_SIZE) >= total_count
            return items_raw or [], is_last
        except (json.JSONDecodeError, AttributeError):
            pass

        # XML fallback
        try:
            root = ET.fromstring(body)
            items_raw = [
                {child.tag: child.text for child in item}
                for item in root.findall(".//item")
            ]
            total_count = int(root.findtext(".//totalCount") or 0)
            is_last = (page_no * PAGE_SIZE) >= total_count
            return items_raw, is_last
        except ET.ParseError:
            return None, True

    # ── 산림청 산이야기 (getforeststoryservice) ──────────────────────────────

    def _fetch_mountain_story(self, service_key, force):
        self.stdout.write("\n[2/2] 산림청 산이야기 서비스 수집 중...")
        page, total_saved, total_skipped = 1, 0, 0

        while True:
            items, is_last = self._request_story_page(service_key, page)
            if items is None:
                self.stdout.write(self.style.ERROR(f"  페이지 {page} 요청 실패 -중단"))
                break

            for item in items:
                name = _text(item, "mntnnm") or _text(item, "Mntiname")
                if not name:
                    continue
                defaults = {
                    "height_m": _int(_text(item, "mntninfohght") or _text(item, "mntihigh")),
                    "region": _text(item, "mntninfopoflc") or _text(item, "mntiadd"),
                    "summary": _clean(_text(item, "mntninfodscrt") or _text(item, "mntisummary"))[:2000],
                    "detail": _clean(_text(item, "mntninfodtlinfocont") or _text(item, "mntidetails"))[:2000],
                    "selection_reason": _clean(_text(item, "hndfmsmtnslctnrson") or _text(item, "mntitop"))[:1000],
                }
                obj, created = MountainKnowledge.objects.get_or_create(
                    mountain_name=name, source="mountain_story", defaults=defaults
                )
                if not created and force:
                    for k, v in defaults.items():
                        setattr(obj, k, v)
                    obj.save()
                    created = True
                if created:
                    total_saved += 1
                else:
                    total_skipped += 1

            self.stdout.write(f"  페이지 {page} 처리 (저장:{total_saved} 건너뜀:{total_skipped})")
            if is_last:
                break
            page += 1
            time.sleep(REQUEST_DELAY)

        self.stdout.write(self.style.SUCCESS(f"  완료 -저장 {total_saved}개 / 건너뜀 {total_skipped}개"))

    def _request_story_page(self, service_key, page_no):
        query = {
            "ServiceKey": service_key,
            "pageNo": page_no,
            "numOfRows": PAGE_SIZE,
        }
        url = f"{MOUNTAIN_STORY_URL}?{urllib.parse.urlencode(query, safe='%')}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                body = resp.read()
        except Exception as exc:
            self.stdout.write(self.style.WARNING(f"  HTTP 오류: {exc}"))
            return None, True

        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return None, True

        result_code = (root.findtext(".//resultCode") or "").strip()
        if result_code not in ("00", "0", ""):
            msg = root.findtext(".//resultMsg") or "오류"
            self.stdout.write(self.style.ERROR(f"  API 오류 {result_code}: {msg}"))
            return None, True

        items_raw = [
            {child.tag: (child.text or "").strip() for child in item}
            for item in root.findall(".//item")
        ]
        total_count = int(root.findtext(".//totalCount") or 0)
        is_last = (page_no * PAGE_SIZE) >= total_count
        return items_raw, is_last

    # ── 국립공원 탐방로 CSV ──────────────────────────────────────────────────

    def _seed_trail_courses(self, force):
        self.stdout.write("\n[3/4] 국립공원 탐방로 CSV → DB 이식 중...")
        courses = load_public_trail_courses()
        saved = skipped = 0
        for course in courses:
            course_id = str(course.get("id", ""))
            if not course_id:
                continue
            defaults = {
                "mountain": course.get("mountain", ""),
                "name": course.get("name", ""),
                "region": course.get("region", ""),
                "difficulty": course.get("difficulty", ""),
                "distance_km": course.get("distance_km"),
                "duration_min": course.get("duration_min"),
                "elevation_gain_m": course.get("elevation_gain_m"),
                "lat": course.get("lat"),
                "lng": course.get("lng"),
                "crowding": course.get("crowding", 0.4),
                "highlights": course.get("highlights", []),
                "source": course.get("source", ""),
            }
            obj, created = TrailCourse.objects.get_or_create(course_id=course_id, defaults=defaults)
            if not created and force:
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.save()
                created = True
            if created:
                saved += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"  완료 -저장 {saved}개 / 건너뜀 {skipped}개"))

    # ── 국립공원 재난위험지구 CSV ────────────────────────────────────────────

    def _seed_disaster_zones(self, force):
        self.stdout.write("\n[4/4] 재난위험지구 CSV → DB 이식 중...")
        zones = load_disaster_risk_zones()
        saved = skipped = 0
        for zone in zones:
            zone_id = str(zone.get("id", ""))
            if not zone_id:
                continue
            defaults = {
                "district": zone.get("district", ""),
                "location": zone.get("location", ""),
                "facility": zone.get("facility", ""),
                "risk_factor": zone.get("risk_factor", ""),
                "evacuation_place": zone.get("evacuation_place", ""),
                "search_text": zone.get("search_text", ""),
            }
            obj, created = DisasterRiskZone.objects.get_or_create(zone_id=zone_id, defaults=defaults)
            if not created and force:
                for k, v in defaults.items():
                    setattr(obj, k, v)
                obj.save()
                created = True
            if created:
                saved += 1
            else:
                skipped += 1

        self.stdout.write(self.style.SUCCESS(f"  완료 -저장 {saved}개 / 건너뜀 {skipped}개"))


# ── 유틸 ─────────────────────────────────────────────────────────────────────

def _text(item, key):
    if isinstance(item, dict):
        return (item.get(key) or "").strip()
    return ""


def _int(value):
    try:
        return int(float(str(value or "0").replace(",", "").strip()))
    except (ValueError, TypeError):
        return None


def _clean(value):
    import html as html_mod, re
    text = html_mod.unescape(str(value or ""))
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()
