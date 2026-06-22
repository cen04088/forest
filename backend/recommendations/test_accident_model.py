from django.test import TestCase

from .accident_model import get_accident_model_training_summary, predict_accident_risk


class AccidentModelTests(TestCase):
    def test_training_uses_added_accident_datasets_except_2023_2024(self):
        summary = get_accident_model_training_summary()

        self.assertTrue(summary["trained"])
        self.assertNotIn("2023-2024.csv", summary["sources"])
        self.assertIn("전국 산악사고 구조활동현황(2010_2016).csv", summary["sources"])
        self.assertIn("전국 산악사고 구조활동현황(2017~2021).csv", summary["sources"])
        self.assertIn("전국 산악사고 현황(2022~2023년).csv", summary["sources"])
        self.assertGreater(summary["rows"], 10000)

    def test_prediction_returns_training_metadata(self):
        result = predict_accident_risk(month=10, hour=12, weekday=5)

        self.assertIn("risk_index", result)
        self.assertIn("training", result)
        self.assertTrue(result["training"]["trained"])
