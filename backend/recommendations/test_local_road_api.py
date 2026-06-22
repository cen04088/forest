from django.test import Client, TestCase

from .local_road_api import fetch_local_road_trails, korea_2000_to_wgs84, load_local_road_trails


class LocalRoadApiTests(TestCase):
    def test_korea_2000_to_wgs84_projects_expected_korea_bounds(self):
        point = korea_2000_to_wgs84(953901.0, 1952032.0)

        self.assertGreater(point["lat"], 37)
        self.assertLess(point["lat"], 38)
        self.assertGreater(point["lng"], 126)
        self.assertLess(point["lng"], 127)

    def test_load_local_road_trails_reads_shp_geometry(self):
        trails = load_local_road_trails()

        self.assertGreater(len(trails), 1000)
        self.assertIn("lat", trails[0])
        self.assertIn("lng", trails[0])

    def test_fetch_local_road_trails_filters_by_mountain(self):
        result = fetch_local_road_trails(mountain_name="건봉산", size=5)

        self.assertTrue(result["ok"])
        self.assertLessEqual(len(result["items"]), 5)
        self.assertTrue(any("건봉산" in item["mountain"] or "건봉산" in item["name"] for item in result["items"]))

    def test_local_road_trails_endpoint_returns_geometry(self):
        response = Client().get("/api/local-road-trails/?lat=37.7&lng=128.45&radius=20&size=3")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["ok"])
        self.assertLessEqual(len(data["items"]), 3)
        if data["items"]:
            self.assertIn("route_geometry", data["items"][0])
