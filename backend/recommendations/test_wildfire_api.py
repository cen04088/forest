from django.test import TestCase

from .wildfire_api import parse_wildfire_risk_xml, wildfire_risk_label


class WildfireApiTests(TestCase):
    def test_wildfire_risk_label(self):
        self.assertEqual(wildfire_risk_label(30), "low")
        self.assertEqual(wildfire_risk_label(55), "medium")
        self.assertEqual(wildfire_risk_label(77), "high")
        self.assertEqual(wildfire_risk_label(90), "very_high")

    def test_parse_wildfire_risk_xml(self):
        xml = """
        <response>
          <header><resultCode>00</resultCode></header>
          <body>
            <items>
              <item>
                <analdate>2026-05-11 15</analdate>
                <doname>전국</doname>
                <meanavg>51</meanavg>
                <maxi>77</maxi>
              </item>
            </items>
          </body>
        </response>
        """.encode("utf-8")

        result = parse_wildfire_risk_xml(xml)

        self.assertEqual(result["risk"], "high")
        self.assertEqual(result["mean_index"], 51)
        self.assertEqual(result["max_index"], 77)
        self.assertEqual(result["region"], "전국")
