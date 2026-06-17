"""
산림청 API로 100대 명산 데이터 자동 수집 → mountain_data.py 재생성
실행: python collect_mountains.py
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Django 환경 없이 직접 API 키 로딩
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "forestrx.settings")

import django
django.setup()

from recommendations.loaders import load_public_service_key
from recommendations.mountain_coordinates import MOUNTAIN_COORDINATES

# ── 산림청 100대 명산 전체 목록 ─────────────────────────────────────────────
TOP100 = [
    "설악산","지리산","한라산","북한산","오대산","소백산","태백산","치악산",
    "월악산","속리산","계룡산","덕유산","가야산","내장산","무등산","주왕산",
    "월출산","팔공산","도봉산","관악산","두타산","함백산","민주지산","황석산",
    "황매산","금오산","비슬산","운문산","재약산","신불산","영축산","고헌산",
    "가리왕산","오봉산","공작산","화악산","명지산","용문산","천마산","감악산",
    "운악산","마이산","조계산","두륜산","천관산","대둔산","서대산","오서산",
    "칠갑산","금산","금정산","토함산","내연산","통고산","방태산","점봉산",
    "대암산","백덕산","청옥산","선자령","용화산","삼악산","인왕산","아차산",
    "수락산","불암산","청계산","광교산","달마산","백운산","축령산","가리산",
    "응봉산","대야산","희양산","구병산","칠현산","남산","수리산","축령산",
    "장안산","봉화산","천성산","정족산","대운산","연화산","사량도지리산",
    "고성 거류산","강천산","추월산","팔영산","무학산","작약산","화왕산",
    "신어산","천황산","가지산","문복산",
]

STORY_URL = "http://api.forest.go.kr/openapi/service/trailInfoService/getforeststoryservice"


def fetch_story(mountain_name, service_key, timeout=8):
    query = {
        "ServiceKey": service_key,
        "pageNo": 1,
        "numOfRows": 1,
        "mntnNm": mountain_name,
    }
    url = f"{STORY_URL}?{urllib.parse.urlencode(query, safe='%')}"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            body = r.read()
        root = ET.fromstring(body)
        items = root.findall(".//item")
        if not items:
            return None
        item = items[0]
        def t(tag):
            el = item.find(tag)
            return el.text.strip() if el is not None and el.text else ""
        height_raw = t("mntnHigh")
        try:
            height_m = int(float(height_raw))
        except (ValueError, TypeError):
            height_m = 0
        return {
            "mountain_id": t("mntnCode"),
            "name_raw": t("mntnNm"),
            "height_m": height_m,
            "address": t("mntnAddr"),
            "summary": t("mntnSumry")[:200] if t("mntnSumry") else "",
        }
    except Exception as e:
        print(f"  ⚠ {mountain_name} API 오류: {e}")
        return None


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlng/2)**2
    return R * 2 * math.asin(math.sqrt(a))


def infer_difficulty(height_m, name):
    hard_names = {"설악산","지리산","한라산","덕유산","치악산","태백산","두타산","함백산",
                  "점봉산","방태산","가리왕산","민주지산","화악산","청옥산","대암산",
                  "백덕산","황석산","운문산","재약산","신불산","천황산","가지산"}
    easy_names = {"남산","인왕산","아차산","수리산","칠현산","칠갑산","금산","천성산",
                  "불암산","선자령","삼악산","수락산","사량도지리산"}
    if name in hard_names or height_m >= 1400:
        return "hard"
    if name in easy_names or height_m <= 400:
        return "easy"
    return "medium"


def infer_companion_fit(difficulty, height_m, name):
    easy_accessible = {"남산","인왕산","아차산","수리산","선자령","삼악산","칠갑산",
                       "금산","천성산","내장산","주왕산","오봉산","공작산","천마산",
                       "불암산","수락산","청계산","광교산","달마산","대둔산","두륜산",
                       "천관산","금정산","토함산","내연산","조계산","강천산","추월산",
                       "팔영산","연화산","정족산","대운산","사량도지리산","도봉산","관악산"}
    if name in easy_accessible or difficulty == "easy":
        return ["vulnerable", "family", "solo"]
    if difficulty == "medium":
        return ["family", "solo"]
    return ["solo"]


def infer_purpose_fit(height_m, name):
    healing = {"오대산","내장산","두륜산","천관산","조계산","강천산","추월산","연화산",
               "팔영산","선자령","달마산","금산","사량도지리산","정족산","남산"}
    view = {"설악산","한라산","지리산","북한산","팔공산","무등산","월출산","마이산",
            "황매산","비슬산","팔영산","두타산","선자령","금정산","화왕산"}
    workout = {"치악산","두타산","함백산","가리왕산","민주지산","화악산","청옥산",
               "가지산","운문산","신불산","재약산","대암산","백덕산","황석산","통고산"}
    fits = ["balanced"]
    if name in healing:
        fits.append("healing")
    if name in view:
        fits.append("view")
    if name in workout:
        fits.append("workout")
    if len(fits) == 1:
        fits.append("healing" if height_m < 800 else "view")
    return list(dict.fromkeys(fits))


def infer_walk_time(height_m, difficulty):
    if difficulty == "easy":
        return (60, 180)
    if difficulty == "medium":
        if height_m < 800:
            return (90, 240)
        return (150, 360)
    if height_m >= 1700:
        return (360, 720)
    if height_m >= 1400:
        return (270, 540)
    return (200, 450)


def infer_highlights(name, address, summary):
    # 간단한 키워드 기반 하이라이트
    highlights = []
    if "국립공원" in summary or name in {"설악산","지리산","한라산","북한산","오대산","소백산",
                                          "태백산","치악산","월악산","속리산","계룡산","덕유산",
                                          "가야산","내장산","무등산","주왕산","월출산","팔공산"}:
        highlights.append("국립공원")
    if "폭포" in summary:
        highlights.append("폭포 경관")
    if "단풍" in summary:
        highlights.append("단풍 명소")
    if "설" in summary or "눈" in summary:
        highlights.append("설경 명소")
    if "암릉" in summary or "바위" in summary:
        highlights.append("암릉 경관")
    if "계곡" in summary:
        highlights.append("계곡 트레킹")
    if "사찰" in summary or "절" in summary:
        highlights.append("사찰 탐방")
    if "전망" in summary or "조망" in summary:
        highlights.append("정상 전망 우수")
    if not highlights:
        highlights.append("자연 경관 우수")
    return highlights[:4]


NATIONAL_PARKS = {
    "설악산","지리산","한라산","북한산","오대산","소백산","태백산","치악산","월악산",
    "속리산","계룡산","덕유산","가야산","내장산","무등산","주왕산","월출산","팔공산",
}

CROWDING_MAP = {
    "북한산":0.82,"도봉산":0.78,"남산":0.80,"인왕산":0.72,"관악산":0.75,
    "청계산":0.65,"아차산":0.70,"수락산":0.38,"불암산":0.42,
    "설악산":0.68,"한라산":0.70,"지리산":0.55,"계룡산":0.55,
    "내장산":0.58,"오대산":0.48,"덕유산":0.45,"속리산":0.52,
    "주왕산":0.48,"가야산":0.55,"치악산":0.45,"소백산":0.40,
    "무등산":0.58,"월출산":0.42,"월악산":0.42,"팔공산":0.60,
    "태백산":0.40,"함백산":0.32,"두타산":0.35,"두륜산":0.40,
    "조계산":0.45,"금정산":0.55,"마이산":0.50,"황매산":0.35,
}


def main():
    service_key = load_public_service_key()
    if not service_key:
        print("❌ PUBLIC_SERVICE_KEY 없음")
        sys.exit(1)

    print(f"🔑 API 키 확인: {service_key[:8]}...")
    print(f"📋 수집 대상: {len(TOP100)}개 산\n")

    results = []
    failed = []

    for i, name in enumerate(TOP100, 1):
        print(f"[{i:3d}/{len(TOP100)}] {name}...", end=" ", flush=True)
        data = fetch_story(name, service_key)

        coord = MOUNTAIN_COORDINATES.get(name)
        if coord is None:
            # 이름 일부 매칭 시도
            for k, v in MOUNTAIN_COORDINATES.items():
                if name in k or k in name:
                    coord = v
                    break

        if data is None and coord is None:
            print("⏭ 데이터 없음 (건너뜀)")
            failed.append(name)
            continue

        height = (data["height_m"] if data else 0) or 0
        address = (data["address"] if data else "") or ""
        summary = (data["summary"] if data else "") or ""

        # 좌표가 없으면 주소에서 지역 추출
        region = coord["region"] if coord else (address.split(",")[0][:20] if address else "정보 없음")

        if not coord:
            print("⚠ 좌표 없음 (스킵)")
            failed.append(name)
            continue

        difficulty = infer_difficulty(height, name)
        walk_min, walk_max = infer_walk_time(height, difficulty)

        mountain = {
            "id": f"m-{name}",
            "name": name,
            "region": region,
            "lat": coord["lat"],
            "lng": coord["lng"],
            "elevation_m": height if height > 0 else None,
            "difficulty": difficulty,
            "walk_time_min": walk_min,
            "walk_time_max": walk_max,
            "trail_count": 0,  # CSV에서 보완
            "companion_fit": infer_companion_fit(difficulty, height, name),
            "purpose_fit": infer_purpose_fit(height, name),
            "crowding": CROWDING_MAP.get(name, 0.40),
            "national_park": name in NATIONAL_PARKS,
            "highlights": infer_highlights(name, address, summary),
            "description": summary[:120] if summary else f"{name} — {region}에 위치한 명산.",
        }
        results.append(mountain)
        print(f"✅ {height}m")
        time.sleep(0.15)  # API 과부하 방지

    # CSV 탐방로 수로 trail_count 보완
    try:
        from recommendations.loaders import load_public_trail_courses
        courses = load_public_trail_courses()
        count_map = {}
        for c in courses:
            mn = c.get("mountain", "")
            count_map[mn] = count_map.get(mn, 0) + 1
        for m in results:
            if m["name"] in count_map:
                m["trail_count"] = count_map[m["name"]]
    except Exception as e:
        print(f"\n⚠ trail_count 보완 실패: {e}")

    # mountain_data.py 출력
    out_path = Path(__file__).parent / "recommendations" / "mountain_data.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 산림청 API 자동 수집 데이터 — collect_mountains.py로 생성\n\n")
        f.write("MOUNTAINS = [\n")
        for m in results:
            f.write(f"    {{\n")
            for k, v in m.items():
                f.write(f"        {json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False)},\n")
            f.write(f"    }},\n")
        f.write("]\n\n")
        f.write("MOUNTAIN_BY_ID = {m['id']: m for m in MOUNTAINS}\n")
        f.write("MOUNTAIN_BY_NAME = {m['name']: m for m in MOUNTAINS}\n")

    print(f"\n{'='*50}")
    print(f"✅ 수집 완료: {len(results)}개")
    print(f"⏭ 건너뜀:    {len(failed)}개 → {failed}")
    print(f"📄 저장됨:   {out_path}")


if __name__ == "__main__":
    main()
