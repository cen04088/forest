from django.test import TestCase

from .disaster_risk import disaster_risk_level, find_course_disaster_risks
from .loaders import normalize_disaster_risk_row


class DisasterRiskTests(TestCase):
    def test_normalize_disaster_risk_row(self):
        row = {
            "지구명": "북한산 탐방로",
            "위치": "백운대 하단",
            "시설명": "백운대 하단",
            "표지판설치": "1",
            "위험요인": "추락위험",
            "일최대예상탐방객": "120",
            "대피계획인원": "30",
            "대피장소": "탐방지원센터",
        }

        zone = normalize_disaster_risk_row(1, row)

        self.assertEqual(zone["risk_factor"], "추락위험")
        self.assertEqual(zone["expected_daily_visitors"], 120)

    def test_find_course_disaster_risks_matches_course_text(self):
        zones = [
            {
                "district": "북한산 탐방로",
                "location": "백운대 하단",
                "facility": "백운대 하단",
                "risk_factor": "추락위험",
                "search_text": "북한산탐방로백운대하단추락위험",
            }
        ]

        matches = find_course_disaster_risks({"mountain": "북한산", "name": "백운대 코스"}, zones)

        self.assertEqual(len(matches), 1)
        self.assertEqual(disaster_risk_level(matches), "high")

    def test_generic_trail_word_does_not_match_unrelated_course(self):
        zones = [
            {
                "district": "가라산 탐방로",
                "location": "가라산 전망대",
                "facility": "가라산 전망대",
                "risk_factor": "추락위험",
                "search_text": "가라산탐방로가라산전망대추락위험",
            }
        ]

        matches = find_course_disaster_risks({"mountain": "국립공원", "name": "탐방로"}, zones)

        self.assertEqual(matches, [])
