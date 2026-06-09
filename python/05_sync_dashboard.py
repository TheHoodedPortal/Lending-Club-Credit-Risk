"""
05_sync_dashboard.py
--------------------
Embed output/dashboard_model.json into index.html.

Run this after 04_reserve.ipynb is executed. The dashboard then consumes the
same JSON payload that the reserve notebook exported, instead of relying on
hand-copied model constants.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "output" / "dashboard_model.json"
INDEX = ROOT / "index.html"

START = '<script id="dashboard-model" type="application/json">'
END = "</script>"


def main() -> None:
    payload = json.loads(MODEL.read_text(encoding="utf-8"))
    embedded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    block = f"{START}{embedded}{END}"

    html = INDEX.read_text(encoding="utf-8")
    pattern = re.compile(
        re.escape(START) + r".*?" + re.escape(END),
        flags=re.DOTALL,
    )

    if pattern.search(html):
        html = pattern.sub(block, html, count=1)
    else:
        html = html.replace("\n<script>\n", f"\n{block}\n<script>\n", 1)

    INDEX.write_text(html, encoding="utf-8")
    print(f"Embedded {MODEL.relative_to(ROOT)} into {INDEX.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
