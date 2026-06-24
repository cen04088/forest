import re, sys
sys.stdout.reconfigure(encoding="utf-8")

text = open("recommendations/mountain_data.py", encoding="utf-8").read()
blocks = re.split(r"(?=\{\s*\"id\")", text)

for block in blocks:
    m = re.search(r'"name": "([^"]+)"', block)
    d = re.search(r'"description": "((?:[^"\\]|\\.)*?)"', block)
    if not m or not d:
        continue
    name = m.group(1)
    desc = d.group(1)
    clean = desc.strip()
    if not clean or clean in ("&#160;", " ") or len(clean) < 5:
        print(f"EMPTY : {name}")
    elif "&#160;" in clean or "gt;" in clean or "lt;" in clean:
        print(f"HTML  : {name} | {clean[:80]}")
    elif len(clean) < 30:
        print(f"SHORT : {name} | {clean}")
