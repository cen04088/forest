"""
77개 산의 소개문을 미리 Gemini로 변환해 DB에 저장합니다.

사용법:
    python manage.py seed_mountain_intros           # 미생성 산만 처리
    python manage.py seed_mountain_intros --force   # 전체 재생성
    python manage.py seed_mountain_intros --dry-run # 산 목록만 출력 (API 호출 없음)
"""
import time

from django.core.management.base import BaseCommand

from recommendations.mountain_data import MOUNTAINS
from recommendations.mountain_story_api import fetch_mountain_story
from recommendations.mountain_intro_ai import _generate
from recommendations.models import MountainIntro


class Command(BaseCommand):
    help = "77개 산 소개문을 Gemini로 변환 후 DB 저장"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="이미 저장된 항목도 재생성")
        parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 목록만 출력")
        parser.add_argument("--delay", type=float, default=1.2, help="요청 간 딜레이(초), 기본 1.2")

    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]
        delay = options["delay"]

        existing = set(MountainIntro.objects.values_list("mountain_name", flat=True))
        total = len(MOUNTAINS)
        skipped = done = failed = 0

        self.stdout.write(self.style.SUCCESS(f"총 {total}개 산 처리 시작"))

        for i, m in enumerate(MOUNTAINS, 1):
            name = m["name"]
            prefix = f"[{i:02d}/{total}] {name}"

            if dry_run:
                status = "✓ 저장됨" if name in existing else "○ 미생성"
                self.stdout.write(f"{prefix}  {status}")
                continue

            if not force and name in existing:
                self.stdout.write(f"{prefix}  → 건너뜀 (이미 저장)")
                skipped += 1
                continue

            # 1) 산림청 스토리 조회
            raw_summary = m.get("description", "")
            selection_reason = ""
            try:
                story_resp = fetch_mountain_story(name, page_no=1, num_of_rows=1)
                item = (story_resp.get("items") or [None])[0]
                if item:
                    raw_summary = item.get("summary") or raw_summary
                    selection_reason = item.get("selection_reason") or ""
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"{prefix}  스토리 API 실패: {e}"))

            if not raw_summary:
                self.stdout.write(self.style.WARNING(f"{prefix}  원문 없음 — 건너뜀"))
                skipped += 1
                continue

            # 2) Gemini 변환
            try:
                intro = _generate(name, raw_summary, selection_reason)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"{prefix}  생성 실패: {e}"))
                failed += 1
                time.sleep(delay)
                continue

            if not intro:
                self.stdout.write(self.style.WARNING(f"{prefix}  빈 응답 — 건너뜀"))
                failed += 1
                time.sleep(delay)
                continue

            # 3) DB 저장
            MountainIntro.objects.update_or_create(
                mountain_name=name,
                defaults={"intro": intro, "raw_summary": raw_summary[:1000]},
            )
            done += 1
            self.stdout.write(f"{prefix}  ✓ 저장 완료")
            self.stdout.write(f"    {intro[:80]}{'...' if len(intro) > 80 else ''}")

            time.sleep(delay)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"\n완료 — 생성: {done}개  건너뜀: {skipped}개  실패: {failed}개"
            ))
