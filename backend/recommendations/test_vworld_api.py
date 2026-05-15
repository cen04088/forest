from django.test import TestCase

from .vworld_api import build_bbox_filter, parse_vworld_trails_json


class VWorldTrailApiTests(TestCase):
    def test_build_bbox_filter_uses_lng_lat_order(self):
        bbox = build_bbox_filter(37.658, 126.977, 5)

        self.assertTrue(bbox.startswith("BOX(126."))
        self.assertIn(",37.", bbox)

    def test_parse_vworld_linestring_to_course(self):
        body = b"""
        {
          "response": {
            "status": "OK",
            "record": {"total": "1"},
            "result": {
              "featureCollection": {
                "features": [
                  {
                    "properties": {
                      "mntil_nm": "Baegundae trail",
                      "sig_kor_nm": "Seoul",
                      "shape_leng": "1200"
                    },
                    "geometry": {
                      "type": "LineString",
                      "coordinates": [[126.97, 37.65], [126.98, 37.66]]
                    }
                  }
                ]
              }
            }
          }
        }
        """

        result = parse_vworld_trails_json(body, mountain_name="Bukhansan")

        self.assertTrue(result["ok"])
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["source"], "브이월드_등산로_LT_L_FRSTCLIMB")
        self.assertEqual(result["items"][0]["route_geometry"][0], {"lat": 37.65, "lng": 126.97})
        self.assertEqual(result["items"][0]["distance_km"], 1.2)
