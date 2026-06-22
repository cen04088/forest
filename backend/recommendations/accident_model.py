from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ACCIDENT_DATASET_NAMES = (
    "소방청_전국 산악사고 현황_20241231.csv",
    "전국 산악사고 구조활동현황(2010_2016).csv",
    "전국 산악사고 구조활동현황(2017~2021).csv",
    "전국 산악사고 현황(2020년).csv",
    "전국 산악사고 현황(2022~2023년).csv",
)

_HOURLY_HIKER = {
    0: 0.002, 1: 0.001, 2: 0.001, 3: 0.002, 4: 0.005, 5: 0.014,
    6: 0.034, 7: 0.075, 8: 0.115, 9: 0.135, 10: 0.130, 11: 0.113,
    12: 0.087, 13: 0.077, 14: 0.065, 15: 0.050, 16: 0.040, 17: 0.025,
    18: 0.013, 19: 0.007, 20: 0.004, 21: 0.002, 22: 0.001, 23: 0.001,
}
_MONTHLY_HIKER = {
    1: 0.052, 2: 0.042, 3: 0.078, 4: 0.122, 5: 0.132, 6: 0.083,
    7: 0.073, 8: 0.091, 9: 0.106, 10: 0.118, 11: 0.067, 12: 0.046,
}
_WEEKDAY_HIKER = {
    0: 0.087, 1: 0.080, 2: 0.080, 3: 0.080, 4: 0.110, 5: 0.262, 6: 0.301,
}


def _normalize(weights: dict) -> dict:
    total = sum(weights.values())
    return {key: value / total for key, value in weights.items()}


_HOURLY_HIKER = _normalize(_HOURLY_HIKER)
_MONTHLY_HIKER = _normalize(_MONTHLY_HIKER)
_WEEKDAY_HIKER = _normalize(_WEEKDAY_HIKER)

_type_clf: RandomForestClassifier | None = None
_sev_clf: RandomForestClassifier | None = None
_hourly_per_capita: dict = {}
_monthly_per_capita: dict = {}
_weekday_per_capita: dict = {}
_training_summary: dict = {}
_initialized = False


def _severity_label(result: str) -> str:
    if not isinstance(result, str):
        return "low"
    if "항공대" in result or "인명구조" in result or "인명검색" in result:
        return "high"
    if "구급대" in result:
        return "medium"
    return "low"


def _accident_category(code: str) -> str:
    if not isinstance(code, str):
        return "기타"
    if "실족" in code or "추락" in code or "사고부상" in code:
        return "부상사고"
    if "조난" in code or "수색" in code or "일반조난" in code:
        return "조난수색"
    if "질환" in code or "탈진" in code or "탈수" in code or "개인질환" in code:
        return "질환"
    return "기타"


def _make_features(month: int, hour: int, weekday: int) -> np.ndarray:
    is_weekend = int(weekday >= 5)
    time_bin = 0 if hour <= 6 else 1 if hour <= 10 else 2 if hour <= 14 else 3 if hour <= 17 else 4 if hour <= 20 else 5
    season = 0 if month in (3, 4, 5) else 1 if month in (6, 7, 8) else 2 if month in (9, 10, 11) else 3
    return np.array([[month, hour, weekday, is_weekend, time_bin, season]])


def _per_capita_rate(counts: pd.Series, hiker_weights: dict) -> dict:
    rate = {idx: cnt / hiker_weights.get(idx, 1e-6) for idx, cnt in counts.items()}
    vals = list(rate.values()) or [0]
    mn, mx = min(vals), max(vals)
    return {k: (v - mn) / (mx - mn + 1e-9) for k, v in rate.items()}


def _read_csv(path: Path) -> pd.DataFrame:
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")


def _first_existing(raw: pd.DataFrame, names: tuple[str, ...], default="") -> pd.Series:
    for name in names:
        if name in raw.columns:
            return raw[name]
    return pd.Series([default] * len(raw), index=raw.index)


def _load_accident_dataset(path: Path) -> pd.DataFrame:
    raw = _read_csv(path)
    if not {"신고년월일", "신고시각", "사고원인코드명_사고종별"}.issubset(raw.columns):
        return pd.DataFrame()

    accident_cause = _first_existing(raw, ("사고원인",), "")
    if "사고원인" in raw.columns:
        raw = raw[accident_cause.astype(str).str.strip().eq("산악")].copy()

    return pd.DataFrame(
        {
            "date": raw["신고년월일"],
            "time": raw["신고시각"],
            "accident_type": raw["사고원인코드명_사고종별"],
            "result": _first_existing(raw, ("처리결과코드",), ""),
            "rescue_count": _first_existing(raw, ("구조인원",), 0),
            "source": path.name,
        }
    )


def _load_training_rows() -> pd.DataFrame:
    frames = []
    source_counts = {}
    for name in ACCIDENT_DATASET_NAMES:
        path = DATA_DIR / name
        if not path.exists():
            continue
        frame = _load_accident_dataset(path)
        if not frame.empty:
            frames.append(frame)
            source_counts[path.name] = len(frame)

    if not frames:
        return pd.DataFrame()

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=["date", "time", "accident_type"])
    df = df.drop_duplicates(subset=["date", "time", "accident_type", "result", "source"])
    df.attrs["source_counts"] = source_counts
    return df


def _prepare_training_frame(rows: pd.DataFrame) -> pd.DataFrame:
    df = rows.copy()
    df["date"] = pd.to_datetime(df["date"].astype(str).str.strip(), errors="coerce")
    df = df.dropna(subset=["date"])

    df["month"] = df["date"].dt.month
    df["hour"] = pd.to_numeric(df["time"].astype(str).str.extract(r"^(\d{1,2})")[0], errors="coerce")
    df = df[df["hour"].between(0, 23)].copy()
    df["hour"] = df["hour"].astype(int)
    df["weekday"] = df["date"].dt.dayofweek
    df["is_weekend"] = (df["weekday"] >= 5).astype(int)
    df["time_bin"] = df["hour"].apply(
        lambda h: 0 if h <= 6 else 1 if h <= 10 else 2 if h <= 14 else 3 if h <= 17 else 4 if h <= 20 else 5
    )
    df["season"] = df["month"].apply(
        lambda m: 0 if m in (3, 4, 5) else 1 if m in (6, 7, 8) else 2 if m in (9, 10, 11) else 3
    )
    df["acc_type"] = df["accident_type"].apply(_accident_category)
    df["severity"] = df["result"].apply(_severity_label)
    return df


def _initialize() -> None:
    global _type_clf, _sev_clf
    global _hourly_per_capita, _monthly_per_capita, _weekday_per_capita
    global _training_summary, _initialized
    if _initialized:
        return

    rows = _load_training_rows()
    df = _prepare_training_frame(rows) if not rows.empty else pd.DataFrame()
    if df.empty:
        _training_summary = {"trained": False, "rows": 0, "sources": {}}
        _initialized = True
        return

    features = ["month", "hour", "weekday", "is_weekend", "time_bin", "season"]
    X = df[features].values

    _type_clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, class_weight="balanced")
    _type_clf.fit(X, df["acc_type"].values)

    _sev_clf = RandomForestClassifier(n_estimators=150, max_depth=8, random_state=42, class_weight="balanced")
    _sev_clf.fit(X, df["severity"].values)

    _hourly_per_capita = _per_capita_rate(df.groupby("hour").size(), _HOURLY_HIKER)
    _monthly_per_capita = _per_capita_rate(df.groupby("month").size(), _MONTHLY_HIKER)
    _weekday_per_capita = _per_capita_rate(df.groupby("weekday").size(), _WEEKDAY_HIKER)
    _training_summary = {
        "trained": True,
        "rows": int(len(df)),
        "sources": rows.attrs.get("source_counts", {}),
        "year_range": [int(df["date"].dt.year.min()), int(df["date"].dt.year.max())],
    }
    _initialized = True


def get_accident_model_training_summary() -> dict:
    _initialize()
    return dict(_training_summary)


def predict_accident_risk(month: int, hour: int, weekday: int) -> dict:
    _initialize()

    if not _initialized or _type_clf is None or _sev_clf is None:
        return {
            "risk_index": 0.5,
            "ml_safety_score": 0.5,
            "severity_proba": {},
            "type_proba": {},
            "top_type": "",
            "warning": "",
            "training": dict(_training_summary),
        }

    X = _make_features(month, hour, weekday)
    type_proba = dict(zip(_type_clf.classes_, _type_clf.predict_proba(X)[0].tolist()))
    sev_proba = dict(zip(_sev_clf.classes_, _sev_clf.predict_proba(X)[0].tolist()))

    h_risk = _hourly_per_capita.get(hour, 0.5)
    m_risk = _monthly_per_capita.get(month, 0.5)
    wd_risk = _weekday_per_capita.get(weekday, 0.5)
    risk_index = round(h_risk * 0.50 + m_risk * 0.35 + wd_risk * 0.15, 3)
    ml_safety_score = round(1.0 - risk_index, 3)

    top_type = max(type_proba, key=type_proba.get)
    type_msg = {
        "부상사고": "실족·추락 사고",
        "조난수색": "길잃음·수색 사고",
        "질환": "탈진·저체온 등 신체 이상",
        "기타": "기타 산악 사고",
    }
    if risk_index >= 0.70:
        level = "1인당 사고율 최고 구간"
    elif risk_index >= 0.45:
        level = "1인당 사고율 높음"
    elif risk_index >= 0.20:
        level = "주의"
    else:
        level = "상대적 안전 구간"

    return {
        "risk_index": risk_index,
        "ml_safety_score": ml_safety_score,
        "severity_proba": {k: round(v, 3) for k, v in sev_proba.items()},
        "type_proba": {k: round(v, 3) for k, v in type_proba.items()},
        "top_type": top_type,
        "warning": f"이 시간대 {type_msg.get(top_type, '산악 사고')} 주의 ({level})",
        "risk_breakdown": {
            "hourly_risk": round(h_risk, 3),
            "monthly_risk": round(m_risk, 3),
            "weekday_risk": round(wd_risk, 3),
        },
        "training": dict(_training_summary),
    }
