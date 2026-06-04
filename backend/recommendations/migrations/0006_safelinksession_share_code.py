from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recommendations", "0005_locationlog"),
    ]

    operations = [
        migrations.AddField(
            model_name="safelinksession",
            name="share_code",
            field=models.CharField(blank=True, max_length=6, unique=True, default=""),
            preserve_default=False,
        ),
    ]
