"""
산림청 API 100대 명산 배치 수집 스크립트 (Django 백엔드 활용)
실행: python collect_mountains2.py
"""
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "forestrx.settings")
import django
django.setup()

from recommendations.mountain_coordinates import MOUNTAIN_COORDINATES

TOP100 = [
    # 기존 77개
    "설악산","지리산","한라산","북한산","오대산","소백산","태백산","치악산",
    "월악산","속리산","계룡산","덕유산","가야산","내장산","무등산","주왕산",
    "월출산","팔공산","도봉산","관악산","두타산","함백산","민주지산","황매산",
    "금오산","비슬산","운문산","재약산","신불산","가리왕산","공작산","화악산",
    "명지산","용문산","천마산","감악산","운악산","마이산","조계산","두륜산",
    "천관산","대둔산","서대산","오서산","칠갑산","금정산","토함산","내연산",
    "방태산","점봉산","대암산","백덕산","청옥산","선자령","용화산","삼악산",
    "인왕산","아차산","수락산","불암산","청계산","광교산","달마산","가리산",
    "응봉산","대야산","장안산","천성산","연화산","팔영산","무학산","화왕산",
    "가지산","문복산","영축산","고헌산","황석산",
    # 추가 산
    "삼성산","수리산","검단산","예봉산","유명산","축령산","주금산","소요산",
    "칠현산","무갑산","태화산",
    "계방산","오봉산","금병산","봉화산","백적산","중미산","가칠봉","향로봉",
    "마산","노인봉","매봉산","황장산","금대봉",
    "용봉산","덕숭산","보개산","도락산","황학산","금수산","제비봉","구병산",
    "장성봉","희양산","군자산","낙영산","악휘봉",
    "청량산","일월산","학가산","도장산","갑장산","천생산","단석산","왕거암","팔봉산",
    "남덕유산","웅석봉","삼봉산","달음산","광려산","정병산","방어산","천황산","산성산",
    "백운산","모악산","방장산","입암산","강천산","추월산","병풍산","봉황산","국사봉",
    "천운산","제암산","존제산","금전산","백아산",
    "성산일출봉","산방산",
    "미륵산","신어산","불모산","와룡산","호구산","망운산","금오산",
    "운길산","백운산2","천보산","왕방산","박달산","상원산",
]

NATIONAL_PARKS = {
    "설악산","지리산","한라산","북한산","오대산","소백산","태백산","치악산",
    "월악산","속리산","계룡산","덕유산","가야산","내장산","무등산","주왕산",
    "월출산","팔공산",
}

CROWDING_MAP = {
    "북한산": 0.82, "도봉산": 0.78, "남산": 0.80, "인왕산": 0.72,
    "관악산": 0.75, "청계산": 0.65, "아차산": 0.70, "수락산": 0.38,
    "불암산": 0.42, "설악산": 0.68, "한라산": 0.70, "지리산": 0.55,
    "계룡산": 0.55, "내장산": 0.58, "오대산": 0.48, "덕유산": 0.45,
    "속리산": 0.52, "주왕산": 0.48, "가야산": 0.55, "치악산": 0.45,
    "소백산": 0.40, "무등산": 0.58, "월출산": 0.42, "월악산": 0.42,
    "팔공산": 0.60, "태백산": 0.40, "함백산": 0.32, "두타산": 0.35,
    "금정산": 0.55, "마이산": 0.50, "황매산": 0.35,
}

HARD_NAMES = {
    "설악산","지리산","한라산","덕유산","치악산","두타산","함백산","점봉산",
    "방태산","가리왕산","민주지산","화악산","청옥산","대암산","백덕산",
    "황석산","운문산","재약산","신불산","가지산","응봉산",
}
EASY_NAMES = {
    "인왕산","아차산","수리산","칠갑산","천성산","불암산","선자령","삼악산",
    "수락산","달마산","연화산","팔영산",
}
HEALING_NAMES = {
    "오대산","내장산","두륜산","천관산","조계산","달마산","연화산","팔영산",
    "선자령","장안산","천성산",
}
VIEW_NAMES = {
    "설악산","한라산","지리산","북한산","팔공산","무등산","월출산","마이산",
    "황매산","비슬산","팔영산","두타산","금정산",
}
EASY_ACCESS = {
    "인왕산","아차산","수리산","선자령","삼악산","불암산","수락산","청계산",
    "달마산","두륜산","천관산","금정산","토함산","조계산","연화산","팔영산",
    "천성산","내장산","주왕산","공작산","천마산","도봉산","관악산",
}


def infer_difficulty(height, name):
    if name in HARD_NAMES or height >= 1400:
        return "hard"
    if name in EASY_NAMES or height <= 400:
        return "easy"
    return "medium"


def infer_companion_fit(difficulty, name):
    if name in EASY_ACCESS or difficulty == "easy":
        return ["vulnerable", "family", "solo"]
    if difficulty == "medium":
        return ["family", "solo"]
    return ["solo"]


def infer_purpose_fit(height, name):
    fits = ["balanced"]
    if name in HEALING_NAMES:
        fits.append("healing")
    if name in VIEW_NAMES:
        fits.append("view")
    if height >= 1200:
        fits.append("workout")
    if len(fits) == 1:
        fits.append("healing" if height < 800 else "view")
    return list(dict.fromkeys(fits))


def infer_walk_time(height, difficulty):
    if difficulty == "easy":
        return (60, 180)
    if difficulty == "medium":
        return (90, 240) if height < 800 else (150, 360)
    if height >= 1700:
        return (360, 720)
    if height >= 1400:
        return (270, 540)
    return (200, 450)


def infer_highlights(name, summary):
    tags = []
    if name in NATIONAL_PARKS:
        tags.append("국립공원")
    kw_map = [
        ("폭포", "폭포 경관"), ("단풍", "단풍 명소"), ("눈", "설경 명소"),
        ("설", "설경 명소"), ("암릉", "암릉 경관"), ("바위", "암릉 경관"),
        ("계곡", "계곡 트레킹"), ("사찰", "사찰 탐방"), ("절", "사찰 탐방"),
        ("전망", "정상 전망 우수"), ("조망", "정상 전망 우수"),
        ("철쭉", "철쭉 명소"), ("동백", "동백 명소"), ("억새", "억새 군락"),
    ]
    seen = set()
    for kw, label in kw_map:
        if kw in summary and label not in seen:
            tags.append(label)
            seen.add(label)
    if not tags:
        tags.append("자연 경관 우수")
    return tags[:4]


def main():
    base_url = "http://127.0.0.1:8000/api/mountain-story/"
    print(f"대상: {len(TOP100)}개 산")

    api_results = {}
    no_coord = []
    no_data = []

    for i, name in enumerate(TOP100, 1):
        if name not in MOUNTAIN_COORDINATES:
            no_coord.append(name)
            print(f"[{i:2d}] {name}: 좌표 없음 - 건너뜀")
            continue

        url = base_url + "?" + urllib.parse.urlencode({"mountain": name, "size": 1})
        try:
            with urllib.request.urlopen(url, timeout=6) as r:
                j = json.loads(r.read())
            if j.get("ok") and j.get("items"):
                item = j["items"][0]
                api_results[name] = {
                    "height_m": item.get("height_m", 0) or 0,
                    "address": item.get("address", ""),
                    "summary": (item.get("summary") or "")[:200],
                }
                print(f"[{i:2d}] {name}: {api_results[name]['height_m']}m OK")
            else:
                no_data.append(name)
                print(f"[{i:2d}] {name}: API 데이터 없음")
        except Exception as e:
            no_data.append(name)
            print(f"[{i:2d}] {name}: 오류 {e}")
        time.sleep(0.12)

    # trail_count 보완
    try:
        from recommendations.loaders import load_public_trail_courses
        courses = load_public_trail_courses()
        trail_counts = {}
        for c in courses:
            mn = c.get("mountain", "")
            trail_counts[mn] = trail_counts.get(mn, 0) + 1
    except Exception:
        trail_counts = {}

    # mountain_data.py 생성
    mountains = []
    for name in TOP100:
        coord = MOUNTAIN_COORDINATES.get(name)
        if not coord:
            continue
        api = api_results.get(name, {})
        height = api.get("height_m", 0) or 0
        summary = api.get("summary", "")
        region = coord.get("region", "")

        difficulty = infer_difficulty(height, name)
        walk_min, walk_max = infer_walk_time(height, difficulty)

        m = {
            "id": f"m-{name}",
            "name": name,
            "region": region,
            "lat": coord["lat"],
            "lng": coord["lng"],
            "elevation_m": height if height > 0 else None,
            "difficulty": difficulty,
            "walk_time_min": walk_min,
            "walk_time_max": walk_max,
            "trail_count": trail_counts.get(name, 0),
            "companion_fit": infer_companion_fit(difficulty, name),
            "purpose_fit": infer_purpose_fit(height, name),
            "crowding": CROWDING_MAP.get(name, 0.40),
            "national_park": name in NATIONAL_PARKS,
            "highlights": infer_highlights(name, summary),
            "description": summary[:130] if summary else f"{name} — {region} 위치 명산.",
        }
        mountains.append(m)

    out_path = Path(__file__).parent / "recommendations" / "mountain_data.py"
    def py_repr(v):
        if v is True:
            return "True"
        if v is False:
            return "False"
        if v is None:
            return "None"
        return json.dumps(v, ensure_ascii=False)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# 산림청 API 자동 수집 — collect_mountains2.py\n\n")
        f.write("MOUNTAINS = [\n")
        for m in mountains:
            f.write("    {\n")
            for k, v in m.items():
                f.write(f"        {json.dumps(k, ensure_ascii=False)}: {py_repr(v)},\n")
            f.write("    },\n")
        f.write("]\n\n")
        f.write("MOUNTAIN_BY_ID = {m['id']: m for m in MOUNTAINS}\n")
        f.write("MOUNTAIN_BY_NAME = {m['name']: m for m in MOUNTAINS}\n")

    print(f"\n=== 완료 ===")
    print(f"성공: {len(mountains)}개")
    print(f"좌표 없음: {len(no_coord)}개 -> {no_coord}")
    print(f"API 데이터 없음: {len(no_data)}개 -> {no_data}")
    print(f"저장: {out_path}")


if __name__ == "__main__":
    main()
