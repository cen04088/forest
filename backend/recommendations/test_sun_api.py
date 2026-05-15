from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from .services import daylight_margin_minutes
from .sun_api import format_hhmm, parse_sun_times_xml


class SunApiTests(TestCase):
    def test_format_hhmm(self):
        self.assertEqual(format_hhmm("1932"), "19:32")
        self.assertEqual(format_hhmm(" 0534 "), "05:34")

    def test_parse_sun_times_xml(self):
        xml = """
        <response>
          <header><resultCode>00</resultCode></header>
          <body>
            <items>
              <item>
                <sunrise>0522</sunrise>
                <sunset>1931</sunset>
                <civile>2000</civile>
              </item>
            </items>
          </body>
        </response>
        """.encode("utf-8")

        result = parse_sun_times_xml(xml)

        self.assertEqual(result["sunrise"], "05:22")
        self.assertEqual(result["sunset"], "19:31")
        self.assertEqual(result["civil_twilight_evening"], "20:00")

    def test_daylight_margin_minutes(self):
        now = datetime(2026, 5, 11, 17, 0, tzinfo=ZoneInfo("Asia/Seoul"))
        margin = daylight_margin_minutes({"duration_min": 90}, {"sunset": "19:00"}, now=now)

        self.assertEqual(margin, 30)
