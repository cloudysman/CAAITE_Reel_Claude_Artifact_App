"""Sinh 8 cảnh của reel "Claude: cài artifact thành ứng dụng trên máy tính" vào compositions/frames/.

Các cảnh dùng chung CSS, thanh tiêu đề, nền và cơ chế mốc lời đọc. Mốc thật do fill_cues.py điền vào đoạn CUE sau khi có
giọng, nên trong JS của cảnh chỉ viết mốc theo chữ của lời đọc: {w:B2S1:artifact} thành wt(S1, i, n) với i là vị trí từ
"artifact" trong bản đọc (tts) của câu B2S1; {t0:B2S2}, {t1:B2S2} là đầu, cuối câu. Không viết cứng giây.
Mốc data-start, data-media-start của video lấy từ src_build/scene_timing.json (build_index.py ghi), nên thứ tự chạy là
build_index.py, tao_canh.py, fill_cues.py (sau_giong.sh làm đúng thứ tự này).

Tư liệu thật dùng trong cảnh:
- video demo của @ClaudeDevs (Anthropic) trên X, bản 4K cắt ở assets/stock/video/claude-demo-*.mp4 (cách cắt ghi trong .json);
- ảnh hộp thoại Install as app cắt từ khung 4,6 s của video đó (assets/web/claude/hop_thoai_cai.png);
- ảnh chụp bài trên X (assets/web/claude/x_post.png), ảnh đầu bài trên claude.com (assets/web/claude/hero_pixel.jpg);
- trang "Felix's Demo Apps" chụp bằng src_build/chup_felix.py (assets/web/felix/).
Không vẽ logo Claude hay Anthropic; tên hãng viết bằng chữ Lexend.
Cách dùng: python -I -X utf8 src_build/tao_canh.py [mã cảnh ...]
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "compositions" / "frames"
TIMING_PATH = ROOT / "src_build" / "scene_timing.json"
TIMING = json.loads(TIMING_PATH.read_text(encoding="utf-8")) if TIMING_PATH.exists() else None
TLS = {c["id"]: c for c in json.loads((ROOT / "voice" / "src" / "tts_lines.json").read_text(encoding="utf-8"))["cau"]}
ANH = json.loads((ROOT / "assets" / "web" / "claude" / "anh.json").read_text(encoding="utf-8"))


def roman(text: str) -> list[str]:
    """Như build_tts_lines.roman: chữ thường, bỏ dấu, tách từ (đúng cách đếm từ của mốc lời đọc)."""
    s = unicodedata.normalize("NFC", text).strip().lower()
    s = re.sub(r"(?<=\w)-(?=\w)", " ", s)
    s = unicodedata.normalize("NFD", s.replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z' ]", " ", s).split()


TU = {sid: roman(c["tts"]) for sid, c in TLS.items()}


def iw(sid: str, tu: str, lan: int = 1) -> int:
    """Vị trí (từ 0) của lần thứ `lan` cụm `tu` trong bản đọc của câu `sid`."""
    seq, words, dem = roman(tu), TU[sid], 0
    for i in range(len(words) - len(seq) + 1):
        if words[i:i + len(seq)] == seq:
            dem += 1
            if dem == lan:
                return i
    raise SystemExit(f"không thấy '{tu}' trong {sid}: {' '.join(words)}")


def canh_tg(canh: str) -> dict | None:
    return next((s for s in TIMING["scenes"] if s["id"] == canh), None) if TIMING else None


def tw(canh: str, sid: str, tu: str, mac_dinh: float, lan: int = 1) -> float:
    """Giây cục bộ (trong cảnh) của đầu cụm `tu` ở câu `sid`, theo scene_timing.json; chưa có thì trả mặc định."""
    i = iw(sid, tu, lan)
    for c in (canh_tg(canh) or {}).get("cues", []):
        if c["sentence"] == sid and i < len(c.get("words", [])):
            return c["words"][i]
    return mac_dinh


def t_cau(canh: str, sid: str, dau: bool, mac_dinh: float) -> float:
    for c in (canh_tg(canh) or {}).get("cues", []):
        if c["sentence"] == sid:
            return c["local_start"] if dau else c["local_end"]
    return mac_dinh


def dai(canh: str, mac_dinh: float = 5.0) -> float:
    sc = canh_tg(canh)
    return round(sc["duration"], 3) if sc else mac_dinh


def thay_moc(js: str, cau: list) -> str:
    """{w:B2S1:artifact[:2]} -> wt(S1, i, n); {t0:B2S1} -> S1.t0; {t1:B2S1} -> S1.t1."""
    def w(m):
        sid, tu, lan = m.group(1), m.group(2), int(m.group(3) or 1)
        return f"wt(S{cau.index(sid) + 1}, {iw(sid, tu, lan)}, {len(TU[sid])})"
    js = re.sub(r"\{w:(B\dS\d):([^}:]+)(?::(\d))?\}", w, js)
    return re.sub(r"\{(t0|t1):(B\dS\d)\}", lambda m: f"S{cau.index(m.group(2)) + 1}.{m.group(1)}", js)


def video(vid: str, tep: str, bat_dau: float, dai_s: float, media: float, rang: int, cls: str = "", toc_do: float = 1.0, them: str = "") -> str:
    """Thẻ video có mốc riêng (không đặt trong phần tử có data-start, luật video_nested_in_timed_element)."""
    rate = f' data-playback-rate="{toc_do:g}"' if abs(toc_do - 1.0) > 1e-6 else ""
    # mốc data-start tính theo giờ cục bộ của cảnh; ghi rõ để lint không hiểu nhầm là giờ toàn phim
    goc = ' data-hf-media-start-basis="local"' if bat_dau > 0 else ""
    return (f'<video id="{vid}" class="{cls}" src="assets/stock/video/{tep}" data-start="{bat_dau:.3f}" data-duration="{max(0.1, dai_s):.3f}" '
            f'data-media-start="{max(0.0, media):.3f}"{rate}{goc} data-track-index="{rang}" muted playsinline{them}></video>')


CSS_CHUNG = """
    @font-face { font-family: "Lexend"; src: url("assets/fonts/Lexend-Variable.ttf") format("truetype"); font-weight: 100 900; font-display: block; }
    #root { position: absolute; inset: 0; overflow: hidden; font-family: "Lexend", sans-serif; --hy: #5154f5; --hy-ink: #2f33c9; --mint: #a4e9ec;
            --ink: #12143a; --claude: #d97757; --claude-hi: #ffc3a8; --claude-ink: #a3401f; --warn: #b4530a; }
    #root[data-theme="light"] { --fg: #12143a; --fg-soft: rgba(18, 20, 58, 0.78); --accent: #2f55d4; color: var(--fg); }
    #root[data-theme="brand"], #root[data-theme="dark"], #root[data-theme="pixel"] { --fg: #ffffff; --fg-soft: rgba(255, 255, 255, 0.94); --accent: #a4e9ec; color: var(--fg); }
    #root .k-bg { position: absolute; inset: 0; overflow: hidden; }
    #root .k-bg-grad { position: absolute; inset: 0; background: linear-gradient(160deg, #5154f5 0%, #4878eb 50%, #3ca7de 100%); }
    #root .k-bg-paper { position: absolute; inset: 0; background: #f9f9ff; }
    #root .k-bg-dark { position: absolute; inset: 0; background:
        radial-gradient(900px 760px at 12% 8%, rgba(81, 84, 245, 0.42), rgba(81, 84, 245, 0) 70%),
        radial-gradient(900px 800px at 92% 92%, rgba(217, 119, 87, 0.34), rgba(217, 119, 87, 0) 70%), #0b0d26; }
    #root .k-bg-pixel { position: absolute; left: 0; top: 0; width: 3562px; height: 1920px; }
    #root .k-bg-plate { position: absolute; left: -54px; top: -96px; width: 1188px; height: 2112px; object-fit: cover; }
    #root .k-bg-arc { mix-blend-mode: soft-light; opacity: 0.22; }
    #root .k-bg-silk { opacity: 0.55; }
    #root .k-bg-grain { position: absolute; inset: 0; background: url("assets/brand/grain-512.png") repeat; background-size: 512px 512px; mix-blend-mode: soft-light; opacity: 0.05; }
    #root .k-shade { position: absolute; left: 0; width: 1080px; pointer-events: none; }
    #root .k-shade-top { top: 0; height: 620px; background: linear-gradient(180deg, rgba(8, 9, 30, 0.86) 0%, rgba(8, 9, 30, 0.55) 55%, rgba(8, 9, 30, 0) 100%); }
    #root .k-shade-bot { top: 1060px; height: 860px; background: linear-gradient(0deg, rgba(8, 9, 30, 0.86) 0%, rgba(8, 9, 30, 0.5) 55%, rgba(8, 9, 30, 0) 100%); }
    #root .k-hdr { position: absolute; left: 72px; right: 72px; top: 150px; height: 48px; display: flex; align-items: center; gap: 18px; }
    #root .k-hdr-label { font-size: 22px; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--fg-soft); white-space: nowrap; }
    #root .k-hdr-pill { font-size: 22px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; padding: 4px 16px 5px; border-radius: 999px; border: 2px solid var(--accent); color: var(--accent); white-space: nowrap; }
    #root[data-theme="brand"] .k-hdr-pill, #root[data-theme="dark"] .k-hdr-pill, #root[data-theme="pixel"] .k-hdr-pill { color: #ffffff; border-color: rgba(255, 255, 255, 0.8); background: rgba(18, 20, 58, 0.28); }
    #root[data-theme="pixel"] .k-hdr-label, #root[data-theme="dark"] .k-hdr-label { color: #ffffff; text-shadow: 0 2px 10px rgba(0, 0, 0, 0.6); }
    #root .k-src { position: absolute; left: 72px; top: 1182px; font-size: 22px; font-weight: 500; letter-spacing: 0.04em; color: var(--fg-soft); white-space: nowrap; }
    #root[data-theme="brand"] .k-src, #root[data-theme="dark"] .k-src, #root[data-theme="pixel"] .k-src { color: #ffffff; background: rgba(12, 13, 40, 0.62); padding: 5px 14px 6px; border-radius: 999px; }
    #root .k-src.k-cr { left: auto; right: 72px; top: 1132px; font-size: 20px; }
    #root[data-theme="brand"] .k-glass, #root[data-theme="dark"] .k-glass, #root[data-theme="pixel"] .k-glass { background: rgba(22, 25, 80, 0.62); border: 2px solid rgba(255, 255, 255, 0.4); border-radius: 32px; box-shadow: 0 30px 60px rgba(8, 9, 30, 0.3); }
    #root[data-theme="light"] .k-glass { background: rgba(255, 255, 255, 0.95); border: 2px solid #dee0fd; border-radius: 32px; box-shadow: 0 30px 60px rgba(81, 84, 245, 0.14); }
    #root .k-kicker { position: absolute; left: 72px; top: 246px; font-size: 32px; font-weight: 500; letter-spacing: 0.02em; color: var(--accent); white-space: nowrap; }
    #root[data-theme="light"] .k-kicker { color: #1e2a8a; }
    #root .k-chip { display: inline-flex; align-items: center; gap: 14px; padding: 12px 28px; border-radius: 999px; font-size: 34px; font-weight: 500; white-space: nowrap; }
    #root[data-theme="light"] .k-chip { background: #ffffff; border: 2px solid #dee0fd; color: var(--fg); }
    #root[data-theme="brand"] .k-chip, #root[data-theme="dark"] .k-chip, #root[data-theme="pixel"] .k-chip { background: rgba(22, 25, 80, 0.72); border: 2px solid rgba(255, 255, 255, 0.55); color: #ffffff; }
    #root .k-tag { position: absolute; display: inline-flex; align-items: center; gap: 12px; padding: 10px 24px 12px; border-radius: 999px; background: #ffffff; color: var(--ink);
                   font-size: 32px; font-weight: 600; white-space: nowrap; box-shadow: 0 14px 30px rgba(8, 9, 30, 0.35); }
    #root .k-ring { position: absolute; border: 6px solid var(--mint); border-radius: 22px; box-shadow: 0 0 26px rgba(164, 233, 236, 0.95), inset 0 0 16px rgba(164, 233, 236, 0.45); }
    #root .k-win { position: absolute; border-radius: 24px; overflow: hidden; background: #0f1024; box-shadow: 0 40px 80px rgba(8, 9, 30, 0.45), 0 0 0 2px rgba(255, 255, 255, 0.16); }
    #root .k-win-bar { position: absolute; left: 0; top: 0; right: 0; height: 52px; background: rgba(248, 248, 252, 0.97); display: flex; align-items: center; gap: 10px; padding: 0 20px;
                       font-size: 28px; font-weight: 600; color: #12143a; white-space: nowrap; }
    #root .k-dot { width: 15px; height: 15px; border-radius: 50%; flex: none; }
    #root .k-win img, #root .k-win video { position: absolute; left: 0; display: block; object-fit: cover; }
    #root .k-paper { position: absolute; background: #ffffff; border-radius: 26px; overflow: hidden; box-shadow: 0 24px 48px rgba(18, 20, 58, 0.22); }
    #root .k-paper img { position: absolute; left: 0; top: 0; display: block; }
    #root .k-hl { position: absolute; border-radius: 8px; background: rgba(255, 196, 90, 0.62); mix-blend-mode: multiply; transform-origin: 0% 50%; }
    #root .k-hl.k-hl-1 { background: rgba(110, 220, 226, 0.6); }
"""

DOTS = '<span class="k-dot" style="background:#ff5f57"></span><span class="k-dot" style="background:#febc2e"></span><span class="k-dot" style="background:#28c840"></span>'


def giay(ten: str, rong: int, pid: str, trai: int, tren: int) -> tuple[int, str]:
    """Ảnh tư liệu cắt sẵn (assets/web/claude/anh.json) rộng `rong` px, kèm vệt tô (lớp k-hl, <pid>-h<nhóm>)."""
    p = ANH[ten]
    k = rong / p["w"]
    cao = round(p["h"] * k)
    to = "".join(
        f'<div class="k-hl{" k-hl-1" if c == 1 else ""} {pid}-h{c}" style="left:{round(x0 * k) - 4}px;top:{round(y0 * k) - 3}px;width:{round((x1 - x0) * k) + 8}px;height:{round((y1 - y0) * k) + 6}px;" data-layout-allow-overlap></div>'
        for x0, y0, x1, y1, c in p["to_sang"])
    html = (f'<div class="k-paper" id="{pid}" style="left:{trai}px;top:{tren}px;width:{rong}px;height:{cao}px;" data-layout-allow-overlap>'
            f'<img src="{p["tep"]}" style="width:{rong}px;height:{cao}px;" alt="" />{to}</div>')
    return cao, html


def bo_cuc(ma: str, c: dict) -> str:
    so = ma[:2]
    theme = c["theme"]
    if theme == "brand":
        bg = f'<div class="k-bg-grad" id="f{so}-grad"></div><img id="f{so}-plate" class="k-bg-plate k-bg-arc" src="assets/plates/{c.get("nen", "deep-v.jpg")}" alt="" /><div class="k-bg-grain"></div>'
    elif theme == "light":
        bg = f'<div class="k-bg-paper"></div><img id="f{so}-plate" class="k-bg-plate k-bg-silk" src="assets/plates/{c.get("nen", "silk-v.jpg")}" alt="" /><div class="k-bg-grain"></div>'
    elif theme == "pixel":
        bg = f'<img id="f{so}-plate" class="k-bg-pixel" src="{c["nen"]}" alt="" /><div class="k-bg-grain"></div>'
    else:
        bg = f'<div class="k-bg-dark" id="f{so}-plate"></div><div class="k-bg-grain"></div>'
    khai = "\n".join(f'      var S{i + 1} = CUE.S["{s}"];' for i, s in enumerate(c["cau"]))
    js = thay_moc(c["js"], c["cau"])
    nen_dong = c.get("nen_dong", f'tl.fromTo("#f{so}-plate", {{ x: 0, y: -16 }}, {{ x: -16, y: 16, duration: D, ease: "none" }}, 0);')
    return f"""<template>
  <style>{CSS_CHUNG}
{c["css"]}
  </style>

  <div id="root" data-composition-id="{ma}" data-theme="{theme}" data-width="1080" data-height="1920" data-duration="5" data-fill-d>
    <div id="f{so}-bg" class="k-bg clip" data-start="0" data-duration="5" data-fill-d data-track-index="0">{bg}</div>
{c.get("video", "")}
{c["than"]}
    <div class="k-hdr" id="f{so}-hdr"><span class="k-hdr-label" data-layout-allow-overlap>Trung tâm Đào tạo AI Chuyên sâu</span><span class="k-hdr-pill" data-layout-allow-overlap>Tin AI</span></div>
  </div>

  <script>
    (function () {{
      var CUE = /*CUE*/{{"D": 5, "S": {{}}}}/*END_CUE*/;
      var D = CUE.D;
{khai}
      function wt(S, i, n) {{ return S.w && S.w[i] != null ? S.w[i] : S.t0 + (S.t1 - S.t0) * i / n; }}
      var tl = gsap.timeline({{ paused: true }});
      {nen_dong}
{js}
      window.__timelines["{ma}"] = tl;
    }})();
  </script>
</template>
"""


CANH = {}

# ---------------------------------------------------------------- 01: móc câu
# Khung đầu: quả địa cầu của ứng dụng Debris Space Tracker (video demo), tiêu đề hiện ngay, lời nhắn gốc hiện như đang gõ
# lúc đọc "Một lời nhắn"; ngay trước chữ "chạy", phóng xuyên qua quả địa cầu sang cảnh máy vừa cài ứng dụng: biểu tượng
# quả địa cầu hiện ra đúng chữ "chạy", cùng lúc nhạc vào nhịp.
C1 = "01-hook"
D1 = dai(C1, 4.6)
T1_POP = tw(C1, "B1S1", "chạy", 2.9)
T1_CUT = max(1.5, T1_POP - 0.4)
# clip máy cài bắt đầu ở giây 7,0 của video demo; biểu tượng đã có từ 1,2 s của clip, cửa sổ ứng dụng hiện quả địa cầu
# từ 2,1 s và mở hẳn ở 2,3 s. QA bản dựng 2: lúc phóng xuyên clip ở 1,45 s, nên chữ "chạy" rơi vào 1,85 s và cửa sổ
# chạy ứng dụng hiện đúng cụm "trên máy tính" (bản trước cửa sổ chỉ đứng rõ 0,2 s trước chuyển cảnh).
MEDIA_DOCK = max(0.0, 1.85 - (T1_POP - T1_CUT))
CANH[C1] = dict(theme="dark", cau=["B1S1"], video=f"""
    <div class="f01-vw" id="f01-wa">{video("f01-va", "claude-demo-globe-v.mp4", 0.0, T1_CUT + 0.3, 0.0, 1, "f01-v", min(1.0, max(0.55, 1.55 / (T1_CUT + 0.3))))}</div>
    <div class="f01-vw" id="f01-wb">{video("f01-vb", "claude-demo-dock-v.mp4", T1_CUT, min(D1 - T1_CUT, 3.38 - MEDIA_DOCK), MEDIA_DOCK, 2, "f01-v")}</div>
    <div class="k-shade k-shade-top" id="f01-st"></div><div class="k-shade k-shade-bot" id="f01-sb"></div>""", css="""
    #root .f01-vw { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; }
    #root .f01-v { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
    #root #f01-wb { opacity: 0; }
    #root #f01-sb { top: 1300px; height: 620px; background: linear-gradient(0deg, rgba(8, 9, 30, 0.97) 0%, rgba(8, 9, 30, 0.95) 75%, rgba(8, 9, 30, 0) 100%); }
    #root #f01-st { height: 720px; background: linear-gradient(180deg, rgba(8, 9, 30, 0.92) 0%, rgba(8, 9, 30, 0.85) 60%, rgba(8, 9, 30, 0) 100%); }
    #root #f01-vb { transform: translateY(-150px) scale(1.2); transform-origin: 50% 50%; }
    #root #f01-title { position: absolute; left: 72px; top: 262px; width: 936px; font-size: 80px; font-weight: 700; line-height: 92px; letter-spacing: -0.02em; color: #ffffff;
                       text-shadow: 0 6px 30px rgba(0, 0, 0, 0.55); }
    #root #f01-title .l2 { color: var(--claude-hi); white-space: nowrap; }
    #root #f01-msg { position: absolute; left: 72px; top: 496px; max-width: 860px; box-sizing: border-box; padding: 18px 28px 20px; border-radius: 28px 28px 28px 8px;
                     background: rgba(255, 255, 255, 0.95); color: var(--ink); font-size: 32px; font-weight: 500; line-height: 42px; box-shadow: 0 18px 40px rgba(0, 0, 0, 0.35); }
    #root #f01-msg .ca { display: inline-block; width: 3px; height: 34px; margin-left: 4px; background: var(--claude); vertical-align: -6px; }
    #root #f01-x { position: absolute; left: 72px; top: 1068px; padding: 14px 28px 15px; font-size: 30px; font-weight: 500; }
    #root #f01-x b { font-weight: 700; color: var(--claude-hi); }
    #root #f01-ring { position: absolute; left: 505px; top: 776px; width: 600px; height: 600px; opacity: 0; }
    #root #f01-new { position: absolute; left: 330px; top: 1046px; }
    #root #f01-flash { position: absolute; inset: 0; background: radial-gradient(circle at 75% 56%, rgba(255, 255, 255, 0.95), rgba(255, 214, 196, 0.55) 35%, rgba(255, 255, 255, 0) 70%); opacity: 0; mix-blend-mode: screen; }
""", than="""
    <div id="f01-title" data-layout-allow-overlap>Artifact của Claude<br><span class="l2">giờ cài thành ứng dụng</span></div>
    <div id="f01-msg" data-layout-allow-overlap><span id="f01-mt">Build me</span><span class="ca"></span></div>
    <div class="k-chip" id="f01-x" data-layout-allow-overlap><span>Bài của @ClaudeDevs: <b>3,9 triệu</b> lượt xem sau 7 giờ</span></div>
    <div id="f01-flash" data-layout-allow-overlap></div>
    <img id="f01-ring" src="assets/derived/iris-ring-1000.png" alt="" data-layout-allow-overlap data-layout-allow-overflow />
    <div class="k-tag" id="f01-new" data-layout-allow-overlap>Ứng dụng vừa cài</div>
    <div class="k-src" id="f01-src" data-layout-allow-overlap>Video: @ClaudeDevs (Anthropic) trên X</div>
""", js=f"""
      var tCut = {T1_CUT:.3f}, tPop = Math.max({{w:B1S1:chạy}}, tCut + 0.3);
      var MSG = "Build me an app that tracks every piece of space junk in orbit.";
      tl.fromTo("#f01-wa", {{ scale: 1.0 }}, {{ scale: 1.1, duration: tCut - 0.13, ease: "none" }}, 0);
      tl.fromTo("#f01-title", {{ y: 0 }}, {{ y: -8, duration: D, ease: "none" }}, 0);
      // "Một lời nhắn": lời nhắn gốc trong video demo hiện như đang gõ
      var go = {{ n: 0 }};
      tl.fromTo(go, {{ n: 8 }}, {{ n: MSG.length, duration: Math.max(0.5, {{w:B1S1:Claud}} - 0.15), ease: "none", onUpdate: function () {{
        var el = document.querySelector("#f01-mt"); if (el) el.textContent = MSG.slice(0, Math.round(go.n));
      }} }}, 0.06);
      tl.fromTo("#f01-msg .ca", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.22, ease: "steps(1)", repeat: 9, yoyo: true }}, 0);
      tl.fromTo("#f01-x, #f01-src", {{ autoAlpha: 0, y: 16 }}, {{ autoAlpha: 1, y: 0, duration: 0.32, ease: "back.out(1.6)" }}, 0.3);
      // trước chữ "chạy": phóng xuyên qua quả địa cầu sang cảnh máy vừa cài ứng dụng
      tl.to("#f01-wa", {{ scale: 1.5, autoAlpha: 0, filter: "blur(10px)", duration: 0.3, ease: "power2.in", immediateRender: false }}, tCut - 0.12);
      tl.fromTo("#f01-wb", {{ autoAlpha: 0, scale: 1.18 }}, {{ autoAlpha: 1, scale: 1, duration: 0.42, ease: "power3.out" }}, tCut);
      tl.to("#f01-msg, #f01-x", {{ autoAlpha: 0, y: -12, duration: 0.2, ease: "power2.in", immediateRender: false }}, tCut - 0.05);
      // "chạy": biểu tượng hiện, vòng sáng loang (cùng lúc nhạc vào nhịp)
      tl.fromTo("#f01-ring", {{ opacity: 0.9, scale: 0.15 }}, {{ opacity: 0, scale: 1.25, duration: 0.85, ease: "power2.out", immediateRender: false }}, tPop - 0.04);
      tl.fromTo("#f01-flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.07, ease: "power2.out", immediateRender: false }}, tPop - 0.03);
      tl.to("#f01-flash", {{ opacity: 0, duration: 0.35, ease: "power2.in", immediateRender: false }}, tPop + 0.05);
      tl.fromTo("#f01-wb", {{ y: 0 }}, {{ y: -10, duration: 0.08, ease: "power2.out", yoyo: true, repeat: 1, immediateRender: false }}, tPop);
      tl.fromTo("#f01-new", {{ autoAlpha: 0, x: -20, scale: 0.8 }}, {{ autoAlpha: 1, x: 0, scale: 1, duration: 0.36, ease: "back.out(1.8)" }}, tPop + 0.12);
      // lúc chuyển cảnh phóng sang 02: ẩn hàng tiêu đề và dòng nguồn của cảnh này để không in đúp với cảnh 02 (QA bản dựng 2)
      tl.to("#f01-hdr, #f01-src, #f01-new", {{ autoAlpha: 0, duration: 0.12, immediateRender: false }}, D - 0.45);
"""
)

# ---------------------------------------------------------------- 02: cách cài
# B2S1: video demo (khung chat và artifact), viên Claude cho macOS, Windows; "artifact": khung và nhãn giải nghĩa;
# "chọn mục cài": menu thật, tô mục Install as app (Beta) đúng chữ "cài" (clip chạy chậm 0,55 lần để con trỏ thật tới
# mục này đúng chữ); bấm xong là hộp thoại Install, kéo qua khoảng lặng trước B2S2 tới lúc bấm Install;
# B2S2: ứng dụng đã cài (biểu tượng ở Dock, cửa sổ riêng), hai viên macOS, Windows, rồi các ứng dụng mẫu khác lướt nhanh.
C2 = "02-cai-dat"
D2 = dai(C2, 9.0)
T2_MENU = max(1.0, tw(C2, "B2S1", "rồi", 2.2) - 0.1)
T2_CAI = tw(C2, "B2S1", "cài", 2.9)
T2_S2 = t_cau(C2, "B2S2", True, 5.4)
T2_WIN = tw(C2, "B2S2", "Windows", 7.6)
TOC_MENU = 0.55
# menu-v bắt đầu ở 1,35 s của demo; con trỏ thật nằm trên mục Install as app ở 3,5 s của demo (2,15 s của clip),
# bấm ở khoảng 3,6 s; sau đó hộp thoại hiện
MEDIA_MENU = max(0.0, 2.15 - TOC_MENU * (T2_CAI - T2_MENU))
T2_END1 = t_cau(C2, "B2S1", False, T2_CAI + 0.8)
T2_DLG = max(T2_CAI + 0.35, T2_END1 + 0.05)
# clip hộp thoại bắt đầu ở 3,95 s của demo; nút Install được bấm ở khoảng 5,6 s của demo (1,65 s của clip)
MEDIA_DLG = min(1.4, max(0.25, 1.65 - ((T2_S2 - 0.45) - T2_DLG)))
CANH[C2] = dict(theme="dark", cau=["B2S1", "B2S2"], video=f"""
    <div class="k-win" id="f02-scr"><div class="k-win-bar">{DOTS}<span>Claude, video demo</span></div>
      {video("f02-v0", "claude-demo-1080p.mp4", 0.0, T2_MENU + 0.3, 0.05, 1, "f02-scrv")}
    </div>
    <div class="f02-full" id="f02-wm">{video("f02-vm", "claude-demo-menu-v.mp4", T2_MENU, T2_DLG - T2_MENU + 0.3, MEDIA_MENU, 2, "f02-fv", TOC_MENU)}
      <img class="f02-fv" id="f02-still" src="assets/web/claude/menu_giu.jpg" alt="" />
      <div class="k-ring" id="f02-row" data-layout-allow-overlap></div><div class="k-shade k-shade-top"></div><div class="k-shade k-shade-bot"></div></div>
    <div class="k-paper" id="f02-dw" data-layout-allow-overlap><img src="assets/web/claude/hop_thoai_cai.png" alt="" style="width:936px;height:328px;" /></div>
    <div class="k-win" id="f02-aw"><div class="k-win-bar">{DOTS}<span class="f02-wt" id="f02-wt1">Ứng dụng Debris Space Tracker vừa cài</span><span class="f02-wt" id="f02-wt2">Các ứng dụng mẫu khác trong video demo</span></div>
      <div class="f02-avw"><div class="f02-avz" id="f02-vaw">{video("f02-va", "claude-demo-1080p.mp4", T2_S2, D2 - T2_S2, 8.75, 4, "f02-av")}</div></div>
    </div>""", css="""
    #root #f02-scr { left: 40px; top: 300px; width: 1000px; height: 615px; transform-origin: 50% 0%; }
    #root .f02-scrv { top: 52px; width: 1000px; height: 563px; }
    #root .f02-full { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; overflow: hidden; opacity: 0; }
    #root .f02-fv { position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; }
    #root #f02-dw { left: 72px; top: 560px; width: 936px; height: 328px; opacity: 0; }
    #root .f02-avw { position: absolute; left: 0; top: 52px; width: 1000px; height: 563px; overflow: hidden; }
    #root .f02-avz { position: absolute; left: 0; top: 0; width: 1000px; height: 563px; transform-origin: 56% 100%; }
    #root #f02-aw { left: 40px; top: 300px; width: 1000px; height: 615px; opacity: 0; }
    #root .f02-av { top: 0; width: 1000px; height: 563px; }
    #root #f02-still { opacity: 0; }
    #root .f02-wt { position: absolute; left: 116px; top: 8px; }
    #root #f02-wt2 { opacity: 0; }
    #root #f02-os0 { position: absolute; left: 72px; top: 958px; opacity: 0; }
    #root #f02-art { left: 318px; top: 350px; width: 716px; height: 562px; border-color: var(--claude-hi); box-shadow: 0 0 26px rgba(255, 195, 168, 0.9); opacity: 0; }
    #root #f02-artl { left: 72px; top: 1050px; opacity: 0; max-width: 936px; white-space: normal; line-height: 42px; border-radius: 28px; z-index: 6; }
    #root #f02-row { left: 217px; top: 819px; width: 731px; height: 102px; opacity: 0; }
    #root #f02-rowl { left: 230px; top: 1100px; opacity: 0; }
    #root #f02-ins { left: 851px; top: 790px; width: 133px; height: 73px; opacity: 0; }
    #root #f02-insl { left: auto; right: 72px; top: 908px; opacity: 0; }
    #root #f02-t1 { left: 72px; top: 958px; opacity: 0; }
    #root #f02-t2 { left: 400px; top: 958px; opacity: 0; }
    #root .f02-os { position: absolute; top: 1146px; opacity: 0; }
    #root #f02-os1 { left: 72px; }
    #root #f02-os2 { left: 290px; }
    #root #f02-t3 { left: 72px; top: 1052px; opacity: 0; font-size: 28px; }
    #root #f02-src { left: auto; right: 72px; top: 240px; font-size: 20px; }
    #root #f02-wm .k-shade-top { height: 420px; background: linear-gradient(180deg, rgba(8, 9, 30, 0.96) 0%, rgba(8, 9, 30, 0.94) 50%, rgba(8, 9, 30, 0) 100%); }
    #root #f02-wm .k-shade-bot { top: 1150px; height: 770px; background: linear-gradient(0deg, rgba(8, 9, 30, 0.95) 0%, rgba(8, 9, 30, 0.9) 50%, rgba(8, 9, 30, 0) 100%); }
    #root #f02-dock { left: 573px; top: 819px; width: 86px; height: 87px; border-radius: 20px; opacity: 0; }
""", than="""
    <div class="k-chip" id="f02-os0" data-layout-allow-overlap>Cần cập nhật Claude lên bản mới</div>
    <div class="k-ring" id="f02-art" data-layout-allow-overlap></div>
    <div class="k-tag" id="f02-artl" data-layout-allow-overlap>Artifact: trang tương tác Claude tạo ra,<br>như biểu đồ hay trang web</div>
    <div class="k-tag" id="f02-rowl" data-layout-allow-overlap>Mục Install as app (Beta)</div>
    <div class="k-ring" id="f02-ins" data-layout-allow-overlap></div>
    <div class="k-ring" id="f02-dock" data-layout-allow-overlap></div>
    <div class="k-tag" id="f02-insl" data-layout-allow-overlap>Bấm Install để cài</div>
    <div class="k-tag" id="f02-t1" data-layout-allow-overlap>Biểu tượng riêng</div>
    <div class="k-tag" id="f02-t2" data-layout-allow-overlap>Cửa sổ riêng</div>
    <div class="k-chip f02-os" id="f02-os1" data-layout-allow-overlap>macOS</div>
    <div class="k-chip f02-os" id="f02-os2" data-layout-allow-overlap>Windows</div>
    <div class="k-tag" id="f02-t3" data-layout-allow-overlap>Không còn mở bên trong Claude</div>
    <div class="k-src" id="f02-src" data-layout-allow-overlap>Video: @ClaudeDevs (Anthropic) trên X</div>
""", js=f"""
      var tMenu = {T2_MENU:.3f}, tDlg = {T2_DLG:.3f}, tApp = {T2_S2:.3f}, tWin = Math.max({{w:B2S2:Windows}}, tApp + 1.0);
      tl.fromTo("#f02-src", {{ autoAlpha: 0 }}, {{ autoAlpha: 1, duration: 0.3 }}, 0.1);
      tl.fromTo("#f02-scr", {{ autoAlpha: 0, rotationX: 18, y: 40, transformPerspective: 1600 }}, {{ autoAlpha: 1, rotationX: 0, y: 0, transformPerspective: 1600, duration: 0.6, ease: "power3.out" }}, 0.0);
      tl.fromTo("#f02-os0", {{ autoAlpha: 0, y: 16 }}, {{ autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.6)" }}, {{w:B2S1:bản máy tính}});
      // "một artifact": khung quanh artifact trong video, nhãn giải nghĩa
      var tArt = {{w:B2S1:artifact}};
      tl.fromTo("#f02-art", {{ autoAlpha: 0, scale: 1.08 }}, {{ autoAlpha: 1, scale: 1, duration: 0.3, ease: "power2.out" }}, tArt - 0.05);
      tl.fromTo("#f02-artl", {{ autoAlpha: 0, y: 14 }}, {{ autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.6)" }}, tArt + 0.05);
      // "rồi chọn mục cài thành ứng dụng": menu thật của artifact, tô mục Install as app
      tl.to("#f02-scr, #f02-art, #f02-os0, #f02-src", {{ autoAlpha: 0, duration: 0.2, immediateRender: false }}, tMenu);
      // nhãn giải nghĩa artifact ở lại trên cảnh menu (dời lên dải tối đầu khung) cho đủ thời gian đọc
      tl.to("#f02-artl", {{ y: -812, duration: 0.3, ease: "power2.inOut", immediateRender: false }}, tMenu);
      tl.fromTo("#f02-wm", {{ autoAlpha: 0, scale: 1.12 }}, {{ autoAlpha: 1, scale: 1, duration: 0.35, ease: "power3.out" }}, tMenu);
      // giữ khung menu đúng lúc con trỏ thật nằm trên mục Install as app (khung 3,5 s của demo) cho tới khi hộp thoại hiện
      tl.set("#f02-still", {{ opacity: 1 }}, {{w:B2S1:cài}} - 0.02);
      tl.fromTo("#f02-row", {{ autoAlpha: 0, scale: 1.15 }}, {{ autoAlpha: 1, scale: 1, duration: 0.25, ease: "back.out(2)" }}, {{w:B2S1:cài}} - 0.12);
      tl.fromTo("#f02-rowl", {{ autoAlpha: 0, y: 14 }}, {{ autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.6)" }}, {{w:B2S1:chọn}} - 0.05);
      // bấm mục này: hộp thoại cài đặt, rồi bấm Install (trong khoảng lặng trước B2S2)
      tl.to("#f02-wm, #f02-rowl, #f02-artl", {{ autoAlpha: 0, duration: 0.2, immediateRender: false }}, tDlg);
      tl.fromTo("#f02-dw", {{ autoAlpha: 0, y: 40, scale: 0.94 }}, {{ autoAlpha: 1, y: 0, scale: 1, duration: 0.4, ease: "power3.out" }}, tDlg);
      tl.to("#f02-src", {{ autoAlpha: 1, duration: 0.25, immediateRender: false }}, tDlg + 0.1);
      tl.fromTo("#f02-ins", {{ autoAlpha: 0, scale: 1.3 }}, {{ autoAlpha: 1, scale: 1, duration: 0.25, ease: "back.out(2)" }}, tDlg + 0.1);
      tl.fromTo("#f02-insl", {{ autoAlpha: 0, y: 12 }}, {{ autoAlpha: 1, y: 0, duration: 0.28, ease: "back.out(1.6)" }}, tDlg + 0.15);
      // bấm Install: cùng tiếng click (B2S2 - 0,45 s)
      tl.fromTo("#f02-ins", {{ scale: 1 }}, {{ scale: 0.9, duration: 0.08, ease: "power2.in", yoyo: true, repeat: 1, immediateRender: false }}, tApp - 0.2);
      // B2S2: ứng dụng đã cài, biểu tượng ở Dock, cửa sổ riêng; hai hệ điều hành; rồi các ứng dụng mẫu khác lướt nhanh
      tl.to("#f02-dw, #f02-ins, #f02-insl", {{ autoAlpha: 0, y: -20, duration: 0.22, ease: "power2.in", immediateRender: false }}, tApp);
      // "ứng dụng có biểu tượng": phóng vào Dock (biểu tượng quả địa cầu mới), lùi ra ở "cửa sổ"
      tl.to("#f02-vaw", {{ scale: 2.4, duration: 0.45, ease: "power3.inOut", immediateRender: false }}, {{w:B2S2:ứng dụng}});
      tl.fromTo("#f02-dock", {{ autoAlpha: 0, scale: 1.3 }}, {{ autoAlpha: 1, scale: 1, duration: 0.25, ease: "back.out(2)" }}, {{w:B2S2:biểu tượng}});
      tl.to("#f02-dock", {{ autoAlpha: 0, duration: 0.15, immediateRender: false }}, {{w:B2S2:cửa sổ}} - 0.1);
      tl.to("#f02-vaw", {{ scale: 1, duration: 0.45, ease: "power3.inOut", immediateRender: false }}, {{w:B2S2:cửa sổ}} - 0.1);
      // video demo chuyển sang các ứng dụng mẫu khác ở khoảng 10,6 s của demo: đổi chữ trên thanh cửa sổ
      var tSw = {T2_S2 + 1.85:.3f};
      tl.to("#f02-wt1", {{ opacity: 0, duration: 0.2, immediateRender: false }}, tSw);
      tl.to("#f02-wt2", {{ opacity: 1, duration: 0.2, immediateRender: false }}, tSw + 0.05);
      tl.fromTo("#f02-aw", {{ autoAlpha: 0, scale: 0.92 }}, {{ autoAlpha: 1, scale: 1, duration: 0.4, ease: "back.out(1.3)" }}, tApp + 0.05);
      tl.fromTo("#f02-t1", {{ autoAlpha: 0, y: 14 }}, {{ autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.6)" }}, {{w:B2S2:biểu tượng}});
      tl.fromTo("#f02-t2", {{ autoAlpha: 0, y: 14 }}, {{ autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.6)" }}, {{w:B2S2:cửa sổ}});
      tl.fromTo("#f02-os1", {{ autoAlpha: 0, scale: 0.7 }}, {{ autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, {{w:B2S2:mác ô ét}});
      tl.fromTo("#f02-os2", {{ autoAlpha: 0, scale: 0.7 }}, {{ autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }}, tWin);
      tl.fromTo("#f02-t3", {{ autoAlpha: 0, x: -20 }}, {{ autoAlpha: 1, x: 0, duration: 0.3, ease: "back.out(1.6)" }}, {{w:B2S2:riêng}});
"""
)

# ---------------------------------------------------------------- 03: ứng dụng mẫu của kỹ sư Anthropic
# Nền là màn hình pixel của trang Felix's Demo Apps; ba cửa sổ ứng dụng mẫu bật lên đúng chữ (sửa ảnh, quản lý tệp,
# bản đồ cơ thể người); cuối câu hiện câu của Felix: người đọc không cần biết lập trình.
WIN3 = [("f03-w1", "linnet_1", "Linnet · sửa ảnh nhiều lớp", 40, 296, -2.5, "sửa ảnh"),
        ("f03-w2", "phosphor_1", "Phosphor · quản lý tệp", 338, 446, 2.0, "quản lý"),
        ("f03-w3", "marrow_1", "Marrow · bản đồ cơ thể người", 112, 596, -1.2, "bản đồ")]
WIN3_HTML = "".join(
    f'<div class="k-win f03-w" id="{wid}" style="left:{x}px;top:{y}px;transform:rotate({r}deg);"><div class="k-win-bar">{DOTS}<span>{ten}</span></div>'
    f'<img src="assets/web/felix/anh/{anh}.jpg" alt="" style="top:52px;width:700px;height:438px;" /></div>' for wid, anh, ten, x, y, r, _ in WIN3)
WIN3_JS = "\n".join(
    f'      tl.fromTo("#{wid}", {{ autoAlpha: 0, scale: 0.4, y: 120 }}, {{ autoAlpha: 1, scale: 1, y: 0, duration: 0.42, ease: "back.out(1.5)" }}, {{w:B3S1:{moc}}} - 0.12);'
    for wid, _, _, _, _, _, moc in WIN3)
CANH["03-vi-du"] = dict(theme="pixel", nen="assets/web/felix/man_hinh.jpg", cau=["B3S1"],
                        nen_dong='tl.fromTo("#f03-plate", { x: -120 }, { x: -640, duration: D, ease: "none" }, 0);', css="""
    #root .f03-w { width: 700px; height: 490px; }
    #root #f03-note { position: absolute; left: 72px; top: 1080px; width: 858px; box-sizing: border-box; padding: 14px 26px 16px; font-size: 28px; font-weight: 500; line-height: 38px;
                      background: rgba(14, 16, 52, 0.94); }
    #root #f03-q { position: absolute; left: 72px; top: 214px; opacity: 0; }
""", than=f"""
    <div class="k-shade k-shade-top"></div><div class="k-shade k-shade-bot"></div>
    {WIN3_HTML}
    <div class="k-tag" id="f03-q" data-layout-allow-overlap>Felix viết: bạn không cần biết lập trình</div>
    <div class="k-glass" id="f03-note" data-layout-allow-overlap>Ứng dụng mẫu trên trang của Felix, kỹ sư Anthropic; trang ghi rõ đây không phải sản phẩm chính thức.</div>
""", js=f"""
{WIN3_JS}
      tl.fromTo("#f03-note", {{ autoAlpha: 0, y: 16 }}, {{ autoAlpha: 1, y: 0, duration: 0.32, ease: "power2.out" }}, 0.3);
      tl.fromTo("#f03-q", {{ autoAlpha: 0, scale: 0.85 }}, {{ autoAlpha: 1, scale: 1, duration: 0.35, ease: "back.out(1.8)" }}, 0.3);
"""
)

# ---------------------------------------------------------------- 04: không phải đóng gói, ký số, tạo khóa API
IC_HOP = '<svg viewBox="0 0 24 24"><path d="M3.5 7.5 L12 3 L20.5 7.5 V16.5 L12 21 L3.5 16.5 Z M3.5 7.5 L12 12 L20.5 7.5 M12 12 V21" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'
IC_KY = '<svg viewBox="0 0 24 24"><path d="M4 19 C7 13 9 9 11 9 C13 9 11 16 13.5 16 C15.5 16 16 12 18 12 C19.5 12 19 15 20.5 15" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M3.5 21.5 H20.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
IC_KHOA = '<svg viewBox="0 0 24 24"><circle cx="8" cy="12" r="4.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M12.2 12 H21 M17.5 12 V15.5 M20 12 V14.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
IC_X = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M8 8 L16 16 M16 8 L8 16" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round"/></svg>'
IC_OK = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M7 12.5 L10.5 16 L17 8.5" fill="none" stroke="#ffffff" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
VIEC = [("f04-r1", IC_HOP, "Đóng gói ứng dụng", "packaging", "đóng gói"), ("f04-r2", IC_KY, "Ký số ứng dụng", "code signing", "ký số"),
        ("f04-r3", IC_KHOA, "Tạo khóa API", "API key", "tạo khóa")]
VIEC_HTML = "".join(
    f'<div class="f04-r" id="{rid}" style="top:{36 + i * 150}px;"><span class="f04-ic">{ic}</span><span class="f04-t">{ten}<span class="f04-en">{en}</span></span>'
    f'<span class="f04-x" id="{rid}x">{IC_X}</span><span class="f04-st" id="{rid}s"></span></div>' for i, (rid, ic, ten, en, _) in enumerate(VIEC))
VIEC_JS = "\n".join(
    f'      tl.fromTo("#{rid}s", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.3, ease: "power2.out" }}, {{w:B4S1:{moc}}});\n'
    f'      tl.to("#{rid} .f04-t, #{rid} .f04-ic", {{ opacity: 0.5, duration: 0.25, immediateRender: false }}, {{w:B4S1:{moc}}} + 0.15);\n'
    f'      tl.fromTo("#{rid}x", {{ autoAlpha: 0, scale: 0.3, rotation: -40 }}, {{ autoAlpha: 1, scale: 1, rotation: 0, duration: 0.3, ease: "back.out(2.2)" }}, {{w:B4S1:{moc}}} + 0.1);'
    for rid, _, _, _, moc in VIEC)
CANH["04-khong-dong-goi"] = dict(theme="brand", cau=["B4S1"], css="""
    #root #f04-card { position: absolute; left: 72px; top: 330px; width: 936px; height: 498px; box-sizing: border-box; }
    #root .f04-r { position: absolute; left: 36px; width: 864px; height: 120px; display: flex; align-items: center; gap: 26px; }
    #root .f04-ic { flex: none; width: 84px; height: 84px; border-radius: 22px; background: rgba(255, 255, 255, 0.16); display: flex; align-items: center; justify-content: center; color: #ffffff; }
    #root .f04-ic svg { width: 50px; height: 50px; }
    #root .f04-t { display: flex; flex-direction: column; font-size: 46px; font-weight: 600; line-height: 56px; color: #ffffff; white-space: nowrap; }
    #root .f04-en { font-size: 30px; font-weight: 400; line-height: 38px; color: rgba(255, 255, 255, 0.88); }
    #root .f04-x { position: absolute; right: 8px; top: 30px; width: 60px; height: 60px; color: #e0603c; }
    #root .f04-x svg { width: 60px; height: 60px; }
    #root .f04-st { position: absolute; left: 104px; top: 40px; width: 470px; height: 7px; border-radius: 4px; background: #ffb39a; transform-origin: 0% 50%;
                    box-shadow: 0 0 12px rgba(255, 179, 154, 0.9); }
    #root #f04-r1s { width: 466px; }
    #root #f04-r2s { width: 376px; }
    #root #f04-r3s { width: 330px; }
    #root #f04-ok { position: absolute; left: 72px; top: 860px; width: 936px; height: 150px; box-sizing: border-box; display: flex; align-items: center; gap: 26px; padding: 0 36px;
                    border-radius: 34px; background: #ffffff; box-shadow: 0 30px 60px rgba(8, 9, 30, 0.3); }
    #root #f04-ok .ic { flex: none; width: 76px; height: 76px; color: #2f33c9; }
    #root #f04-ok .ic svg { width: 76px; height: 76px; }
    #root #f04-ok .t { display: flex; flex-direction: column; font-size: 44px; font-weight: 700; line-height: 54px; color: var(--ink); white-space: nowrap; }
    #root #f04-ok .s { font-size: 28px; font-weight: 500; line-height: 36px; color: #3b3f72; }
""", than=f"""
    <div class="k-kicker" id="f04-k" data-layout-allow-overlap>Bạn không phải làm</div>
    <div class="k-glass" id="f04-card" data-layout-allow-overlap>{VIEC_HTML}</div>
    <div id="f04-ok" data-layout-allow-overlap><span class="ic">{IC_OK}</span><span class="t">Dùng tài khoản Claude của bạn<span class="s">Không cần đăng nhập riêng</span></span></div>
    <div class="k-src" id="f04-src" data-layout-allow-overlap>Nguồn: claude.com, 24/11/2026; @ClaudeDevs trên X</div>
""", js=f"""
      tl.fromTo("#f04-k, #f04-src", {{ autoAlpha: 0 }}, {{ autoAlpha: 1, duration: 0.3 }}, 0.05);
      tl.fromTo("#f04-card", {{ autoAlpha: 0, y: 30 }}, {{ autoAlpha: 1, y: 0, duration: 0.4, ease: "power3.out" }}, 0.05);
      tl.fromTo(".f04-r", {{ autoAlpha: 0, x: -30 }}, {{ autoAlpha: 1, x: 0, duration: 0.3, ease: "power3.out", stagger: 0.08 }}, 0.15);
{VIEC_JS}
      var tOk = {{w:B4S1:tài khoản}};
      tl.fromTo("#f04-ok", {{ autoAlpha: 0, y: 30, scale: 0.9 }}, {{ autoAlpha: 1, y: 0, scale: 1, duration: 0.42, ease: "back.out(1.6)" }}, tOk - 0.1);
      tl.fromTo("#f04-ok .ic", {{ scale: 0, rotation: -60 }}, {{ scale: 1, rotation: 0, duration: 0.4, ease: "back.out(2.4)" }}, tOk + 0.05);
"""
)

# ---------------------------------------------------------------- 05: ứng dụng làm được gì
# Cửa sổ ứng dụng mẫu thật (trang của Felix): Sift dùng Claude sắp xếp tệp (B5S1, kèm hai dịch vụ Lịch, Email);
# Vitals trên thanh menu (B5S2); trang demo của Felix và đường link chia sẻ (B5S3).
IC_LICH = '<svg viewBox="0 0 24 24"><rect x="3.5" y="5" width="17" height="15.5" rx="3" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.5 10 H20.5 M8 3 V7 M16 3 V7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
IC_THU = '<svg viewBox="0 0 24 24"><rect x="3" y="5.5" width="18" height="13" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M3.8 7 L12 13 L20.2 7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'
IC_KHOA_MO = '<svg viewBox="0 0 24 24"><rect x="5" y="10.5" width="14" height="10" rx="2.5" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M8.5 10.5 V7.5 C8.5 5.3 10.1 3.8 12 3.8 C13.9 3.8 15.5 5.3 15.5 7.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>'
IC_CHUONG = '<svg viewBox="0 0 24 24"><path d="M6 16.5 V11 C6 7.7 8.7 5 12 5 C15.3 5 18 7.7 18 11 V16.5 L19.5 18 H4.5 Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="M10 20.5 C10.5 21.3 11.2 21.7 12 21.7 C12.8 21.7 13.5 21.3 14 20.5" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>'
IC_VONG = '<svg viewBox="0 0 24 24"><path d="M19 12 A7 7 0 1 1 16.9 7" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><path d="M14.5 3.8 L17.4 7 L13.9 8.6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
IC_GUI = '<svg viewBox="0 0 24 24"><path d="M3.5 11.5 L20.5 4 L15 20.5 L11.5 13.5 Z M11.5 13.5 L20.5 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>'
WIN5_W, WIN5_H = 936, 586
CANH["05-lam-duoc-gi"] = dict(theme="light", cau=["B5S1", "B5S2", "B5S3"], css=f"""
    #root #f05-win {{ left: 72px; top: 300px; width: {WIN5_W}px; height: {WIN5_H + 52}px; }}
    #root .f05-img {{ top: 52px; width: {WIN5_W}px; height: {WIN5_H}px; }}
    #root #f05-i2, #root #f05-i3 {{ opacity: 0; }}
    #root .f05-wt {{ position: absolute; left: 116px; top: 8px; }}
    #root #f05-wt2, #root #f05-wt3 {{ opacity: 0; }}
    #root #f05-cap {{ position: absolute; left: 72px; top: 958px; width: 936px; height: 44px; }}
    #root .f05-c {{ position: absolute; left: 0; top: 0; font-size: 30px; font-weight: 500; line-height: 40px; color: var(--fg); white-space: nowrap; opacity: 0; }}
    #root .f05-chip {{ position: absolute; top: 1030px; opacity: 0; }}
    #root .f05-chip svg {{ width: 40px; height: 40px; color: #2f33c9; flex: none; }}
    #root #f05-cl {{ left: 72px; }}
    #root #f05-lich {{ left: 300px; }}
    #root #f05-mail {{ left: 520px; }}
    #root #f05-lk {{ left: 72px; }}
    #root #f05-tb {{ left: 72px; }}
    #root #f05-mb {{ left: 72px; }}
    #root #f05-up {{ left: 932px; top: 280px; width: 68px; height: 68px; padding: 0; justify-content: center; border-radius: 50%; border: 4px solid #ffffff; background: #2f33c9; color: #ffffff;
                    box-shadow: 0 10px 24px rgba(47, 51, 201, 0.45); }}
    #root #f05-up svg {{ width: 42px; height: 42px; color: #ffffff; }}
    #root #f05-link {{ left: 72px; top: 1030px; font-size: 30px; color: #2f33c9; }}
    #root #f05-ring {{ left: 518px; top: 382px; width: 346px; height: 548px; opacity: 0; border-color: #ffb36b; box-shadow: 0 0 24px rgba(255, 179, 107, 0.95); }}
    #root #f05-bar {{ left: 664px; top: 348px; width: 56px; height: 34px; opacity: 0; border-radius: 10px; border-width: 4px; border-color: #c2410c; box-shadow: 0 0 18px rgba(194, 65, 12, 0.85); }}
""", than=f"""
    <div class="k-kicker" id="f05-k" data-layout-allow-overlap>Ứng dụng đã cài làm được gì</div>
    <div class="k-win" id="f05-win"><div class="k-win-bar">{DOTS}<span class="f05-wt" id="f05-wt1">Sift, ứng dụng mẫu</span><span class="f05-wt" id="f05-wt2">Vitals, ứng dụng mẫu</span><span class="f05-wt" id="f05-wt3">Felix's Demo Apps</span></div>
      <img class="f05-img" id="f05-i1" src="assets/web/felix/anh/sift_1.jpg" alt="" />
      <img class="f05-img" id="f05-i2" src="assets/web/felix/anh/vitals_1.jpg" alt="" />
      <img class="f05-img" id="f05-i3" src="assets/web/felix/man_hinh.jpg" alt="" style="object-position: 0% 50%;" />
    </div>
    <div class="k-ring" id="f05-ring" data-layout-allow-overlap></div>
    <div class="k-ring" id="f05-bar" data-layout-allow-overlap></div>
    <div id="f05-cap">
      <div class="f05-c" id="f05-c1" data-layout-allow-overlap>Sift dùng Claude để sắp xếp tệp theo quy tắc thư mục</div>
      <div class="f05-c" id="f05-c2" data-layout-allow-overlap>Vitals theo dõi hiệu năng máy</div>
      <div class="f05-c" id="f05-c3" data-layout-allow-overlap>Felix chia sẻ các ứng dụng mẫu bằng một link</div>
    </div>
    <div class="k-chip f05-chip" id="f05-cl" data-layout-allow-overlap>Claude</div>
    <div class="k-chip f05-chip" id="f05-lich" data-layout-allow-overlap>{IC_LICH}<span>Lịch</span></div>
    <div class="k-chip f05-chip" id="f05-mail" data-layout-allow-overlap>{IC_THU}<span>Email</span></div>
    <div class="k-chip f05-chip" id="f05-tb" data-layout-allow-overlap>{IC_CHUONG}<span>Thông báo</span></div>
    <div class="k-chip f05-chip" id="f05-mb" data-layout-allow-overlap><span>Thanh menu (macOS) · khay hệ thống (Windows)</span></div>
    <div class="k-chip f05-chip" id="f05-up" data-layout-allow-overlap>{IC_VONG}</div>
    <div class="k-chip f05-chip" id="f05-link" data-layout-allow-overlap>{IC_GUI}<span>claude.ai/artifact/9j53nCVcrSdZyCHtxUZkWJ</span></div>
    <div class="k-src" id="f05-src" data-layout-allow-overlap>Ảnh: ứng dụng mẫu trên trang của Felix, kỹ sư Anthropic</div>
""", js="""
      tl.fromTo("#f05-k, #f05-src", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, 0.05);
      tl.fromTo("#f05-win", { autoAlpha: 0, y: 40, scale: 0.95 }, { autoAlpha: 1, y: 0, scale: 1, duration: 0.45, ease: "back.out(1.3)" }, 0.05);
      tl.fromTo("#f05-i1", { scale: 1.06 }, { scale: 1, duration: 2.2, ease: "power1.out" }, 0.05);
      tl.fromTo("#f05-c1", { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.3 }, 0.35);
      // B5S1: các dịch vụ đã kết nối như lịch, email; viên Claude hiện cùng chữ "dùng được" (lời đọc bỏ chữ Claude, xem TREATMENT.md)
      tl.fromTo("#f05-cl", { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.8)" }, {w:B5S1:dùng được});
      tl.fromTo("#f05-lich", { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.8)" }, {w:B5S1:lịch});
      tl.fromTo("#f05-mail", { autoAlpha: 0, y: 20 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "back.out(1.8)" }, {w:B5S1:email});
      // B5S2: Vitals trên thanh menu; cần bạn cho phép, thông báo
      var t2 = {t0:B5S2} - 0.05;
      tl.to("#f05-cl, #f05-lich, #f05-mail, #f05-c1", { autoAlpha: 0, y: -10, duration: 0.2, immediateRender: false }, t2);
      tl.to("#f05-i2", { opacity: 1, duration: 0.25, immediateRender: false }, t2);
      tl.to("#f05-wt1", { opacity: 0, duration: 0.15, immediateRender: false }, t2);
      tl.to("#f05-wt2", { opacity: 1, duration: 0.15, immediateRender: false }, t2 + 0.05);
      tl.fromTo("#f05-c2", { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.3 }, t2 + 0.1);
      tl.fromTo("#f05-tb", { autoAlpha: 0, scale: 0.8 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }, {w:B5S2:gửi});
      tl.fromTo("#f05-ring", { autoAlpha: 0, scale: 1.1 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "power2.out" }, {w:B5S2:hiện});
      tl.to("#f05-tb", { autoAlpha: 0, duration: 0.2, immediateRender: false }, {w:B5S2:thanh} - 0.05);
      tl.fromTo("#f05-mb", { autoAlpha: 0, scale: 0.8 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }, {w:B5S2:thanh});
      tl.fromTo("#f05-bar", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.25 }, {w:B5S2:thanh});
      // B5S3: sửa artifact thì ứng dụng tự cập nhật; muốn chia sẻ thì gửi link
      var t3 = {t0:B5S3} - 0.05;
      tl.to("#f05-mb, #f05-ring, #f05-bar, #f05-c2", { autoAlpha: 0, duration: 0.2, immediateRender: false }, t3);
      tl.to("#f05-i3", { opacity: 1, duration: 0.25, immediateRender: false }, t3);
      tl.to("#f05-wt2", { opacity: 0, duration: 0.15, immediateRender: false }, t3);
      tl.to("#f05-wt3", { opacity: 1, duration: 0.15, immediateRender: false }, t3 + 0.05);
      tl.fromTo("#f05-i3", { objectPosition: "0% 50%" }, { objectPosition: "100% 50%", duration: Math.max(1, D - t3), ease: "none", immediateRender: false }, t3);
      tl.fromTo("#f05-c3", { autoAlpha: 0, y: 10 }, { autoAlpha: 1, y: 0, duration: 0.3 }, {w:B5S3:muốn} - 0.1);
      tl.fromTo("#f05-up", { autoAlpha: 0, scale: 0.8 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "back.out(2)" }, {w:B5S3:sửa});
      tl.fromTo("#f05-up svg", { rotation: 0 }, { rotation: 360, duration: 0.8, ease: "power2.inOut" }, {w:B5S3:cập nhật});
      tl.fromTo("#f05-i3", { filter: "blur(0px)" }, { filter: "blur(8px)", duration: 0.18, yoyo: true, repeat: 1, ease: "power1.inOut", immediateRender: false }, {w:B5S3:cập nhật});
      tl.fromTo("#f05-link", { autoAlpha: 0, x: -30 }, { autoAlpha: 1, x: 0, duration: 0.35, ease: "back.out(1.6)" }, {w:B5S3:chia sẻ});
      tl.fromTo("#f05-link svg", { x: 0, y: 0 }, { x: 14, y: -10, duration: 0.3, ease: "power2.out", yoyo: true, repeat: 1 }, {w:B5S3:gửi});
"""
)

# ---------------------------------------------------------------- 06: điều kiện dùng, hạn mức
DK = [("f06-a", "Bản thử nghiệm trong Claude bản máy tính", "ok", 330, "thử nghiệm"), ("f06-b", "Mọi gói: đang triển khai dần", "ok", 430, "triển khai"),
      ("f06-c", "Team: bật sẵn, riêng toàn quyền máy tính bị tắt", "ok", 530, "cho"), ("f06-d", "Enterprise: chờ chủ sở hữu tổ chức bật", "cho", 630, "mọi"),
      ("f06-e", "Trừ tổ chức HIPAA-ready và bản triển khai hybrid", "khong", 730, "gói")]
IC_CHO = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2.2"/><path d="M12 7 V12 L15.5 14" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>'
DK_HTML = "".join(
    f'<div class="k-chip f06-r f06-{loai}" id="{did}" style="top:{y}px;" data-layout-allow-overlap><span class="f06-ic">{IC_OK if loai == "ok" else (IC_CHO if loai == "cho" else IC_X)}</span><span>{chu}</span></div>'
    for did, chu, loai, y, _ in DK)
DK_JS = "\n".join(
    (f'      tl.fromTo("#{did}", {{ autoAlpha: 0, x: -30 }}, {{ autoAlpha: 1, x: 0, duration: 0.3, ease: "power3.out" }}, Math.max(0.12, {{w:B6S1:{moc}}} - 0.1));'
     if moc else
     f'      tl.fromTo("#{did}", {{ autoAlpha: 0, x: -30 }}, {{ autoAlpha: 1, x: 0, duration: 0.3, ease: "power3.out" }}, {{w:B6S1:mọi gói}} + {0.35 * k:.2f});')
    for k, (did, _, _, _, moc) in enumerate(DK, start=-1))
CANH["06-dieu-kien"] = dict(theme="brand", cau=["B6S1", "B6S2"], css="""
    #root .f06-r { position: absolute; left: 72px; height: 82px; box-sizing: border-box; font-size: 32px; padding: 0 30px 0 16px; }
    #root .f06-ic { flex: none; width: 50px; height: 50px; }
    #root .f06-ic svg { width: 50px; height: 50px; }
    #root .f06-ok .f06-ic { color: #a4e9ec; }
    #root .f06-cho .f06-ic { color: #ffd98a; }
    #root .f06-khong .f06-ic { color: #ffb39a; }
    #root #f06-meter { position: absolute; left: 72px; top: 830px; width: 936px; height: 156px; box-sizing: border-box; padding: 24px 34px; }
    #root .f06-mt { font-size: 34px; font-weight: 600; line-height: 44px; color: #ffffff; white-space: nowrap; }
    #root .f06-tr { position: relative; margin-top: 22px; width: 868px; height: 40px; border-radius: 20px; background: rgba(255, 255, 255, 0.18); overflow: hidden; }
    #root #f06-fill { position: absolute; left: 0; top: 0; width: 868px; height: 40px; border-radius: 20px; background: linear-gradient(90deg, #a4e9ec, #ffffff); transform-origin: 0% 50%; transform: scaleX(0.18); }
    #root .f06-plus { position: absolute; top: 918px; padding: 0 14px; border-radius: 999px; background: #12143a; font-size: 28px; font-weight: 700; line-height: 44px;
                      color: #ffd98a; opacity: 0; white-space: nowrap; box-shadow: 0 6px 16px rgba(8, 9, 30, 0.35); }
    #root #f06-p1 { left: 560px; }
    #root #f06-p2 { left: 699px; }
    #root #f06-p3 { left: 838px; }
    #root #f06-foot { position: absolute; left: 72px; top: 1012px; width: 936px; font-size: 30px; font-weight: 500; line-height: 40px; color: #ffffff; }
""", than=f"""
    <div class="k-kicker" id="f06-k" data-layout-allow-overlap>Ai dùng được</div>
    {DK_HTML}
    <div class="k-glass" id="f06-meter" data-layout-allow-overlap><div class="f06-mt">Hạn mức sử dụng của gói</div><div class="f06-tr"><div id="f06-fill"></div></div></div>
    <div class="f06-plus" id="f06-p1" data-layout-allow-overlap>+1</div><div class="f06-plus" id="f06-p2" data-layout-allow-overlap>+1</div><div class="f06-plus" id="f06-p3" data-layout-allow-overlap>+1</div>
    <div id="f06-foot" data-layout-allow-overlap>Cần có mạng và đăng nhập Claude để mở ứng dụng.<br>Không cài được Claude Docs, Slides, Sheets.</div>
    <div class="k-src" id="f06-src" data-layout-allow-overlap>Nguồn: claude.com, 24/11/2026; @ClaudeDevs trên X</div>
""", js=f"""
      tl.fromTo("#f06-k, #f06-src", {{ autoAlpha: 0 }}, {{ autoAlpha: 1, duration: 0.3 }}, 0.05);
{DK_JS}
      // B6S2: thanh hạn mức đầy dần, lúc làm ứng dụng rồi theo từng lượt ứng dụng dùng Claude (câu viết "Claude làm việc cho nó": ở "dùng Claude đều" tai tiếng Anh nghe "Cloud" 18/18 bản)
      tl.fromTo("#f06-meter", {{ autoAlpha: 0, y: 30 }}, {{ autoAlpha: 1, y: 0, duration: 0.36, ease: "power3.out" }}, {{t0:B6S2}} - 0.15);
      var tg = {{w:B6S2:Claud}};
      tl.to("#f06-fill", {{ scaleX: 0.40, duration: 0.3, ease: "back.out(2)", immediateRender: false }}, {{w:B6S2:làm ứng dụng}});
      [0, 1, 2].forEach(function (k) {{
        tl.to("#f06-fill", {{ scaleX: 0.40 + 0.16 * (k + 1), duration: 0.22, ease: "back.out(2)", immediateRender: false }}, tg + k * 0.32);
        tl.fromTo("#f06-p" + (k + 1), {{ autoAlpha: 0, scale: 0.4, y: 0 }}, {{ autoAlpha: 1, scale: 1, y: -6, duration: 0.25, ease: "back.out(2.4)", immediateRender: false }}, tg + k * 0.32);
        tl.to("#f06-p" + (k + 1), {{ autoAlpha: 0, duration: 0.25, immediateRender: false }}, tg + k * 0.32 + 0.4);
      }});
      tl.fromTo("#f06-foot", {{ autoAlpha: 0, y: 12 }}, {{ autoAlpha: 1, y: 0, duration: 0.3 }}, {{t0:B6S2}} + 0.65);
      // chuyển cảnh light sang 07 (0,7 s, hai cảnh chồng nhau): chữ cảnh này lui trước để không đè chữ ba thẻ quyền (check 25/11)
      tl.to("#f06-k, .f06-r, #f06-meter, .f06-plus, #f06-foot, #f06-src", {{ autoAlpha: 0, duration: 0.2, immediateRender: false }}, D - 0.7);
"""
)

# ---------------------------------------------------------------- 07: ba mức quyền
MUC = [("f07-m1", "1", "Mặc định", "Chỉ làm được như khi chạy trong trình duyệt", ""),
       ("f07-m2", "2", "Quyền ứng dụng", "Thông báo, phím tắt toàn hệ thống, cửa sổ luôn ở trên", ""),
       ("f07-m3", "3", "Toàn quyền máy tính", "Chạy chương trình; đọc, sửa, xóa tệp, không hỏi từng lần", " f07-hot")]
MUC_HTML = "".join(
    f'<div class="k-glass f07-m{hot}" id="{mid}" style="top:{330 + i * 168}px;" data-layout-allow-overlap><span class="f07-n">{so}</span>'
    f'<span class="f07-tx"><span class="f07-tt">{ten}</span><span class="f07-ds" id="{mid}-ds">{mo_ta}</span></span></div>' for i, (mid, so, ten, mo_ta, hot) in enumerate(MUC))
# B7S2: hai ứng dụng mẫu của Felix minh họa "chạy chương trình khác" (Tern, cửa sổ dòng lệnh) và "sửa, xóa tệp"
# (Phosphor, trình quản lý tệp); hộp thoại tiếng Anh đã chiếu cỡ lớn ở cảnh 02 nên không lặp lại ở đây (QA bản dựng 2).
WIN7 = [("f07-w1", "tern_1", "Tern · dòng lệnh", 72), ("f07-w2", "phosphor_1", "Phosphor · quản lý tệp", 548)]
WIN7_HTML = "".join(
    f'<div class="k-win f07-w" id="{wid}" style="left:{x}px;" data-layout-allow-overlap><div class="k-win-bar">{DOTS}<span>{ten}</span></div>'
    f'<img src="assets/web/felix/anh/{anh}.jpg" alt="" style="top:52px;width:460px;height:288px;" /></div>'
    f'<div class="k-ring f07-wr" id="{wid}r" style="left:{x - 10}px;" data-layout-allow-overlap></div>' for wid, anh, ten, x in WIN7)
CANH["07-quyen"] = dict(theme="light", cau=["B7S1", "B7S2", "B7S3"], css="""
    #root .f07-m { position: absolute; left: 72px; width: 936px; height: 150px; box-sizing: border-box; display: flex; align-items: center; gap: 20px; padding: 0 26px; }
    #root .f07-n { flex: none; width: 76px; height: 76px; border-radius: 50%; background: #e6e7fe; color: #2f33c9; display: flex; align-items: center; justify-content: center;
                   font-size: 38px; font-weight: 700; }
    #root .f07-tx { display: flex; flex-direction: column; }
    #root .f07-tt { font-size: 42px; font-weight: 700; line-height: 52px; color: var(--ink); white-space: nowrap; }
    #root .f07-ds { font-size: 28px; font-weight: 400; line-height: 36px; color: #3b3f72; white-space: nowrap; }
    #root .f07-hot { border-color: #f0b27a !important; }
    #root .f07-hot .f07-n { background: #fde3c8; color: var(--warn); }
    #root #f07-m1-ds { align-self: flex-start; background: linear-gradient(rgba(255, 196, 90, 0.6), rgba(255, 196, 90, 0.6)) no-repeat 0 90% / 0% 42%; }
    #root .f07-w { top: 836px; width: 460px; height: 340px; opacity: 0; }
    #root .f07-wr { top: 826px; width: 480px; height: 360px; opacity: 0; border-color: #f0b27a; border-radius: 30px; box-shadow: 0 0 24px rgba(240, 178, 122, 0.95); }
    #root #f07-stw { position: absolute; left: 72px; top: 872px; width: 936px; text-align: center; }
    #root #f07-stamp { display: inline-block; box-sizing: border-box; padding: 18px 34px 20px; border: 6px solid #c2410c; border-radius: 22px; white-space: nowrap;
                       background: rgba(255, 247, 237, 0.97); color: #9a3412; font-size: 46px; font-weight: 800; line-height: 56px; text-align: center; transform: rotate(-3deg);
                       box-shadow: 0 24px 50px rgba(154, 52, 18, 0.25); opacity: 0; }
    #root .f07-note { position: absolute; left: 72px; width: 936px; box-sizing: border-box; padding: 14px 26px 16px; font-size: 28px; font-weight: 500; line-height: 38px; white-space: nowrap; opacity: 0; }
    #root #f07-n1 { top: 1012px; }
    #root #f07-n2 { top: 1100px; }
    #root #f07-src { top: 1198px; }
""", than=f"""
    <div class="k-kicker" id="f07-k" data-layout-allow-overlap>Ba mức quyền</div>
    {MUC_HTML}
    {WIN7_HTML}
    <div id="f07-stw" data-layout-allow-overlap><span id="f07-stamp">Anthropic không duyệt trước</span></div>
    <div class="k-glass f07-note" id="f07-n1" data-layout-allow-overlap>Toàn quyền: chỉ cho ứng dụng do bạn hoặc tổ chức của bạn làm</div>
    <div class="k-glass f07-note" id="f07-n2" data-layout-allow-overlap>Sau mỗi lần cập nhật, Claude hỏi lại quyền</div>
    <div class="k-src" id="f07-src" data-layout-allow-overlap>Nguồn: claude.com, 24/11/2026; ảnh: ứng dụng mẫu của Felix</div>
""", js="""
      tl.fromTo("#f07-k, #f07-src", { autoAlpha: 0 }, { autoAlpha: 1, duration: 0.3 }, 0.05);
      tl.fromTo(".f07-m", { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.36, ease: "power3.out", stagger: 0.09 }, 0.08);
      // B7S1: mức 1 sáng, hai mức kia mờ
      tl.to("#f07-m2, #f07-m3", { opacity: 0.45, duration: 0.25, immediateRender: false }, {w:B7S1:ứng dụng});
      tl.fromTo("#f07-m1", { scale: 1 }, { scale: 1.03, duration: 0.25, ease: "power2.out", immediateRender: false }, {w:B7S1:ứng dụng});
      tl.fromTo("#f07-m1-ds", { backgroundSize: "0% 42%" }, { backgroundSize: "100% 42%", duration: 0.5, ease: "power2.out", immediateRender: false }, {w:B7S1:trình duyệt} - 0.1);
      // B7S2: Tern bật ở "chạy" (chương trình khác), Phosphor ở "sửa" (tệp); mức 3 sáng và hai cửa sổ viền cam ở "toàn quyền"
      tl.fromTo("#f07-w1", { autoAlpha: 0, scale: 0.5, y: 80 }, { autoAlpha: 1, scale: 1, y: 0, duration: 0.4, ease: "back.out(1.5)" }, {w:B7S2:chạy} - 0.1);
      tl.fromTo("#f07-w2", { autoAlpha: 0, scale: 0.5, y: 80 }, { autoAlpha: 1, scale: 1, y: 0, duration: 0.4, ease: "back.out(1.5)" }, {w:B7S2:sửa} - 0.1);
      tl.fromTo(".f07-w img", { scale: 1 }, { scale: 1.07, duration: 3, ease: "none", immediateRender: false }, {w:B7S2:chạy});
      tl.fromTo(".f07-wr", { autoAlpha: 0, scale: 1.06 }, { autoAlpha: 1, scale: 1, duration: 0.28, ease: "power2.out", immediateRender: false }, {w:B7S2:toàn quyền});
      tl.to("#f07-m1", { opacity: 0.45, scale: 1, duration: 0.25, immediateRender: false }, {w:B7S2:toàn quyền});
      tl.to("#f07-m3", { opacity: 1, duration: 0.25, immediateRender: false }, {w:B7S2:toàn quyền});
      tl.fromTo("#f07-m3", { scale: 1 }, { scale: 1.04, duration: 0.3, ease: "back.out(2)", immediateRender: false }, {w:B7S2:toàn quyền});
      // B7S3: hộp thoại lui, con dấu; hai ghi chú
      tl.to(".f07-w, .f07-wr", { autoAlpha: 0, y: -16, duration: 0.2, immediateRender: false }, {t0:B7S3} - 0.05);
      tl.fromTo("#f07-stamp", { autoAlpha: 0, scale: 1.7 }, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "power4.in" }, {w:B7S3:không duyệt} - 0.15);
      tl.fromTo("#f07-stamp", { x: 0 }, { x: 7, duration: 0.05, yoyo: true, repeat: 3, ease: "none", immediateRender: false }, {w:B7S3:không duyệt} + 0.15);
      tl.fromTo("#f07-n1", { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "power2.out" }, {w:B7S3:chỉ nên});
      tl.fromTo("#f07-n2", { autoAlpha: 0, y: 16 }, { autoAlpha: 1, y: 0, duration: 0.3, ease: "power2.out" }, {w:B7S3:chỉ nên} + 0.4);
"""
)

# ---------------------------------------------------------------- 08: hỏi người xem, khung kết CAAITE
sys.path.insert(0, str(Path(__file__).resolve().parent))  # python -I không tự thêm thư mục của tệp chạy
from khung_ket import KET_LOGO, KET_CSS, KET_THAN, doi_tien_to  # noqa: E402

ICON8 = ["bonsai", "debris", "marrow", "linnet", "alcove", "footprint", "tern", "phosphor", "sift", "tally", "vitals"]
ICON8_HTML = "".join(
    f'<img class="f08-ic" id="f08-ic{i}" src="assets/web/felix/icon/{ten}.png" alt="" style="left:{60 + (i % 6) * 164 + (i // 6) * 82}px;top:{950 + (i // 6) * 140}px;" data-layout-allow-overlap />'
    for i, ten in enumerate(ICON8))
CANH["08-ket"] = dict(theme="brand", cau=["B8S1", "B8S2"], css=doi_tien_to(KET_CSS, "f08") + """
    #root #f08-q { position: absolute; left: 72px; top: 280px; width: 936px; font-size: 56px; font-weight: 600; line-height: 70px; color: #ffffff; text-align: center; }
    #root .f08-nb { white-space: nowrap; }
    #root .f08-opt { position: absolute; top: 500px; width: 420px; height: 150px; box-sizing: border-box; display: flex; align-items: center; justify-content: center; gap: 18px;
                     font-size: 56px; font-weight: 700; color: #ffffff; }
    #root #f08-o1 { left: 72px; }
    #root #f08-o2 { left: 588px; }
    #root .f08-opt svg { width: 58px; height: 58px; flex: none; }
    #root #f08-o1 svg { color: #a4e9ec; }
    #root #f08-o2 svg { color: #ffb39a; }
    #root .f08-ic { position: absolute; width: 118px; height: 119px; opacity: 0; }
    #root #f08-tray { position: absolute; left: 44px; top: 934px; width: 992px; height: 290px; border-radius: 30px;
                      background: linear-gradient(180deg, #aaccee 0%, #ccddee 50%, #ffddcc 100%); box-shadow: 0 24px 48px rgba(8, 9, 30, 0.3); opacity: 0; }
""", than=doi_tien_to(KET_LOGO, "f08") + f"""
    <div id="f08-q" data-layout-allow-overlap>Bạn có cấp toàn quyền <span class="f08-nb">cho ứng dụng mình làm không?</span></div>
    <div class="k-glass f08-opt" id="f08-o1" data-layout-allow-overlap>{IC_OK}<span>Có</span></div>
    <div class="k-glass f08-opt" id="f08-o2" data-layout-allow-overlap>{IC_X}<span>Không</span></div>
    <div id="f08-tray" data-layout-allow-overlap></div>
    {ICON8_HTML}
""" + doi_tien_to(KET_THAN, "f08"), js="""
      var tQ = 0.12, tO = Math.max({w:B8S1:không}, tQ + 0.5);
      var tCmt = Math.max({t0:B8S2}, tO + 0.4);
      var tK = Math.max({t1:B8S2}, tCmt + 0.45);
      tl.fromTo("#f08-logo", { y: 0 }, { y: -12, duration: D, ease: "none" }, 0);
      tl.fromTo("#f08-q", { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.4, ease: "power3.out" }, tQ);
      tl.fromTo("#f08-tray", { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.35, ease: "power3.out" }, 0.12);
      tl.fromTo(".f08-ic", { autoAlpha: 0, y: 40, scale: 0.6 }, { autoAlpha: 1, y: 0, scale: 1, duration: 0.4, ease: "back.out(1.8)", stagger: 0.05 }, 0.2);
      tl.fromTo(".f08-ic", { y: 0 }, { y: -10, duration: 0.9, ease: "sine.inOut", yoyo: true, repeat: 5, stagger: 0.07, immediateRender: false }, 0.8);
      tl.fromTo("#f08-o1", { autoAlpha: 0, x: -40 }, { autoAlpha: 1, x: 0, duration: 0.36, ease: "back.out(1.5)" }, tO);
      tl.fromTo("#f08-o2", { autoAlpha: 0, x: 40 }, { autoAlpha: 1, x: 0, duration: 0.36, ease: "back.out(1.5)" }, tO + 0.12);
      tl.fromTo("#f08-cmt", { autoAlpha: 0, scale: 0.6 }, { autoAlpha: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, tCmt);
      tl.fromTo("#f08-bubble", { rotation: -18, transformOrigin: "30% 90%" }, { rotation: 0, transformOrigin: "30% 90%", duration: 0.6, ease: "elastic.out(1, 0.45)" }, tCmt + 0.15);
      tl.to("#f08-q, #f08-o1, #f08-o2, .f08-ic, #f08-tray, #f08-hdr", { y: -40, autoAlpha: 0, duration: 0.22, ease: "power2.in", stagger: 0.01, immediateRender: false }, tK);
      // viên Bình luận ở lại tới khung cuối: về lề trái dưới ba viên liên hệ (đáy 1128 px), nhịp nhẹ
      tl.to("#f08-cmt", { x: -279, y: 362, scale: 0.85, transformOrigin: "0% 50%", duration: 0.45, ease: "power3.inOut", immediateRender: false }, tK + 0.2);
      tl.to("#f08-cmt", { scale: 0.92, duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 1, immediateRender: false }, tK + 1.0);
      tl.fromTo("#f08-kicker, #f08-name, #f08-center, #f08-dept", { yPercent: 110, autoAlpha: 0 }, { yPercent: 0, autoAlpha: 1, duration: 0.6, ease: "power3.out", stagger: 0.12 }, tK + 0.3);
      tl.fromTo("#f08-swoosh-line path", { strokeDashoffset: 1, opacity: 1 }, { strokeDashoffset: 0, opacity: 1, duration: 0.7, ease: "power2.out" }, tK);
      tl.fromTo("#f08-swoosh path", { fillOpacity: 0 }, { fillOpacity: 1, duration: 0.4, ease: "power1.out" }, tK + 0.6);
      tl.to("#f08-swoosh-line path", { opacity: 0, duration: 0.3, ease: "power1.out", immediateRender: false }, tK + 0.9);
      tl.fromTo("#f08-leg-left, #f08-leg-inner, #f08-leg-right", { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "power3.out", stagger: 0.1 }, tK + 0.25);
      tl.fromTo("#f08-crossbar", { x: -60, opacity: 0 }, { x: 0, opacity: 1, duration: 0.35, ease: "back.out(2)" }, tK + 0.75);
      var tS = tK + 1.1;
      tl.fromTo("#f08-bloom", { opacity: 0, scale: 0.3 }, { opacity: 0.9, scale: 1.2, duration: 0.3, ease: "power2.out" }, tS);
      tl.to("#f08-bloom", { opacity: 0.3, scale: 1, duration: 0.45, ease: "power2.inOut", immediateRender: false }, tS + 0.3);
      tl.fromTo("#f08-star", { opacity: 1, scale: 0, rotation: 45 }, { opacity: 1, scale: 1.2, rotation: 0, duration: 0.35, ease: "power3.out" }, tS);
      tl.to("#f08-star", { scale: 1, duration: 0.25, ease: "power2.inOut", immediateRender: false }, tS + 0.35);
      tl.fromTo("#f08-c-web, #f08-c-mail, #f08-c-fb", { autoAlpha: 0, scale: 0.7, transformOrigin: "0% 50%" }, { autoAlpha: 1, scale: 1, transformOrigin: "0% 50%", duration: 0.5, ease: "back.out(1.4)", stagger: 0.1 }, tK + 0.5);
"""
)


def main() -> None:
    chi = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.html"):  # xóa cảnh của reel cũ không còn trong danh sách
        if f.stem not in CANH:
            f.unlink()
    for ma, c in CANH.items():
        if chi and ma not in chi:
            continue
        t = bo_cuc(ma, c)
        t = re.sub(r"[ \t]+\n", "\n", t)
        (OUT / f"{ma}.html").write_text(t, encoding="utf-8", newline="\n")
        print(ma, len(t))


if __name__ == "__main__":
    main()
