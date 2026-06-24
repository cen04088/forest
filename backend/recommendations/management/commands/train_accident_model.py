from django.core.management.base import BaseCommand

from recommendations.accident_model import (
    get_accident_model_training_summary,
    predict_accident_risk,
    save_accident_model_to_disk,
)


class Command(BaseCommand):
    help = "Train the in-memory mountain accident risk model and print a training summary."

    def handle(self, *args, **options):
        summary = get_accident_model_training_summary()
        if not summary.get("trained"):
            self.stderr.write(self.style.ERROR("Accident model training failed: no usable rows."))
            return

        self.stdout.write(self.style.SUCCESS("Accident model trained."))
        if save_accident_model_to_disk():
            self.stdout.write(self.style.SUCCESS("Trained model successfully saved to accident_trained_model.pkl."))
        else:
            self.stdout.write(self.style.WARNING("Failed to save trained model to disk."))

        self.stdout.write(f"Rows used: {summary.get('rows')}")
        self.stdout.write(f"Year range: {summary.get('year_range')}")
        self.stdout.write("Sources:")
        for source, count in sorted((summary.get("sources") or {}).items()):
            self.stdout.write(f"  - {source}: {count}")

        samples = [
            ("spring_weekend_noon", 4, 12, 5),
            ("summer_evening", 8, 18, 6),
            ("autumn_morning", 10, 9, 5),
            ("winter_early", 1, 6, 6),
        ]
        self.stdout.write("Sample predictions:")
        for label, month, hour, weekday in samples:
            result = predict_accident_risk(month=month, hour=hour, weekday=weekday)
            self.stdout.write(
                "  - "
                f"{label}: risk={result['risk_index']} "
                f"safety={result['ml_safety_score']} "
                f"type={result['top_type']} "
                f"warning={result['warning']}"
            )
