import time
import uuid as _uuid

_sessions: dict = {}


def create(course: dict) -> dict:
    sid = str(_uuid.uuid4())
    _sessions[sid] = {
        "id": sid,
        "course_name": course.get("name", ""),
        "mountain": course.get("mountain", ""),
        "safety_label": course.get("safety_label", ""),
        "safety_decision": course.get("safety_decision", ""),
        "risk_factors": (course.get("risk_factors") or [])[:3],
        "distance_km": course.get("distance_km", 0),
        "duration_min": course.get("duration_min", 0),
        "course_lat": course.get("lat"),
        "course_lng": course.get("lng"),
        "route_geometry": (course.get("route_geometry") or [])[:80],
        "current_lat": course.get("lat"),
        "current_lng": course.get("lng"),
        "location_ts": None,
        "alerts": [],
        "status": "hiking",
        "created_at": int(time.time()),
    }
    return _sessions[sid]


def get(sid: str) -> dict | None:
    return _sessions.get(sid)


def update_location(sid: str, lat: float, lng: float) -> dict | None:
    session = _sessions.get(sid)
    if not session:
        return None
    session["current_lat"] = lat
    session["current_lng"] = lng
    session["location_ts"] = int(time.time())
    return session


def end_session(sid: str) -> dict | None:
    session = _sessions.get(sid)
    if not session:
        return None
    session["status"] = "ended"
    return session
