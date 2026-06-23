import re


def mountain_key(name, region=""):
    raw = f"{name or ''}_{region or ''}"
    compact = re.sub(r"\s+", "", raw)
    return compact or str(name or "")


def with_mountain_identity(mountain):
    item = dict(mountain)
    item["mountain_key"] = item.get("mountain_key") or mountain_key(
        item.get("name", ""),
        item.get("region", ""),
    )
    return item
