import random
import string
import time

_MAX_TRAIL_POINTS = 200

# 읽기 쉬운 문자만 사용 (0/O/I/1 제외)
_CODE_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_code() -> str:
    """충돌 없는 6자리 공유 코드를 생성한다."""
    from .models import SafeLinkSession
    for _ in range(20):
        code = "".join(random.choices(_CODE_CHARS, k=6))
        if not SafeLinkSession.objects.filter(share_code=code, status="hiking").exists():
            return code
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=8))


def _to_dict(session, include_trail=False) -> dict:
    data = {
        "id": str(session.id),
        "share_code": session.share_code,
        "course_name": session.course_name,
        "mountain": session.mountain,
        "safety_label": session.safety_label,
        "safety_decision": session.safety_decision,
        "risk_factors": session.risk_factors,
        "distance_km": session.distance_km,
        "duration_min": session.duration_min,
        "course_lat": session.course_lat,
        "course_lng": session.course_lng,
        "current_lat": session.current_lat,
        "current_lng": session.current_lng,
        "location_ts": session.location_ts,
        "status": session.status,
        "created_at": int(session.created_at.timestamp()),
    }
    if include_trail:
        from .models import LocationLog
        logs = list(
            LocationLog.objects.filter(session=session)
            .order_by("recorded_at")
            .values("lat", "lng", "recorded_at")
        )
        data["trail"] = logs[-_MAX_TRAIL_POINTS:]
    return data


def create(course: dict) -> dict:
    from .models import SafeLinkSession
    session = SafeLinkSession.objects.create(
        share_code=_generate_code(),
        course_name=course.get("name", ""),
        mountain=course.get("mountain", ""),
        safety_label=course.get("safety_label", ""),
        safety_decision=course.get("safety_decision", ""),
        risk_factors=(course.get("risk_factors") or [])[:3],
        distance_km=course.get("distance_km"),
        duration_min=course.get("duration_min", 0),
        course_lat=course.get("lat"),
        course_lng=course.get("lng"),
        current_lat=course.get("lat"),
        current_lng=course.get("lng"),
    )
    return _to_dict(session)


def get(sid: str) -> dict | None:
    from .models import SafeLinkSession
    try:
        return _to_dict(SafeLinkSession.objects.get(pk=sid), include_trail=True)
    except (SafeLinkSession.DoesNotExist, Exception):
        return None


def get_by_code(code: str) -> dict | None:
    from .models import SafeLinkSession
    clean = code.upper().strip()
    if not clean:
        return None
    try:
        session = SafeLinkSession.objects.get(share_code=clean)
        return _to_dict(session, include_trail=True)
    except SafeLinkSession.DoesNotExist:
        return None
    except Exception:
        return None


def update_location(sid: str, lat: float, lng: float) -> dict | None:
    from .models import SafeLinkSession, LocationLog
    updated = SafeLinkSession.objects.filter(pk=sid).update(
        current_lat=lat,
        current_lng=lng,
        location_ts=int(time.time()),
    )
    if not updated:
        return None
    try:
        session = SafeLinkSession.objects.get(pk=sid)
        LocationLog.objects.create(session=session, lat=lat, lng=lng, recorded_at=int(time.time()))
        return _to_dict(session)
    except SafeLinkSession.DoesNotExist:
        return None


def end_session(sid: str) -> dict | None:
    from .models import SafeLinkSession
    updated = SafeLinkSession.objects.filter(pk=sid).update(status="ended")
    if not updated:
        return None
    try:
        return _to_dict(SafeLinkSession.objects.get(pk=sid))
    except SafeLinkSession.DoesNotExist:
        return None
