from django.core.management.base import BaseCommand

from recommendations.models import MountainTags
from recommendations.mountain_tags import MOUNTAIN_TAGS


class Command(BaseCommand):
    help = "MOUNTAIN_TAGS 딕셔너리를 DB(MountainTags)에 저장합니다."

    def handle(self, *args, **options):
        created = updated = 0
        for name, tags in MOUNTAIN_TAGS.items():
            obj, is_new = MountainTags.objects.update_or_create(
                mountain_name=name,
                defaults={"tags": tags},
            )
            if is_new:
                created += 1
            else:
                updated += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"완료: {created}개 생성 / {updated}개 갱신 (총 {created + updated}개)"
            )
        )
