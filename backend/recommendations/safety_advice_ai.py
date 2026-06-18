import os


def generate_safety_advice(mountain: dict, weather: dict, profile: dict, sun_times: dict = None) -> str | None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from google import genai
        from google.genai import types

        diff = {"easy": "초급", "medium": "중급", "hard": "고급"}.get(mountain.get("difficulty", ""), "")
        companion = {"vulnerable": "어린이·노약자 동반", "family": "가족", "solo": "혼자"}.get(
            profile.get("companion", ""), ""
        )
        rainfall = weather.get("rainfall_mm") or 0
        wind = weather.get("wind_speed_ms") or 0
        wildfire = weather.get("wildfire_risk") or "low"
        wildfire_label = {"low": "낮음", "medium": "보통", "high": "높음", "very_high": "매우 높음"}.get(wildfire, "낮음")
        sunset = (sun_times or {}).get("sunset", "미상")
        departure = profile.get("departureTime", "미상")
        desired_min = profile.get("desiredHikingMinutes", 120)
        walk_max = mountain.get("walk_time_max") or 180

        prompt = (
            f"다음 조건에서 산행 전 꼭 알아야 할 안전 조언 3가지를 작성하세요.\n\n"
            f"산: {mountain.get('name')} ({mountain.get('region')})  해발 {mountain.get('elevation_m')}m  난이도 {diff}\n"
            f"동반자: {companion}  출발: {departure}  희망 산행: {desired_min}분  예상 최대 소요: {walk_max}분\n"
            f"날씨: 강수 {rainfall}mm  풍속 {wind}m/s  산불위험 {wildfire_label}\n"
            f"일몰 시각: {sunset}\n\n"
            "형식 규칙:\n"
            "- 정확히 3줄, 줄바꿈으로만 구분 (번호·불릿 없음)\n"
            "- 각 줄 앞에 관련 이모지 1개\n"
            "- 각 줄은 한 문장, 구체적 행동 권고로 끝내기\n"
            "- 일몰 시간과 출발·소요 시간을 비교해 귀가 가능 여부 반드시 포함\n"
        )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=200),
        )
        return response.text.strip()

    except Exception:
        return None
