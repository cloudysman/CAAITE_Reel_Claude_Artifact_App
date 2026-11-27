"""Đặt khoảng nghỉ riêng trước các câu mở đoạn trong src/c4_ghep.py (chạy trong ~/HieuDT/claude_app_reel trước c4)."""
import re
from pathlib import Path

NGHI = {"B2S2": 1.2, "B8S1": 0.4}
p = Path("src/c4_ghep.py")
s = p.read_text(encoding="utf-8")
s = re.sub(r"^NGHI_RIENG = \{.*?\}", "NGHI_RIENG = " + repr(NGHI).replace("'", '"'), s, count=1, flags=re.M)
p.write_text(s, encoding="utf-8")
print([l[:120] for l in s.splitlines() if l.startswith("NGHI_RIENG")])
