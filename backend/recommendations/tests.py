import json

from django.test import Client, TestCase

from .services import data_quality_adjustment, purpose_bonus, select_alternatives, time_buffer_range


class RecommendationApiTests(TestCase):
    def test_health_endpoint(self):
        response = Client().get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_data_sources_endpoint_does_not_expose_key(self):
        response = Client().get("/api/data-sources/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("connected_sources", data)
        self.assertIsInstance(data.get("service_key_loaded"), bool)
        self.assertNotIn("73ce", str(data))

    def test_recommendations_returns_top_three_courses(self):
        payload = {
            "profile": {
                "ageGroup": "30s",
                "experience": "beginner",
                "condition": 3,
                "intensity": "moderate",
                "availableMinutes": 150,
                "companion": "solo",
                "purpose": "balanced",
                "transport": "public",
                "maxDistanceKm": 30,
                "departureTime": "17:00",
            },
            "location": {"lat": 37.5665, "lng": 126.978},
        }

        response = Client().post(
            "/api/recommendations/",
            data=json.dumps(payload),
            content_type="application/json",
        )

        data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data["recommendations"]), 3)
        self.assertGreaterEqual(data["recommendations"][0]["score"], data["recommendations"][1]["score"])
        self.assertIn("weather", data)


class RecommendationServiceTests(TestCase):
    def test_select_alternatives_prefers_short_easy_daylight_safe_courses(self):
        courses = [
            {
                "id": "top",
                "difficulty": "medium",
                "duration_min": 150,
                "daylight_margin_min": 20,
                "distance_from_user_km": 10,
            },
            {
                "id": "hard",
                "difficulty": "hard",
                "duration_min": 230,
                "daylight_margin_min": 10,
                "distance_from_user_km": 2,
            },
            {
                "id": "easy",
                "difficulty": "easy",
                "duration_min": 50,
                "daylight_margin_min": 120,
                "distance_from_user_km": 8,
            },
        ]

        alternatives = select_alternatives(courses, [courses[0]])

        self.assertEqual(alternatives[0]["id"], "easy")

    def test_data_quality_adjustment_penalizes_generic_unknown_courses(self):
        adjustment = data_quality_adjustment({"name": "주등산로", "mountain": "국립공원", "lat": None, "lng": None})

        self.assertLess(adjustment, -20)

    def test_purpose_bonus_prefers_healing_short_easy_course(self):
        bonus = purpose_bonus({"difficulty": "easy", "duration_min": 60, "lat": 37.5, "lng": 127.0}, {"purpose": "healing"})

        self.assertGreaterEqual(bonus, 10)

    def test_time_buffer_range_shrinks_upper_bound_for_vulnerable_mode(self):
        self.assertEqual(time_buffer_range(120, {"companion": "solo"}), (90, 150))
        self.assertEqual(time_buffer_range(120, {"companion": "vulnerable"}), (90, 135))
