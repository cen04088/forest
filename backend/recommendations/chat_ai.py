import os

_SYSTEM = """당신은 올라(Olla) 앱의 산행 안전 AI 어시스턴트입니다.
한국의 등산 안전, 산행 코스, 날씨 대응, 장비, 응급처치에 대해 친절하고 전문적으로 답변합니다.
답변은 3~5문장 이내로 간결하게 작성하고, 안전을 최우선으로 강조하세요.
모르는 내용은 추측하지 말고 "현장 관리소나 국립공원 홈페이지를 확인하세요"처럼 안내하세요.
아래 [참고 정보]가 제공된 경우 반드시 활용하여 더 구체적이고 정확한 답변을 제공하세요."""


def _build_system(context: dict, rag_context: str = "") -> str:
    system = _SYSTEM
    mountain = context.get("mountain") or {}
    weather = context.get("weather") or {}

    # 현재 시각
    if context.get("now"):
        system += f"\n\n[현재 시각]\n{context['now']}"

    # 사용자 프로필
    profile = context.get("userProfile") or {}
    if profile:
        exp_map = {"beginner": "초보", "intermediate": "중급", "expert": "숙련"}
        comp_map = {"solo": "혼자", "family": "가족", "vulnerable": "어린이·노약자 동반"}
        int_map = {"light": "가볍게", "moderate": "보통", "hard": "강하게"}
        system += (
            f"\n\n[사용자 프로필]\n"
            f"경험: {exp_map.get(profile.get('experience', ''), profile.get('experience', '-'))}  "
            f"동반자: {comp_map.get(profile.get('companion', ''), profile.get('companion', '-'))}  "
            f"산행 강도: {int_map.get(profile.get('intensity', ''), '-')}\n"
            f"가능 시간: {profile.get('availableMinutes', '-')}분  "
            f"희망 등산 시간: {profile.get('desiredHikingMinutes', '-')}분  "
            f"최대 거리: {profile.get('maxDistanceKm', '-')}km\n"
            f"출발 예정: {profile.get('departureDate', '')} {profile.get('departureTime', '')}"
        )

    if mountain.get("name"):
        diff = {"easy": "초급", "medium": "중급", "hard": "고급"}.get(mountain.get("difficulty", ""), "")
        system += (
            f"\n\n[현재 선택된 산]\n"
            f"산: {mountain['name']} ({mountain.get('region', '')})  "
            f"해발: {mountain.get('elevation_m', '-')}m  난이도: {diff}\n"
            f"소요: {mountain.get('walk_time_min', '-')}~{mountain.get('walk_time_max', '-')}분"
        )

    if weather.get("temperature_c") is not None:
        sun = context.get("sunTimes") or {}
        system += (
            f"\n\n[현재 날씨]\n"
            f"기온 {weather.get('temperature_c')}°C  "
            f"강수 {weather.get('rainfall_mm', 0)}mm  "
            f"풍속 {weather.get('wind_speed_ms', 0)}m/s"
        )
        if sun.get("sunrise") or sun.get("sunset"):
            system += f"  일출 {sun.get('sunrise', '-')}  일몰 {sun.get('sunset', '-')}"

    courses = context.get("recommendedCourses") or []
    if courses:
        diff_map = {"easy": "초급", "medium": "중급", "hard": "고급"}
        lines = []
        for c in courses[:3]:
            diff = diff_map.get(c.get("difficulty", ""), "")
            lines.append(
                f"- {c.get('name', '')} ({diff}, {c.get('distance_km', '')}km, "
                f"{c.get('duration_min', '')}분, {c.get('safety_label', '')})"
            )
        system += "\n\n[추천된 코스]\n" + "\n".join(lines)

    # 재난위험지구
    disaster_zones = context.get("disasterZones") or []
    if disaster_zones:
        lines = []
        for z in disaster_zones:
            loc = z.get("location") or z.get("district") or ""
            risk = z.get("risk_factor") or ""
            if loc:
                lines.append(f"- {loc}" + (f" ({risk})" if risk else ""))
        if lines:
            system += "\n\n[인근 재난위험지구]\n" + "\n".join(lines)

    # 실시간 안전 현황 (wildfire, landslide, NIFOS)
    safety_lines = _build_realtime_safety(context)
    if safety_lines:
        system += f"\n\n[실시간 안전 현황]\n{safety_lines}"

    # RAG 검색 결과
    if rag_context:
        system += f"\n\n[참고 정보 (RAG 검색 결과)]\n{rag_context}"

    return system


def _build_realtime_safety(context: dict) -> str:
    parts = []

    wildfire = context.get("wildfire") or {}
    risk = wildfire.get("risk", "")
    if risk in ("high", "very_high"):
        label = "매우 높음" if risk == "very_high" else "높음"
        parts.append(f"산불위험: {label} (지수 {wildfire.get('max_index', '-')})")

    landslide = context.get("landslide") or {}
    items = landslide.get("items", []) or []
    warnings = [item for item in items if item.get("risk") in ("danger", "caution")]
    if warnings:
        parts.append(f"산사태 경보: {len(warnings)}개 지역 발령 중")

    nifos = context.get("nifos_weather") or {}
    if nifos.get("ok") and nifos.get("temperature_c") is not None:
        parts.append(
            f"NIFOS 산악기상 ({nifos.get('station_name', '관측소')}): "
            f"기온 {nifos.get('temperature_c')}°C  "
            f"풍속 {nifos.get('wind_speed_ms', 0)}m/s"
        )

    nifos_dust = context.get("nifos_dust") or {}
    if nifos_dust.get("ok") and nifos_dust.get("pm25_ugm3") is not None:
        grade = nifos_dust.get("grade_pm25", "")
        parts.append(
            f"NIFOS 산림미세먼지 ({nifos_dust.get('station_name', '관측소')}): "
            f"PM2.5 {nifos_dust.get('pm25_ugm3')}㎍/m³ ({grade})"
        )

    aq = context.get("air_quality") or {}
    if aq.get("ok") and aq.get("pm25_ugm3") is not None:
        grade = aq.get("grade_pm25", "")
        parts.append(
            f"대기질 ({aq.get('sido', '')} / {aq.get('station_name', '관측소')}): "
            f"PM2.5 {aq.get('pm25_ugm3')}㎍/m³ ({grade}), "
            f"PM10 {aq.get('pm10_ugm3')}㎍/m³ ({aq.get('grade_pm10', '')})"
        )

    return "\n".join(parts)


def get_chat_response(messages: list, context: dict) -> str:
    gms_key = os.environ.get("GMS_KEY", "").strip()
    api_key = gms_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "AI 기능을 사용하려면 GMS_KEY 또는 GEMINI_API_KEY 환경변수를 설정해 주세요."

    # RAG: 마지막 사용자 메시지로 관련 문서 검색
    last_user_msg = next(
        (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
        "",
    )
    mountain_name = (context.get("mountain") or {}).get("name", "")

    rag_context = ""
    try:
        from .rag_retriever import build_rag_context
        rag_context = build_rag_context(last_user_msg, mountain_name)
    except Exception:
        pass

    try:
        from google import genai
        from google.genai import types

        if gms_key:
            client = genai.Client(
                api_key=api_key,
                http_options={"base_url": "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/"},
            )
        else:
            client = genai.Client(api_key=api_key)

        contents = []
        for msg in messages:
            role = "model" if msg.get("role") == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part(text=msg.get("content", ""))]))

        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=_build_system(context, rag_context),
                max_output_tokens=400,
            ),
        )
        return response.text.strip()

    except Exception as e:
        msg = str(e)
        if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
            return "요청이 너무 많습니다. 잠시 후(30초~1분) 다시 시도해 주세요. (API 무료 한도 초과)"
        return f"일시적인 오류가 발생했습니다. 잠시 후 다시 시도해 주세요. ({msg[:60]})"
