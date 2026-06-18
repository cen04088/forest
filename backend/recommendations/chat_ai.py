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

    if mountain.get("name"):
        diff = {"easy": "초급", "medium": "중급", "hard": "고급"}.get(mountain.get("difficulty", ""), "")
        system += (
            f"\n\n[현재 선택된 산]\n"
            f"산: {mountain['name']} ({mountain.get('region', '')})  "
            f"해발: {mountain.get('elevation_m', '-')}m  난이도: {diff}\n"
            f"소요: {mountain.get('walk_time_min', '-')}~{mountain.get('walk_time_max', '-')}분"
        )
    if weather.get("temperature_c") is not None:
        system += (
            f"\n\n[현재 날씨]\n"
            f"기온 {weather.get('temperature_c')}°C  "
            f"강수 {weather.get('rainfall_mm', 0)}mm  "
            f"풍속 {weather.get('wind_speed_ms', 0)}m/s"
        )

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

    return "\n".join(parts)


def get_chat_response(messages: list, context: dict) -> str:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "AI 기능을 사용하려면 GEMINI_API_KEY 환경변수를 설정해 주세요."

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
