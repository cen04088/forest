from django.test import TestCase

from .coordinates import extract_forest_map_coordinates
from .forest_api import forest_spatial_items_to_courses, parse_forest_spatial_xml
from .mountain_coordinates import find_mountain_coordinates


class ForestSpatialApiParserTests(TestCase):
    def test_parse_forest_spatial_xml(self):
        xml = """
        <response>
          <header>
            <resultCode>00</resultCode>
            <resultMsg>NORMAL SERVICE.</resultMsg>
          </header>
          <body>
            <items>
              <item>
                <mntnnm>가리왕산</mntnnm>
                <mntninfourl>https://map.forest.go.kr/forest/?systype=mapSearch&amp;searchOption=trail&amp;longitude=196756.2031&amp;latitude=438114.5625&amp;scale=17</mntninfourl>
                <mntnfile>http://www.forest.go.kr/images/data/down/mount/2211050100.zip</mntnfile>
                <mntnimg>http://www.forest.go.kr/swf/foreston/mountain/R_M0006.swf</mntnimg>
              </item>
            </items>
            <totalCount>1</totalCount>
          </body>
        </response>
        """.encode("utf-8")

        result = parse_forest_spatial_xml(xml)

        self.assertTrue(result["ok"])
        self.assertEqual(result["total_count"], 1)
        self.assertEqual(result["items"][0]["mountain"], "가리왕산")
        self.assertTrue(result["items"][0]["file_url"].endswith(".zip"))
        self.assertAlmostEqual(result["items"][0]["lat"], 37.44, places=1)
        self.assertAlmostEqual(result["items"][0]["lng"], 126.96, places=1)


class CoordinateTransformTests(TestCase):
    def test_extract_forest_map_coordinates(self):
        coordinates = extract_forest_map_coordinates(
            "https://map.forest.go.kr/forest/?longitude=196756.2031&latitude=438114.5625&scale=17"
        )

        self.assertAlmostEqual(coordinates["lat"], 37.44, places=1)
        self.assertAlmostEqual(coordinates["lng"], 126.96, places=1)

    def test_find_mountain_coordinates(self):
        mountain, coordinates = find_mountain_coordinates("소공원~권금성")

        self.assertEqual(mountain, "설악산")
        self.assertAlmostEqual(coordinates["lat"], 38.119444)

    def test_find_mountain_coordinates_does_not_match_ui_do_as_bukhansan(self):
        mountain, coordinates = find_mountain_coordinates("우이도탐방로")

        self.assertIsNone(mountain)
        self.assertIsNone(coordinates)

    def test_forest_spatial_items_to_courses(self):
        courses = forest_spatial_items_to_courses(
            {
                "items": [
                    {
                        "mountain": "관악산",
                        "map_url": "https://map.forest.go.kr/forest/",
                        "coordinates": {"lat": 37.442424, "lng": 126.963344},
                    }
                ]
            }
        )

        self.assertEqual(courses[0]["mountain"], "관악산")
        self.assertEqual(courses[0]["lat"], 37.442424)
        self.assertEqual(courses[0]["source"], "산림청_산림공간정보_등산로정보")
