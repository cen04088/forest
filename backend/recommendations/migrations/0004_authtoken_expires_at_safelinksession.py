import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("recommendations", "0003_emergencycontact_hikingrecord_favoritecourse"),
    ]

    operations = [
        migrations.AddField(
            model_name="authtoken",
            name="expires_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="SafeLinkSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)),
                ("course_name", models.CharField(blank=True, max_length=200)),
                ("mountain", models.CharField(blank=True, max_length=100)),
                ("safety_label", models.CharField(blank=True, max_length=20)),
                ("safety_decision", models.CharField(blank=True, max_length=30)),
                ("risk_factors", models.JSONField(default=list)),
                ("distance_km", models.FloatField(blank=True, null=True)),
                ("duration_min", models.IntegerField(default=0)),
                ("course_lat", models.FloatField(blank=True, null=True)),
                ("course_lng", models.FloatField(blank=True, null=True)),
                ("current_lat", models.FloatField(blank=True, null=True)),
                ("current_lng", models.FloatField(blank=True, null=True)),
                ("location_ts", models.IntegerField(blank=True, null=True)),
                ("status", models.CharField(default="hiking", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "recommendations_safelinksession", "ordering": ["-created_at"]},
        ),
    ]
