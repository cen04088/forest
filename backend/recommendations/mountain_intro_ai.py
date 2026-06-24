import os


def get_or_generate_intro(mountain_name: str, raw_summary: str, selection_reason: str = "") -> str:
    """DB에서 AI 변환 소개문 조회; 없으면 Gemini로 생성 후 저장."""
    from .models import MountainIntro

    stored = MountainIntro.objects.filter(mountain_name=mountain_name).first()
    if stored:
        return stored.intro

    intro = _generate(mountain_name, raw_summary, selection_reason)
    if intro:
        MountainIntro.objects.update_or_create(
            mountain_name=mountain_name,
            defaults={"intro": intro, "raw_summary": raw_summary[:1000]},
        )
    return intro or raw_summary  # 생성 실패 시 원문 반환


def _generate(name: str, raw_summary: str, selection_reason: str = "") -> str | None:
    gms_key = os.environ.get("GMS_KEY", "").strip()
    api_key = gms_key or os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or not raw_summary:
        return None

    try:
        from google import genai
        from google.genai import types

        extra = f"\n선정 이유 참고: {selection_reason[:200]}" if selection_reason else ""

        prompt = (
            f"아래 산림청 공식 설명을 읽기 쉬운 한 문단으로 바꿔주세요.\n\n"
            f"산 이름: {name}\n"
            f"원문: {raw_summary[:600]}{extra}\n\n"
            "규칙:\n"
            "- 3~4문장 이내\n"
            "- 등산 좋아하는 친구가 추천하듯 친근하고 생동감 있는 말투\n"
            "- 어려운 한자·고어 표현 제거, 쉬운 현대 한국어로\n"
            "- 산의 가장 인상적인 특징 1~2가지만 부각\n"
            "- 정보 나열 금지, 감성적으로 묘사\n"
            "- 출력은 문단 하나만, 라벨·제목 없이\n"
        )

        if gms_key:
            client = genai.Client(
                api_key=api_key,
                http_options={"base_url": "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com/"},
            )
        else:
            client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=prompt,
            config=types.GenerateContentConfig(max_output_tokens=180),
        )
        return (response.text or "").strip() or None

    except Exception:
        return None
