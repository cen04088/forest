from django.test import TestCase

from .mountain_story_api import clean_html, parse_mountain_story_xml


class MountainStoryApiTests(TestCase):
    def test_clean_html(self):
        self.assertEqual(clean_html("<산><BR>좋은 산</산>"), "좋은 산")

    def test_parse_mountain_story_xml(self):
        body = """
        <response>
          <header><resultCode>00</resultCode></header>
          <body>
            <totalCount>1</totalCount>
            <items>
              <item>
                <mntnid>100</mntnid>
                <mntnnm>관악산</mntnnm>
                <mntninfohght>632</mntninfohght>
                <mntninfopoflc>서울특별시 관악구</mntninfopoflc>
                <mntninfomngmemnbdnm>관악구</mntninfomngmemnbdnm>
                <mntninfodscrt>바위가 많은 산&lt;BR&gt;초보자는 우회 권장</mntninfodscrt>
              </item>
            </items>
          </body>
        </response>
        """.encode("utf-8")

        result = parse_mountain_story_xml(body)

        self.assertTrue(result["ok"])
        self.assertEqual(result["items"][0]["mountain"], "관악산")
        self.assertEqual(result["items"][0]["height_m"], 632)
