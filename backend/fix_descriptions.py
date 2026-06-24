import re
import sys

src = open("recommendations/mountain_data.py", encoding="utf-8").read()

def clean_desc(text):
    # &lt;...&gt; 앞부분 태그 제거
    text = re.sub(r"&lt;[^&]*?&gt;\s*", "", text)
    # 남아있는 HTML 엔티티 변환
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").replace("&nbsp;", " ")
    # 숫자 1개로 끝나는 잘림 제거 (예: "...장벽이다. 1")
    text = re.sub(r"\s+\d+$", "", text.rstrip())
    # 문장 중간 잘림 — 마침표/느낌표/물음표로 끝나지 않으면 마지막 완전한 문장까지만
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    if sentences and not re.search(r"[.!?\"']$", text.strip()):
        # 마지막 문장이 잘렸다면 제거
        sentences = sentences[:-1]
    result = " ".join(sentences).strip() if sentences else text.strip()
    return result if result else text.strip()

def replace_desc(m):
    raw = m.group(1)
    cleaned = clean_desc(raw)
    return f'"description": "{cleaned}"'

fixed = re.sub(r'"description":\s*"((?:[^"\\]|\\.)*)"', replace_desc, src)

open("recommendations/mountain_data.py", "w", encoding="utf-8").write(fixed)
print("done")
