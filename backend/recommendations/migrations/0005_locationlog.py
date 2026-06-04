from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("recommendations", "0004_authtoken_expires_at_safelinksession"),
    ]

    operations = [
        migrations.CreateModel(
            name="LocationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("lat", models.FloatField()),
                ("lng", models.FloatField()),
                ("recorded_at", models.IntegerField()),
                ("session", models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name="location_logs",
                    to="recommendations.safelinksession",
                )),
            ],
            options={"db_table": "recommendations_locationlog", "ordering": ["recorded_at"]},
        ),
    ]
