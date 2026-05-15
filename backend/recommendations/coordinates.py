from math import atan, cos, degrees, radians, sin, sqrt, tan
from urllib.parse import parse_qs, urlparse


def extract_forest_map_coordinates(map_url):
    if not map_url:
        return None

    query = parse_qs(urlparse(map_url).query)
    try:
        x = float(query["longitude"][0])
        y = float(query["latitude"][0])
    except (KeyError, IndexError, ValueError):
        return None

    lat, lng = korea_central_belt_to_wgs84(y, x)
    return {"lat": round(lat, 6), "lng": round(lng, 6)}


def korea_central_belt_to_wgs84(northing, easting):
    # Forest map URLs use Korean central belt TM-style coordinates.
    # This inverse projection gives WGS84-close lat/lng for distance ranking.
    a = 6378137.0
    inv_f = 298.257222101
    f = 1 / inv_f
    e2 = 2 * f - f * f
    ep2 = e2 / (1 - e2)
    k0 = 1.0
    lat0 = radians(38.0)
    lon0 = radians(127.0)
    false_easting = 200000.0
    false_northing = 500000.0

    m0 = meridional_arc(lat0, a, e2)
    m = m0 + (northing - false_northing) / k0
    mu = m / (a * (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256))

    e1 = (1 - sqrt(1 - e2)) / (1 + sqrt(1 - e2))
    fp = (
        mu
        + (3 * e1 / 2 - 27 * e1**3 / 32) * sin(2 * mu)
        + (21 * e1**2 / 16 - 55 * e1**4 / 32) * sin(4 * mu)
        + (151 * e1**3 / 96) * sin(6 * mu)
        + (1097 * e1**4 / 512) * sin(8 * mu)
    )

    sin_fp = sin(fp)
    cos_fp = cos(fp)
    tan_fp = tan(fp)
    n1 = a / sqrt(1 - e2 * sin_fp**2)
    r1 = a * (1 - e2) / (1 - e2 * sin_fp**2) ** 1.5
    t1 = tan_fp**2
    c1 = ep2 * cos_fp**2
    d = (easting - false_easting) / (n1 * k0)

    lat = fp - (n1 * tan_fp / r1) * (
        d**2 / 2
        - (5 + 3 * t1 + 10 * c1 - 4 * c1**2 - 9 * ep2) * d**4 / 24
        + (61 + 90 * t1 + 298 * c1 + 45 * t1**2 - 252 * ep2 - 3 * c1**2) * d**6 / 720
    )
    lng = lon0 + (
        d
        - (1 + 2 * t1 + c1) * d**3 / 6
        + (5 - 2 * c1 + 28 * t1 - 3 * c1**2 + 8 * ep2 + 24 * t1**2) * d**5 / 120
    ) / cos_fp

    return degrees(lat), degrees(lng)


def meridional_arc(lat, a, e2):
    return a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * sin(2 * lat)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * sin(4 * lat)
        - (35 * e2**3 / 3072) * sin(6 * lat)
    )
