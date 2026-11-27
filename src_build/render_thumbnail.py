"""Render ảnh bìa dọc 1080x1920 (YouTube Shorts và TikTok) từ thumbnail/thumb.html và tự kiểm tra
(reel "Claude: cài artifact thành ứng dụng trên máy tính"; bộ render lấy từ các reel trước, phông Lexend).

Cách dùng:  python src_build/render_thumbnail.py v1 v2 --final v1 --alt v2

- Mở trang qua máy chủ HTTP cục bộ (phông chữ không tải được từ file://), chờ phông và ảnh, chụp PNG.
- Đo: hộp chữ, hộp mực từng khối, độ tương phản chữ so với nền thật (chụp lại lần hai khi ẩn nét chữ,
  lấy phân vị 95 độ sáng nền), vùng an toàn của cả hai nền tảng. Số đo lấy từ trang web thật ngày 05/10/2026
  (người nghiên cứu đo bằng Chromium, chưa đăng nhập; ứng dụng điện thoại chưa đo được):
    YouTube Shorts: ô hiển thị cắt 2:3 ở giữa (y 150-1770); trên điện thoại, tiêu đề và lượt xem phủ ở khoảng
    y 1375-1715 (căn trái, gần hết bề ngang), nút ba chấm x 848-1080 y 150-382, viên "Mới" x 30-215 y 180-295;
    TikTok: ô lưới cắt 3:4 ở giữa (y 240-1680), lượt xem x 80-535 y 1500-1607, nhãn "Đã ghim" x 53-387 y 293-413;
    chữ chính của ảnh phải nằm trong dải chung x 60-1020, y 420-1280.
- Xuất JPG < 2 MB, ảnh xem thử ở cỡ thẻ Shorts (180x320, 120x213), bản giả lập lớp phủ của YouTube,
  ô lưới TikTok có lượt xem, và các khung cắt 3:4, 4:5, 1:1.
- --final vX: chép bản vX thành thumbnail/CAAITE-Claude-artifact-app-anh-bia.jpg (và .png);
  --alt vY: chép bản vY thành ...-anh-bia-ban-phu.jpg.
"""
from __future__ import annotations

import argparse
import functools
import http.server
import io
import json
import os
import shutil
import socketserver
import sys
import threading
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thumbnail" / "out"
FONT_SEMI = str(ROOT / "assets" / "fonts" / "BeVietnamPro-SemiBold.ttf")
FONT_REG = str(ROOT / "assets" / "fonts" / "BeVietnamPro-Regular.ttf")
YT_TITLE = "Claude cho cài artifact thành ứng dụng trên macOS, Windows: cách làm và ba mức quyền"
FINAL_NAME = "CAAITE-Claude-artifact-app-anh-bia.jpg"
W, H = 1080, 1920
MAX_BYTES = 2 * 1024 * 1024

KEY_TEXT = {"title", "title-b", "kicker", "p-lead", "p-hl", "p-row", "p-row-2", "p-note", "p-note-2", "p-cond", "bar-text", "b1", "b2", "b3", "bv1", "bv2", "bv3"}
# Dải chữ chính dùng chung cho hai nền tảng (người nghiên cứu đo ngày 05/10/2026): x 60-1020, y 420-1280.
SAFE = {"x0": 60, "x1": 1020, "y0": 420, "y1": 1280}
TT_CROP = ((H - 1440) // 2, (H - 1440) // 2 + 1440)   # ô lưới TikTok 3:4: y 240-1680
YT_CROP = ((H - 1620) // 2, (H - 1620) // 2 + 1620)   # ô Shorts của YouTube 2:3: y 150-1770
# Lớp phủ của nền tảng (x0, y0, x1, y1) trên khung 1080x1920; chữ chính không được nằm dưới các lớp này
OVERLAYS = {
    "tiêu đề và lượt xem YouTube (điện thoại)": (0, 1375, 1080, 1715),
    "nút ba chấm YouTube": (848, 150, 1080, 382),
    "viên Mới của YouTube": (30, 180, 215, 295),
    "lượt xem TikTok": (80, 1500, 535, 1607),
    "nhãn Đã ghim của TikTok": (53, 293, 387, 413),
}


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def serve(root: Path):
    handler = functools.partial(QuietHandler, directory=str(root))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def srgb_to_lin(c):
    c = c / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def luminance(rgb):
    lin = srgb_to_lin(np.asarray(rgb, dtype=np.float64))
    return 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]


def parse_css_color(s: str):
    s = s.strip()
    inner = s[s.index("(") + 1: s.rindex(")")].replace("/", ",")
    parts = [p.strip() for p in inner.replace(" ", ",").split(",") if p.strip()]
    r, g, b = (float(parts[i]) for i in range(3))
    a = float(parts[3]) if len(parts) > 3 else 1.0
    return (r, g, b), a


def contrast(l1, l2):
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


FAMILY = {"pcard": "card", "p-lead": "card", "p-row": "card", "p-hl": "card", "p-note": "card", "p-cond": "card"}


def ink_box(full, bg, boxes, thr=90, exclude=()):
    """Hộp mực: điểm ảnh đổi mạnh giữa bản có chữ và bản ẩn chữ, trong các hộp chữ (nới 6 px),
    bỏ qua các hộp chữ của phần tử khác (exclude) để không lẫn nét của chữ bên cạnh."""
    x0 = max(0, int(min(b[0] for b in boxes)) - 6); y0 = max(0, int(min(b[1] for b in boxes)) - 6)
    x1 = min(W, int(max(b[2] for b in boxes)) + 6); y1 = min(H, int(max(b[3] for b in boxes)) + 6)
    diff = np.abs(full[y0:y1, x0:x1] - bg[y0:y1, x0:x1]).max(axis=2) > thr
    for ex in exclude:
        ex0, ey0 = max(x0, int(ex[0])), max(y0, int(ex[1]))
        ex1, ey1 = min(x1, int(ex[2]) + 1), min(y1, int(ex[3]) + 1)
        if ex1 > ex0 and ey1 > ey0:
            diff[ey0 - y0:ey1 - y0, ex0 - x0:ex1 - x0] = False
    ys, xs = np.nonzero(diff)
    if not len(xs):
        return None
    return [int(x0 + xs.min()), int(y0 + ys.min()), int(x0 + xs.max() + 1), int(y0 + ys.max() + 1)]


def ink_per_key(page, metrics, png: Path, thr=90):
    """Hộp mực từng khối: ẩn riêng chữ của khối đó (lớp .ink-hide), chụp lại, so với ảnh đầy đủ.
    Cách này không bị cắt hay lẫn khi hộp dòng của khối bên cạnh chồng lên (lỗi kicker/tiêu đề)."""
    full = np.asarray(Image.open(png).convert("RGB"), dtype=np.float64)
    js_on = "k => document.querySelectorAll('[data-key=\"' + k + '\"]').forEach(e => e.classList.add('ink-hide'))"
    js_off = "k => document.querySelectorAll('[data-key=\"' + k + '\"]').forEach(e => e.classList.remove('ink-hide'))"
    out = {}
    for m in metrics:
        k = m["key"]
        page.evaluate(js_on, k)
        shot = page.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H})
        page.evaluate(js_off, k)
        arr = np.asarray(Image.open(io.BytesIO(shot)).convert("RGB"), dtype=np.float64)
        ys, xs = np.nonzero(np.abs(full - arr).max(axis=2) > thr)
        out[k] = [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)] if len(xs) else None
    return out


def analyse(variant: str, metrics, bg_png: Path, png: Path, ink=None):
    bg = np.asarray(Image.open(bg_png).convert("RGB"), dtype=np.float64)
    full = np.asarray(Image.open(png).convert("RGB"), dtype=np.float64)
    report = {"variant": variant, "texts": [], "problems": [], "ink": {}}
    for m in metrics:
        for g in m["glyphs"]:
            x0, y0 = max(0, int(g["x"])), max(0, int(g["y"]))
            x1, y1 = min(W, int(g["x"] + g["w"])), min(H, int(g["y"] + g["h"]))
            if x1 <= x0 or y1 <= y0:
                continue
            region = bg[y0:y1, x0:x1].reshape(-1, 3)
            lum = luminance(region)
            p95, p50 = float(np.percentile(lum, 95)), float(np.percentile(lum, 50))
            (r, gg, b), a = parse_css_color(g["color"])
            # chữ trong suốt một phần: trộn với nền trung vị
            med = np.median(region, axis=0)
            txt = np.array([r, gg, b]) * a + med * (1 - a)
            lt = float(luminance(txt))
            worst = contrast(lt, p95)
            large = g["size"] >= 24
            need = 3.0 if large else 4.5
            item = {"key": m["key"], "text": g["text"].strip(), "size": round(g["size"], 1), "box": [x0, y0, x1, y1],
                    "contrast_worst": round(worst, 2), "contrast_median": round(contrast(lt, p50), 2), "need": need}
            report["texts"].append(item)
            if worst < need:
                report["problems"].append(f"tương phản thấp: {m['key']} '{item['text']}' {worst:.2f} < {need}")
        boxes = [(g["x"], g["y"], g["x"] + g["w"], g["y"] + g["h"]) for g in m["glyphs"]] + [tuple(e) for e in m.get("extras", [])]
        fam = FAMILY.get(m["key"], m["key"])
        others = [(g["x"], g["y"], g["x"] + g["w"], g["y"] + g["h"]) for o in metrics
                  if FAMILY.get(o["key"], o["key"]) != fam for g in o["glyphs"]]
        others += [tuple(e) for o in metrics if FAMILY.get(o["key"], o["key"]) != fam for e in o.get("extras", [])]
        if ink is not None:
            report["ink"][m["key"]] = ink.get(m["key"])
        elif boxes:
            report["ink"][m["key"]] = ink_box(full, bg, boxes, exclude=others)
        # vùng an toàn: dùng hộp mực nếu đo được (hộp dòng chữ cao hơn nét thật)
        x0, y0, x1, y1 = m["x"], m["y"], m["x"] + m["w"], m["y"] + m["h"]
        if report["ink"].get(m["key"]):
            x0, y0, x1, y1 = report["ink"][m["key"]]
        if x0 < 0 or y0 < 0 or x1 > W or y1 > H:
            report["problems"].append(f"tràn khung: {m['key']} {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}")
        if m["key"] in KEY_TEXT and (x0 < SAFE["x0"] or x1 > SAFE["x1"] or y0 < SAFE["y0"] or y1 > SAFE["y1"]):
            report["problems"].append(f"chữ chính ra ngoài vùng an toàn: {m['key']} {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}")
        for oname, (ox0, oy0, ox1, oy1) in OVERLAYS.items():
            if x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0:
                msg = f"chữ nằm dưới lớp phủ '{oname}': {m['key']} {x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}"
                (report["problems"] if m["key"] in KEY_TEXT else report.setdefault("warnings", [])).append(msg)
        for name, (cy0, cy1) in {"2:3 YouTube": YT_CROP, "3:4 TikTok": TT_CROP}.items():
            if m["key"] != "pcard" and (y0 < cy0 < y1 or y0 < cy1 < y1):
                report["problems"].append(f"chữ bị xén nửa khi cắt {name} (y {cy0}-{cy1}): {m['key']} y {y0:.0f}-{y1:.0f}")
        if m["key"] == "pcard":
            by0, by1 = m["box"][1], m["box"][1] + m["box"][3]
            report["card_box_y"] = [round(by0, 1), round(by1, 1)]
            if by1 > SAFE["y1"]:
                report["problems"].append(f"viền đáy thẻ ra ngoài dải chữ chính: y {by1:.1f} > {SAFE['y1']}")
    # Tóm tắt vùng an toàn để ghi vào nhật ký (người chấm vòng 1 xin thêm): từng khối chữ nằm trọn trong,
    # trọn ngoài hay bị xén ở khung cắt 1:1; có chữ trong vùng chữ phủ (y > 1680) hay góc ba chấm không
    safe = {"khung_2x3_youtube": {}, "khung_3x4_tiktok": {}, "dai_chu_chinh_y420_1280": {}, "duoi_lop_phu": []}
    for m in metrics:
        box = report["ink"].get(m["key"]) or [m["x"], m["y"], m["x"] + m["w"], m["y"] + m["h"]]
        x0, y0, x1, y1 = box
        for key, (t0, t1) in (("khung_2x3_youtube", YT_CROP), ("khung_3x4_tiktok", TT_CROP)):
            safe[key][m["key"]] = "trong" if (y0 >= t0 and y1 <= t1) else ("ngoài" if (y1 <= t0 or y0 >= t1) else "XÉN")
        safe["dai_chu_chinh_y420_1280"][m["key"]] = "trong" if (x0 >= SAFE["x0"] and x1 <= SAFE["x1"] and y0 >= SAFE["y0"] and y1 <= SAFE["y1"]) else "ngoài"
        for oname, (ox0, oy0, ox1, oy1) in OVERLAYS.items():
            if x0 < ox1 and x1 > ox0 and y0 < oy1 and y1 > oy0:
                safe["duoi_lop_phu"].append(f"{m['key']} / {oname}")
    report["safe"] = safe
    return report


def save_jpg(png: Path, jpg: Path):
    im = Image.open(png).convert("RGB")
    for q in (93, 90, 87, 84, 80):
        im.save(jpg, "JPEG", quality=q, subsampling=0, optimize=True, progressive=True)
        if jpg.stat().st_size < MAX_BYTES:
            return q, jpg.stat().st_size
    raise SystemExit(f"{jpg} vẫn lớn hơn 2 MB")


def yt_overlay(im: Image.Image, w=204, h=306) -> Image.Image:
    """Giả lập ô Shorts của YouTube trên điện thoại (số đo m.youtube.com ngày 05/10/2026): ảnh cắt 2:3 ở giữa,
    nền tối dần ở 30% dưới, tiêu đề hai dòng và lượt xem phủ ở khoảng 76-96% chiều cao, nút ba chấm góc trên phải."""
    card = im.crop((0, YT_CROP[0], W, YT_CROP[1])).resize((w, h), Image.LANCZOS).convert("RGBA")
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = shade.load()
    start = int(h * 0.70)
    for y in range(start, h):
        a = int(153 * ((y - start) / (h - start)))
        for x in range(w):
            px[x, y] = (0, 0, 0, a)
    card = Image.alpha_composite(card, shade)
    d = ImageDraw.Draw(card)
    # cỡ chữ theo số đo m.youtube.com (ô 204x306 CSS px: tiêu đề khoảng 14 px, dòng 20 px; lượt xem khoảng 12 px)
    f_title = ImageFont.truetype(FONT_SEMI, int(w * 0.068))
    f_views = ImageFont.truetype(FONT_REG, int(w * 0.058))
    words, lines, cur = YT_TITLE.split(), [], ""
    maxw = w - 2 * int(w * 0.04)
    for wd in words:
        test = (cur + " " + wd).strip()
        if d.textlength(test, font=f_title) <= maxw:
            cur = test
        else:
            lines.append(cur)
            cur = wd
    lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        while d.textlength(lines[1] + "...", font=f_title) > maxw:
            lines[1] = lines[1][:-1]
        lines[1] += "..."
    lh = int(w * 0.098)
    y = int(h * 0.76)   # khối tiêu đề bắt đầu ở khoảng 76% chiều cao ô (tiêu đề hai dòng), lượt xem kết thúc ở khoảng 96%
    for ln in lines:
        d.text((int(w * 0.04), y), ln, font=f_title, fill=(255, 255, 255, 255))
        y += lh
    d.text((int(w * 0.04), y + 2), "1,2 N lượt xem", font=f_views, fill=(255, 255, 255, 220))
    cx, cy = w - int(w * 0.05), int(w * 0.06)
    for k in (-1, 0, 1):
        r = max(2, int(w * 0.007))
        d.ellipse((cx - r, cy + k * 3 * r - r, cx + r, cy + k * 3 * r + r), fill=(255, 255, 255, 235))
    return card.convert("RGB")


def tiktok_tile(im: Image.Image, w=240, views="12,3K", pinned=False) -> Image.Image:
    """Giả lập ô lưới trang cá nhân TikTok: cắt 3:4 ở giữa, lượt xem (biểu tượng phát + số) ở góc dưới trái."""
    h = int(w * 4 / 3)
    tile = im.crop((0, TT_CROP[0], W, TT_CROP[1])).resize((w, h), Image.LANCZOS).convert("RGBA")
    shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = shade.load()
    start = int(h * 0.78)
    for y in range(start, h):
        a = int(150 * ((y - start) / (h - start)))
        for x in range(w):
            px[x, y] = (0, 0, 0, a)
    tile = Image.alpha_composite(tile, shade)
    d = ImageDraw.Draw(tile)
    f = ImageFont.truetype(FONT_SEMI, max(10, int(w * 0.07)))
    s = int(w * 0.055)
    x0, y0 = int(w * 0.05), h - int(w * 0.05) - s
    d.polygon([(x0, y0), (x0, y0 + s), (x0 + int(s * 0.85), y0 + s // 2)], outline=(255, 255, 255, 255), width=max(1, w // 160))
    d.text((x0 + s + int(w * 0.03), y0 - int(s * 0.25)), views, font=f, fill=(255, 255, 255, 255))
    if pinned:
        fp = ImageFont.truetype(FONT_SEMI, max(9, int(w * 0.055)))
        d.rounded_rectangle((int(w * 0.04), int(w * 0.04), int(w * 0.04) + int(w * 0.3), int(w * 0.04) + int(w * 0.1)), radius=4, fill=(254, 44, 85, 255))
        d.text((int(w * 0.06), int(w * 0.045)), "Đã ghim", font=fp, fill=(255, 255, 255, 255))
    return tile.convert("RGB")


def label(img: Image.Image, text: str) -> Image.Image:
    f = ImageFont.truetype(FONT_SEMI, 18)
    out = Image.new("RGB", (img.width, img.height + 30), (245, 246, 252))
    out.paste(img, (0, 30))
    ImageDraw.Draw(out).text((6, 5), text, font=f, fill=(18, 20, 58))
    return out


def hstack(imgs, gap=16, bg=(245, 246, 252)):
    w = sum(i.width for i in imgs) + gap * (len(imgs) - 1)
    h = max(i.height for i in imgs)
    out = Image.new("RGB", (w, h), bg)
    x = 0
    for i in imgs:
        out.paste(i, (x, 0))
        x += i.width + gap
    return out


def vstack(imgs, gap=16, bg=(245, 246, 252)):
    w = max(i.width for i in imgs)
    h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGB", (w, h), bg)
    y = 0
    for i in imgs:
        out.paste(i, (0, y))
        y += i.height + gap
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variants", nargs="*", default=["v1", "v2"])
    ap.add_argument("--final", default=None)
    ap.add_argument("--alt", default=None, help="xuất thêm bản phụ, ví dụ v5")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    httpd, port = serve(ROOT)
    reports = {}
    with sync_playwright() as p:
        # THUMB_CHROME: đường dẫn trình duyệt có sẵn (trên server dùng chrome-headless-shell của HyperFrames), để chụp
        # được ở máy không cài trình duyệt của Playwright (laptop thiếu RAM thì chụp trên server)
        exe = os.environ.get("THUMB_CHROME")
        if exe:
            browser = p.chromium.launch(executable_path=exe)
        else:
            try:
                browser = p.chromium.launch()
            except Exception:
                browser = p.chromium.launch(channel="chrome")
        for v in a.variants:
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto(f"http://127.0.0.1:{port}/thumbnail/thumb.html?v={v}")
            page.wait_for_function("window.__ready === true", timeout=30000)
            fonts = page.evaluate("Array.from(document.fonts).map(f => f.family + ' ' + f.weight + ' ' + f.status)")
            bad_fonts = [f for f in fonts if not f.endswith("loaded") and "Lexend" in f]
            png = OUT / f"{v}.png"
            page.screenshot(path=str(png), clip={"x": 0, "y": 0, "width": W, "height": H})
            metrics = page.evaluate("window.__metrics()")
            ink = ink_per_key(page, metrics, png)
            page.evaluate("document.body.classList.add('no-text')")
            bg_png = OUT / f"{v}_bg.png"
            page.screenshot(path=str(bg_png), clip={"x": 0, "y": 0, "width": W, "height": H})
            page.close()
            rep = analyse(v, metrics, bg_png, png, ink)
            rep["fonts_not_loaded"] = bad_fonts
            rep["fonts_used"] = sorted(set(f for f in fonts if f.endswith("loaded")))
            rep["metrics"] = metrics
            q, size = save_jpg(png, OUT / f"{v}.jpg")
            rep["jpg"] = {"quality": q, "bytes": size}
            reports[v] = rep
            print(f"{v}: jpg q{q} {size/1024:.0f} KB; phông chưa tải: {bad_fonts or 'không'}; vấn đề: {rep['problems'] or 'không'}; lưu ý: {rep.get('warnings') or 'không'}")
            print(f"   vùng an toàn: {rep['safe']}; viền thẻ y {rep.get('card_box_y')}")
            worst = sorted(rep["texts"], key=lambda t: t["contrast_worst"])[:4]
            for t in worst:
                print(f"   tương phản thấp nhất: {t['key']:9s} {t['contrast_worst']:5.2f} (cần {t['need']}) cỡ {t['size']}px  '{t['text'][:30]}'")
            for m in metrics:
                ink = rep["ink"].get(m["key"])
                print(f"   {m['key']:9s} x{m['x']:6.0f} y{m['y']:6.0f} w{m['w']:6.0f} h{m['h']:5.0f} font {m['fontSize']:.0f}px  mực {ink}")
        browser.close()
    httpd.shutdown()

    (OUT / "metrics.json").write_text(json.dumps(reports, ensure_ascii=False, indent=1), encoding="utf-8")

    # Ảnh so sánh cho người chấm
    ims = {v: Image.open(OUT / f"{v}.png").convert("RGB") for v in a.variants}
    full = hstack([label(ims[v].resize((540, 960), Image.LANCZOS), f"{v} - 540x960") for v in a.variants])
    full.save(OUT / "compare_full.jpg", quality=90)
    overlay = hstack([label(yt_overlay(ims[v], 408, 612), f"{v} - ô Shorts 2:3 có lớp phủ (gấp đôi)") for v in a.variants])
    overlay.save(OUT / "compare_overlay.jpg", quality=90)
    small = hstack([
        label(hstack([yt_overlay(ims[v], 204, 306), tiktok_tile(ims[v], 130)], gap=10), f"{v} YouTube 204 | TikTok 130")
        for v in a.variants
    ], gap=24)
    small.save(OUT / "compare_small.jpg", quality=92)
    crops = []
    for v in a.variants:
        im = ims[v]
        c23 = im.crop((0, YT_CROP[0], W, YT_CROP[1])).resize((270, 405), Image.LANCZOS)
        c34 = im.crop((0, TT_CROP[0], W, TT_CROP[1])).resize((270, 360), Image.LANCZOS)
        c11 = im.crop((0, (H - W) // 2, W, (H - W) // 2 + W)).resize((270, 270), Image.LANCZOS)
        crops.append(label(hstack([c23, c34, c11], gap=10), f"{v} cắt 2:3 (YouTube) | 3:4 (TikTok) | 1:1"))
    vstack(crops, gap=24).save(OUT / "compare_crops.jpg", quality=90)
    # Ô lưới TikTok ở cỡ thật trên điện thoại (3 cột trên màn 360 px: mỗi ô khoảng 118 px) và cỡ lớn hơn để đọc
    tt = [label(hstack([tiktok_tile(ims[v], 240, pinned=(i == 0)), tiktok_tile(ims[v], 118)], gap=10), f"{v} ô TikTok 240 | 118")
          for i, v in enumerate(a.variants)]
    hstack(tt, gap=24).save(OUT / "compare_tiktok.jpg", quality=92)
    print("Ảnh so sánh:", ", ".join(str((OUT / n).relative_to(ROOT)) for n in
                                     ["compare_full.jpg", "compare_overlay.jpg", "compare_small.jpg", "compare_crops.jpg", "compare_tiktok.jpg"]))

    if a.final:
        dst = ROOT / "thumbnail" / FINAL_NAME
        shutil.copyfile(OUT / f"{a.final}.jpg", dst)
        shutil.copyfile(OUT / f"{a.final}.png", dst.with_suffix(".png"))
        print(f"Bản cuối: {dst.relative_to(ROOT)} ({dst.stat().st_size/1024:.0f} KB)")
    if a.alt:
        dst = ROOT / "thumbnail" / FINAL_NAME.replace(".jpg", "-ban-phu.jpg")
        shutil.copyfile(OUT / f"{a.alt}.jpg", dst)
        print(f"Bản phụ: {dst.relative_to(ROOT)} ({dst.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
