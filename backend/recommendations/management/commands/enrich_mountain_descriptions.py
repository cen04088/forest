"""
python manage.py enrich_mountain_descriptions

Gemini(GMS_KEY)로 148개 산 설명을 3~4문장으로 재생성해 MountainIntro 테이블에 저장.
--force  이미 300자 이상인 항목도 재생성
--dry    DB 저장 없이 생성 결과만 출력
"""

import os
import time

from django.core.management.base import BaseCommand

from recommendations.models import MountainIntro
from recommendations.mountain_data import MOUNTAINS


PROMPT_TMPL = """아래 산에 대해 등산객을 위한 소개문을 작성해줘.

산 이름: {name}
지역: {region}
해발: {elevation_m}m
난이도: {diff}
특징: {highlights}

작성 조건:
- 정확히 3~4개의 완성된 문장 (번호·불릿 없음)
- 위치와 높이 → 대표 경관 또는 문화유산 → 추천 포인트 순서로 자연스럽게 연결
- 생동감 있는 문체, 200~350자 분량
- 문장이 중간에 끊기지 않도록 완결된 형태로 작성
- 한국어만 사용"""

DIFF_LABEL = {"easy": "초급", "medium": "중급", "hard": "고급"}


def _call_gemini(prompt: str) -> str | None:
    gms_key = os.environ.get("GMS_KEY", "").strip()
    api_key = gms_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None
    try:
        from google import genai
        from google.genai import types

        kwargs = {"api_key": api_key}
        if gms_key:
            kwargs["http_options"] = {
                "base_url": "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/"
            }
        client = genai.Client(**kwargs)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=400,
                temperature=0.7,
            ),
        )
        return response.text.strip()
    except Exception as e:
        return None


class Command(BaseCommand):
    help = "Gemini로 산 소개문 3~4문장 재생성 후 DB 저장"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="300자 이상도 재생성")
        parser.add_argument("--dry", action="store_true", help="DB 저장 없이 출력만")
        parser.add_argument("--name", type=str, help="특정 산만 처리 (예: --name 북한산)")

    def handle(self, *args, **options):
        force = options["force"]
        dry = options["dry"]
        target_name = options.get("name")

        existing = {
            obj.mountain_name: obj.intro
            for obj in MountainIntro.objects.all()
        }

        mountains = MOUNTAINS
        if target_name:
            mountains = [m for m in mountains if m["name"] == target_name]

        created = updated = skipped = failed = 0

        for m in mountains:
            name = m["name"]
            current = existing.get(name, "")

            # 이미 충분히 길면 건너뜀 (--force 없는 경우)
            if not force and len(current) >= 300:
                skipped += 1
                self.stdout.write(f"  SKIP  {name} ({len(current)}자)")
                continue

            prompt = PROMPT_TMPL.format(
                name=name,
                region=m.get("region", ""),
                elevation_m=m.get("elevation_m", ""),
                diff=DIFF_LABEL.get(m.get("difficulty", ""), ""),
                highlights=", ".join(m.get("highlights", [])) or "자연 경관",
            )

            intro = _call_gemini(prompt)
            if not intro:
                failed += 1
                self.stdout.write(self.style.ERROR(f"  FAIL  {name}"))
                continue

            if dry:
                self.stdout.write(f"\n=== {name} ===\n{intro}\n")
                continue

            obj, is_new = MountainIntro.objects.update_or_create(
                mountain_name=name,
                defaults={"intro": intro},
            )
            if is_new:
                created += 1
            else:
                updated += 1

            flag = "NEW" if is_new else "UPD"
            self.stdout.write(f"  {flag}  {name} ({len(intro)}자)")

            # GMS 레이트 리밋 방지
            time.sleep(0.5)

        if not dry:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n완료: 신규 {created}개 / 업데이트 {updated}개 / 건너뜀 {skipped}개 / 실패 {failed}개"
                )
            )
