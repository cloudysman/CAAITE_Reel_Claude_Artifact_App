"""Liệt kê mọi chữ người xem thấy (để soát văn theo humanizer và "Signs of AI writing").

Đọc: compositions/frames/*.html, compositions/watermark.html (chữ trong thẻ, bỏ <script>, <style>, thuộc tính),
compositions/captions.html (các viên phụ đề), thumbnail/thumb.html, DANG_BAI_tieu_de_mo_ta.txt, DANG_BAI/1-TikTok.txt.
Ghi script/soat_van/chu_tren_hinh.txt (mỗi dòng một khối chữ, có tên tệp) và in thống kê dấu câu nên tránh
(gạch ngang dài, ngoặc kép cong, ba chấm một ký tự, ký tự ẩn).
Cách dùng: python src_build/liet_ke_chu.py
"""
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
CAM = re.compile(r"[—–“”‘’…​-‏⁠﻿]")


class Chu(HTMLParser):
    KHOI = {"div", "p", "h1", "h2", "h3", "li", "br", "section", "figure", "figcaption", "td", "th", "tr"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.bo = 0
        self.dong, self.cur = [], []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.bo += 1
        elif tag in self.KHOI:
            self._xong()

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.bo -= 1
        elif tag in self.KHOI:
            self._xong()

    def handle_data(self, data):
        if not self.bo:
            self.cur.append(data)

    def _xong(self):
        t = re.sub(r"\s+", " ", "".join(self.cur)).strip()
        if t:
            self.dong.append(t)
        self.cur = []


def chu_html(p: Path) -> list[str]:
    t = p.read_text(encoding="utf-8")
    m = re.search(r"<template[^>]*>(.*)</template>", t, re.S)
    k = Chu()
    k.feed(m.group(1) if m else t)
    k._xong()
    return k.dong


def main() -> None:
    out, canh_bao = [], []
    tep = sorted((ROOT / "compositions" / "frames").glob("*.html")) + [ROOT / "compositions" / "watermark.html",
                                                                      ROOT / "compositions" / "captions.html",
                                                                      ROOT / "thumbnail" / "thumb.html"]
    for p in tep:
        if not p.exists():
            continue
        dong = chu_html(p)
        out.append(f"== {p.relative_to(ROOT).as_posix()} ({len(dong)} khối)")
        out += [f"  {d}" for d in dong]
        for d in dong:
            for m in CAM.finditer(d):
                canh_bao.append(f"{p.name}: U+{ord(m.group()):04X} trong '{d}'")
    for p in (ROOT / "DANG_BAI_tieu_de_mo_ta.txt", ROOT / "DANG_BAI" / "1-TikTok.txt"):
        if p.exists():
            t = p.read_text(encoding="utf-8")
            out.append(f"== {p.relative_to(ROOT).as_posix()}")
            out += [f"  {d}" for d in t.splitlines() if d.strip()]
            for m in CAM.finditer(t):
                canh_bao.append(f"{p.name}: U+{ord(m.group()):04X} ở vị trí {m.start()}")
    dst = ROOT / "script" / "soat_van" / "chu_tren_hinh.txt"
    dst.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{sum(1 for x in out if x.startswith('  '))} khối chữ -> {dst.relative_to(ROOT)}")
    print("ký tự nên tránh:", canh_bao or "không")


if __name__ == "__main__":
    main()
