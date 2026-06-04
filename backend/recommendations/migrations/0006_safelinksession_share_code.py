import random

from django.db import migrations, models

_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gen(used):
    for _ in range(50):
        code = "".join(random.choices(_CODE_CHARS, k=6))
        if code not in used:
            return code
    return "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=8))


def populate_codes(apps, schema_editor):
    SafeLinkSession = apps.get_model("recommendations", "SafeLinkSession")
    used = set(SafeLinkSession.objects.exclude(share_code="").values_list("share_code", flat=True))
    for session in SafeLinkSession.objects.filter(share_code=""):
        code = _gen(used)
        used.add(code)
        session.share_code = code
        session.save(update_fields=["share_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("recommendations", "0005_locationlog"),
    ]

    operations = [
        # 1단계: unique 없이 컬럼만 추가
        migrations.AddField(
            model_name="safelinksession",
            name="share_code",
            field=models.CharField(blank=True, max_length=6, default=""),
            preserve_default=False,
        ),
        # 2단계: 기존 행에 고유 코드 채우기
        migrations.RunPython(populate_codes, migrations.RunPython.noop),
        # 3단계: unique 제약 추가
        migrations.AlterField(
            model_name="safelinksession",
            name="share_code",
            field=models.CharField(blank=True, max_length=6, unique=True),
        ),
    ]
