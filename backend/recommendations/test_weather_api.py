from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from .weather_api import kma_nowcast_base_datetime, lat_lng_to_kma_grid, parse_kma_nowcast_xml


class WeatherApiTests(TestCase):
    def test_lat_lng_to_kma_grid(self):
        nx, ny = lat_lng_to_kma_grid(37.5665, 126.978)

        self.assertEqual((nx, ny), (60, 127))

    def test_base_datetime_uses_previous_hour_before_observation_ready(self):
        now = datetime(2026, 5, 11, 15, 30, tzinfo=ZoneInfo("Asia/Seoul"))

        self.assertEqual(kma_nowcast_base_datetime(now), ("20260511", "1400"))

    def test_parse_kma_nowcast_xml(self):
        xml = """
        <response>
          <header>
            <resultCode>00</resultCode>
            <resultMsg>NORMAL_SERVICE</resultMsg>
          </header>
          <body>
            <items>
              <item><category>T1H</category><obsrValue>19.4</obsrValue></item>
              <item><category>RN1</category><obsrValue>0</obsrValue></item>
              <item><category>WSD</category><obsrValue>2.1</obsrValue></item>
              <item><category>REH</category><obsrValue>57</obsrValue></item>
              <item><category>PTY</category><obsrValue>0</obsrValue></item>
            </items>
          </body>
        </response>
        """.encode("utf-8")

        weather = parse_kma_nowcast_xml(xml, nx=60, ny=127, base_date="20260511", base_time="1500")

        self.assertEqual(weather["temperature_c"], 19.4)
        self.assertEqual(weather["rainfall_mm"], 0)
        self.assertEqual(weather["precipitation_type"], "없음")
        self.assertEqual(weather["source"], "기상청_초단기실황")
