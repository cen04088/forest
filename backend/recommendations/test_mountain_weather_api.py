from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from .mountain_weather_api import parse_mountain_weather_response, resolve_base_datetime


class MountainWeatherApiTests(TestCase):
    def test_resolve_base_datetime_uses_previous_kma_slot(self):
        now = datetime(2026, 5, 15, 13, 20, tzinfo=ZoneInfo("Asia/Seoul"))

        base_date, base_time = resolve_base_datetime(now=now)

        self.assertEqual(base_date, "20260515")
        self.assertEqual(base_time, "1100")

    def test_parse_json_response_summarizes_categories(self):
        body = b"""
        {
          "response": {
            "body": {
              "items": {
                "item": [
                  {"mountainNum":"5","category":"TMP","fcstValue":"14","lat":"37.66","lon":"126.98","alt":"836","stn_nm":"Bukhansan summit"},
                  {"mountainNum":"5","category":"PCP","fcstValue":"1.5mm"},
                  {"mountainNum":"5","category":"WSD","fcstValue":"6"}
                ]
              }
            }
          }
        }
        """

        result = parse_mountain_weather_response(body, "5", "20260515", "1100")

        self.assertTrue(result["ok"])
        self.assertEqual(result["temperature_c"], 14.0)
        self.assertEqual(result["rainfall_mm"], 1.5)
        self.assertEqual(result["wind_speed_ms"], 6.0)
        self.assertEqual(result["station_name"], "Bukhansan summit")
