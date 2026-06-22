"""
소방청 전국 산악사고 현황(2024) 기반 ML 위험도 예측 모델

데이터: 소방청_전국 산악사고 현황_20241231.csv (10,134건)
모델:
  - Random Forest 분류기 ① 사고유형 (부상사고/조난수색/질환/기타)
  - Random Forest 분류기 ② 중증도 (high/medium/low)
  - 1인당 사고율 위험 지수 (사고건수 ÷ 추정 등산객 수)

등산객 추정 근거:
  - 시간대별 비율: 산림청 등산 실태조사 기반 오전 집중 패턴
  - 월별 비율: 국립공원공단 탐방객 통계 기반 (봄·가을 피크)
  - 요일별 비율: 주말이 평일 대비 약 3배 (설문 기반)
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

_DATA_PATH = (
    Path(__file__).parent.parent.parent
    / "data"
    / "소방청_전국 산악사고 현황_20241231.csv"
)

# ── 등산객 추정 분포 ────────────────────────────────────────────────────────────
# 시간대별 등산객 비율 (24시간 합계 = 1.0)
# 출처: 산림청 등산 실태조사 — 오전 7-11시 집중, 오후 급감
_HOURLY_HIKER = {
    0: 0.002, 1: 0.001, 2: 0.001, 3: 0.002, 4: 0.005, 5: 0.014,
    6: 0.034, 7: 0.075, 8: 0.115, 9: 0.135, 10: 0.130, 11: 0.113,
    12: 0.087, 13: 0.077, 14: 0.065, 15: 0.050, 16: 0.040, 17: 0.025,
    18: 0.013, 19: 0.007, 20: 0.004, 21: 0.002, 22: 0.001, 23: 0.001,
}  # 합계 ≈ 1.0

# 월별 등산객 비율 (12개월 합계 = 1.0)
# 출처: 국립공원공단 탐방객 통계 — 5월·10월 최다, 2월 최소
_MONTHLY_HIKER = {
    1: 0.052,  2: 0.042,  3: 0.078,  4: 0.122,  5: 0.132,  6: 0.083,
    7: 0.073,  8: 0.091,  9: 0.106,  10: 0.118, 11: 0.067, 12: 0.046,
}  # 합계 = 1.010 → _normalize 처리

# 요일별 등산객 비율 (1주 합계 = 1.0)
# 출처: 주말 등산객이 평일 대비 약 3배 (산림청 실태조사)
_WEEKDAY_HIKER = {
    0: 0.087,   # 월
    1: 0.080,   # 화
    2: 0.080,   # 수
    3: 0.080,   # 목
    4: 0.110,   # 금 (반차 등 영향)
    5: 0.262,   # 토
    6: 0.301,   # 일
}  # 합계 ≈ 1.0


def _normalize(d: dict) -> dict:
    total = sum(d.values())
    return {k: v / total for k, v in d.items()}


_HOURLY_HIKER  = _normalize(_HOURLY_HIKER)
_MONTHLY_HIKER = _normalize(_MONTHLY_HIKER)
_WEEKDAY_HIKER = _normalize(_WEEKDAY_HIKER)


# ── 전역 상태 ──────────────────────────────────────────────────────────────────
_type_clf: RandomForestClassifier | None = None
_sev_clf:  RandomForestClassifier | None = None
_hourly_per_capita:  dict = {}   # 시간 → 1인당 사고율 (0~1 정규화)
_monthly_per_capita: dict = {}   # 월   → 1인당 사고율 (0~1 정규화)
_weekday_per_capita: dict = {}   # 요일 → 1인당 사고율 (0~1 정규화)
_initialized: bool = False


# ── 레이블 변환 ────────────────────────────────────────────────────────────────

def _severity_label(result: str) -> str:
    if not isinstance(result, str):
        return "low"
    if "항공대" in result or "인명구조" in result:
        return "high"
    if "구급대" in result:
        return "medium"
    return "low"


def _accident_category(code: str) -> str:
    if not isinstance(code, str):
        return "기타"
    if "사고부상" in code:
        return "부상사고"
    if "조난" in code or "수색" in code:
        return "조난수색"
    if "질환" in code:
        return "질환"
    return "기타"


# ── 피처 생성 ──────────────────────────────────────────────────────────────────

def _make_features(month: int, hour: int, weekday: int) -> np.ndarray:
    is_weekend = int(weekday >= 5)
    time_bin = (
        0 if hour <= 6 else
        1 if hour <= 10 else
        2 if hour <= 14 else
        3 if hour <= 17 else
        4 if hour <= 20 else 5
    )
    season = (
        0 if month in (3, 4, 5) else
        1 if month in (6, 7, 8) else
        2 if month in (9, 10, 11) else 3
    )
    return np.array([[month, hour, weekday, is_weekend, time_bin, season]])


def _per_capita_rate(counts: pd.Series, hiker_weights: dict) -> dict:
    """
    사고 건수를 추정 등산객 비율로 나눠 1인당 사고율 계산 → 0~1 정규화.
    등산객이 많은 시간대에 사고도 많으면 낮게, 등산객 적은데 사고 많으면 높게.
    """
    rate = {}
    for idx, cnt in counts.items():
        hiker = hiker_weights.get(idx, 1e-6)
        rate[idx] = cnt / hiker
    # 0~1 정규화
    vals = list(rate.values())
    mn, mx = min(vals), max(vals)
    return {k: (v - mn) / (mx - mn + 1e-9) for k, v in rate.items()}


# ── 모델 초기화 (1회만 실행) ───────────────────────────────────────────────────

def _initialize() -> None:
    global _type_clf, _sev_clf
    global _hourly_per_capita, _monthly_per_capita, _weekday_per_capita
    global _initialized
    if _initialized:
        return

    try:
        df = pd.read_csv(_DATA_PATH, encoding="cp949")
    except Exception:
        _initialized = True
        return

    df["날짜"] = pd.to_datetime(df["신고년월일"], errors="coerce")
    df = df.dropna(subset=["날짜"])
    df["월"]  = df["날짜"].dt.month
    df["시간"] = pd.to_numeric(df["신고시각"].str[:2], errors="coerce")
    df = df[df["시간"].between(0, 23)].copy()
    df["시간"] = df["시간"].astype(int)
    df["요일"] = df["날짜"].dt.dayofweek
    df["주말"] = (df["요일"] >= 5).astype(int)
    df["시간대"] = df["시간"].apply(
        lambda h: 0 if h<=6 else 1 if h<=10 else 2 if h<=14 else 3 if h<=17 else 4 if h<=20 else 5
    )
    df["계절"] = df["월"].apply(
        lambda m: 0 if m in (3,4,5) else 1 if m in (6,7,8) else 2 if m in (9,10,11) else 3
    )
    df["acc_type"] = df["사고원인코드명_사고종별"].apply(_accident_category)
    df["severity"] = df["처리결과코드"].apply(_severity_label)

    # ─ Random Forest 학습 ────────────────────────────────────────────────────
    FEATURES = ["월", "시간", "요일", "주말", "시간대", "계절"]
    X = df[FEATURES].values

    _type_clf = RandomForestClassifier(
        n_estimators=150, max_depth=8, random_state=42, class_weight="balanced",
    )
    _type_clf.fit(X, df["acc_type"].values)

    _sev_clf = RandomForestClassifier(
        n_estimators=150, max_depth=8, random_state=42, class_weight="balanced",
    )
    _sev_clf.fit(X, df["severity"].values)

    # ─ 1인당 사고율 계산 (C안 핵심) ─────────────────────────────────────────
    # 사고 건수 ÷ 추정 등산객 비율 → 등산객이 적은 시간대에 사고가 많으면 위험
    _hourly_per_capita  = _per_capita_rate(df.groupby("시간").size(), _HOURLY_HIKER)
    _monthly_per_capita = _per_capita_rate(df.groupby("월").size(),   _MONTHLY_HIKER)
    _weekday_per_capita = _per_capita_rate(df.groupby("요일").size(), _WEEKDAY_HIKER)

    _initialized = True


# ── 공개 인터페이스 ────────────────────────────────────────────────────────────

def predict_accident_risk(month: int, hour: int, weekday: int) -> dict:
    """
    1인당 사고율 기반 산악 위험도 예측

    Args:
        month   : 1~12
        hour    : 0~23
        weekday : 0=월 … 6=일

    Returns:
        risk_index         : 0.0~1.0 (1인당 사고율 기준, 높을수록 위험)
        ml_safety_score    : 0.0~1.0 (안전 점수 반영값)
        severity_proba     : {'high': 0.12, 'medium': 0.45, 'low': 0.43}
        type_proba         : {'부상사고': 0.47, '조난수색': 0.31, ...}
        top_type           : 가장 확률 높은 사고 유형
        warning            : 경고 메시지
        risk_breakdown     : 시간대·월·요일별 1인당 위험 지수 (설명용)
    """
    _initialize()

    if not _initialized or _type_clf is None:
        return {
            "risk_index": 0.5, "ml_safety_score": 0.5,
            "severity_proba": {}, "type_proba": {}, "top_type": "", "warning": "",
        }

    X = _make_features(month, hour, weekday)
    type_proba = dict(zip(_type_clf.classes_, _type_clf.predict_proba(X)[0].tolist()))
    sev_proba  = dict(zip(_sev_clf.classes_,  _sev_clf.predict_proba(X)[0].tolist()))

    # 1인당 사고율: 시간(50%) + 월(35%) + 요일(15%) 가중 합산
    h_risk  = _hourly_per_capita.get(hour, 0.5)
    m_risk  = _monthly_per_capita.get(month, 0.5)
    wd_risk = _weekday_per_capita.get(weekday, 0.5)
    risk_index = round(h_risk * 0.50 + m_risk * 0.35 + wd_risk * 0.15, 3)
    ml_safety_score = round(1.0 - risk_index, 3)

    top_type = max(type_proba, key=type_proba.get)

    _type_msg = {
        "부상사고": "실족·추락 사고",
        "조난수색": "길잃음·조난 사고",
        "질환":    "탈진·저체온 등 신체 이상",
        "기타":    "기타 산악 사고",
    }
    if risk_index >= 0.70:
        level = "1인당 사고율 최고 구간"
    elif risk_index >= 0.45:
        level = "1인당 사고율 높음"
    elif risk_index >= 0.20:
        level = "주의"
    else:
        level = "상대적 안전 구간"

    warning = f"이 시간대 {_type_msg.get(top_type, '산악 사고')} 주의 ({level})"

    return {
        "risk_index": risk_index,
        "ml_safety_score": ml_safety_score,
        "severity_proba": {k: round(v, 3) for k, v in sev_proba.items()},
        "type_proba":     {k: round(v, 3) for k, v in type_proba.items()},
        "top_type": top_type,
        "warning":  warning,
        "risk_breakdown": {
            "hourly_risk":  round(h_risk, 3),
            "monthly_risk": round(m_risk, 3),
            "weekday_risk": round(wd_risk, 3),
        },
    }
