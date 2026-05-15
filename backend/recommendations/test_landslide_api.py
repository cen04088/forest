from django.test import TestCase

from .landslide_api import (
    landslide_risk_label,
    parse_landslide_prediction_json,
    parse_landslide_prediction_xml,
)


class LandslideApiTests(TestCase):
    def test_landslide_risk_label(self):
        self.assertEqual(landslide_risk_label("경보"), "danger")
        self.assertEqual(landslide_risk_label("주의보"), "caution")
        self.assertEqual(landslide_risk_label("정상"), "low")

    def test_parse_landslide_prediction_json(self):
        body = b"""
        {
          "response": {
            "header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
            "body": {
              "totalCount": 1,
              "items": {
                "item": {
                  "lndslFrcstNm": "\xec\xa3\xbc\xec\x9d\x98\xeb\xb3\xb4",
                  "sgg": "\xec\x84\x9c\xec\x9a\xb8\xed\x8a\xb9\xeb\xb3\x84\xec\x8b\x9c \xea\xb4\x80\xec\x95\x85\xea\xb5\xac",
                  "prctnInfoAnlssDt": "2026-05-15 10:00:00"
                }
              }
            }
          }
        }
        """

        result = parse_landslide_prediction_json(body)

        self.assertTrue(result["ok"])
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["risk"], "caution")

    def test_parse_landslide_prediction_xml(self):
        body = """
        <response>
          <header><resultCode>00</resultCode></header>
          <body>
            <totalCount>1</totalCount>
            <items>
              <item>
                <lndslFrcstNm>경보</lndslFrcstNm>
                <sgg>강원특별자치도 인제군</sgg>
                <prctnInfoAnlssDt>2026-05-15 10:00:00</prctnInfoAnlssDt>
              </item>
            </items>
          </body>
        </response>
        """.encode("utf-8")

        result = parse_landslide_prediction_xml(body)

        self.assertTrue(result["ok"])
        self.assertEqual(result["items"][0]["risk"], "danger")
