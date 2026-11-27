"""Ráp index.html của reel từ src_build/scenes.json + voice/narration_timing.json.

Cách dùng:  python src_build/build_index.py

Sinh ra:
  - index.html                 : composition gốc 1080x1920 (khe cảnh, phụ đề, âm thanh, chuyển cảnh)
  - src_build/scene_timing.json: mốc từng cảnh (giờ phim) + mốc cục bộ của từng cụm chữ trong cảnh
  - src_build/audio_plan.json  : kế hoạch trộn cho mix_reel.py (nhạc, lời đọc, SFX theo mốc)

scenes.json:
{
  "narration_offset": 0.45,  "lead": 0.22,  "tail": 2.6,
  "music": "assets/stock/audio/<bản nhạc>-48k.wav", "music_start": 0.0,
  "scenes": [
    {"id": "01-hook", "sentences": ["B1S1"], "transition_in": "none",
     "sfx": [{"match": "GPT-6.1 Sol", "file": "...", "gain_db": -20, "shift": -0.05}]},
    ...
  ]
}
transition_in: none | push | light | pushlight | blur | expand | zoom. Cảnh cuối kéo dài tới hết lời đọc + tail.
expand (ngữ pháp "giao diện mở ra" của phong cách Dark Tech Keynote, lemo-opuscar): cảnh mới hiện từ một khung chữ nhật
"expand_from": [x, y, w, h] (thường là thẻ hoặc ô của cảnh cũ) rồi mở ra kín khung; cảnh cũ lùi nhẹ và tối đi.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
W, H = 1080, 1920
FX = "assets/stock/audio/"
TRANSITION = {  # thời lượng chuyển cảnh (giây), SFX mặc định, lệch SFX so với mốc cắt
    "push": (0.5, FX + "sfx-whoosh-short-soft-pixabay-48k.wav", -21.0, -0.06),
    "light": (0.7, FX + "sfx-sweep-magic-shimmer-transition-mixkit-2638-48k.wav", -20.0, -1.08),  # đỉnh tệp ở 1,31 s trùng quầng sáng ở mốc cắt + 0,23 s (QA 10/10)
    "pushlight": (0.55, FX + "sfx-sweep-magic-shimmer-transition-mixkit-2638-48k.wav", -19.0, -0.22),
    "blur": (0.8, FX + "sfx-whoosh-cinematic-long-swell-pixabay-48k.wav", -23.0, -2.25),  # đỉnh tệp ở 2,54 s rơi vào mốc cắt + 0,29 s (QA 25/11)
    "expand": (0.6, FX + "sfx-whoosh-short-soft-pixabay-48k.wav", -22.0, -0.05),
    # zoom: cảnh cũ phóng to và mờ đi như lao xuyên qua, cảnh mới thu từ lớn về vừa khung
    "zoom": (0.45, FX + "sfx-whoosh-fast-cinematic-transition-mixkit-1492-48k.wav", -23.0, -0.86),  # đỉnh tệp ở 1,06 s rơi vào mốc cắt + 0,2 s (QA 25/11)
    "none": (0.0, None, 0.0, 0.0),
}


def nap_vi_tri_tu():
    """Hàm (mã câu, chữ, lần) -> vị trí từ trong bản đọc, để mốc âm thanh ghi theo chữ ("tu") thay cho số thứ tự."""
    import re
    import unicodedata
    tl = {c["id"]: c for c in json.loads((ROOT / "voice" / "src" / "tts_lines.json").read_text(encoding="utf-8"))["cau"]}

    def roman(text: str) -> list:
        t = unicodedata.normalize("NFC", text).strip().lower()
        t = re.sub(r"(?<=\w)-(?=\w)", " ", t)
        t = unicodedata.normalize("NFD", t.replace("đ", "d"))
        t = "".join(c for c in t if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z' ]", " ", t).split()

    def vi_tri(sid: str, tu: str, lan: int = 1) -> int:
        words, seq, dem = roman(tl[sid]["tts"]), roman(tu), 0
        for i in range(len(words) - len(seq) + 1):
            if words[i:i + len(seq)] == seq:
                dem += 1
                if dem == lan:
                    return i
        raise SystemExit(f"scenes.json: không thấy '{tu}' trong {sid}")
    return vi_tri


def r3(x: float) -> float:
    return round(x + 1e-9, 3)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    real = ROOT / "voice" / "narration_timing.json"
    ap.add_argument("--timing", default=str(real if real.exists() else ROOT / "voice" / "narration_timing_est.json"))
    a = ap.parse_args()
    print("mốc lời đọc:", Path(a.timing).name)
    cfg = json.loads((ROOT / "src_build" / "scenes.json").read_text(encoding="utf-8"))
    timing = json.loads(Path(a.timing).read_text(encoding="utf-8"))
    sent = {s["id"]: s for s in timing["sentences"]}
    T0 = float(cfg["narration_offset"])
    lead = float(cfg.get("lead", 0.22))
    tail = float(cfg.get("tail", 2.6))
    scenes = cfg["scenes"]
    vi_tri = nap_vi_tri_tu()
    for sc in scenes:  # mốc âm thanh ghi theo chữ: {"sid": "B1S1", "tu": "cài"} -> "w" là vị trí chữ đó
        for cue in sc.get("sfx", []):
            if cue.get("tu"):
                cue["w"] = vi_tri(cue["sid"], cue["tu"], int(cue.get("lan", 1)))
    if cfg.get("music_hit_anchor", {}).get("tu"):
        a = cfg["music_hit_anchor"]
        a["w"] = vi_tri(a["sid"], a["tu"], int(a.get("lan", 1)))

    starts = []
    for i, sc in enumerate(scenes):
        first = sent[sc["sentences"][0]]
        # "truoc": số giây cảnh bắt đầu sớm hơn câu đầu của nó (để khoảng nghỉ dài trước câu nằm trong cảnh này)
        starts.append(0.0 if i == 0 else r3(first["start"] + T0 - lead - float(sc.get("truoc", 0.0))))
    last_sent = sent[scenes[-1]["sentences"][-1]]
    total = r3(last_sent["end"] + T0 + tail)

    slots = []
    for i, sc in enumerate(scenes):
        start = starts[i]
        if i + 1 < len(scenes):
            dt = TRANSITION[scenes[i + 1].get("transition_in", "push")][0]
            end = r3(starts[i + 1] + dt)
        else:
            end = total
        slots.append({"id": sc["id"], "start": start, "end": end, "duration": r3(end - start),
                      "transition_in": sc.get("transition_in", "push" if i else "none"),
                      "expand_from": sc.get("expand_from")})

    # mốc cục bộ của từng cụm chữ (để viết cue trong storyboard / packet)
    scene_timing = {"total": total, "narration_offset": T0, "scenes": []}
    for i, sc in enumerate(scenes):
        s0 = slots[i]["start"]
        cues = []
        for sid in sc["sentences"]:
            s = sent[sid]
            cues.append({"sentence": sid, "display": s["display"], "local_start": r3(s["start"] + T0 - s0),
                         "local_end": r3(s["end"] + T0 - s0),
                         "chunks": [{"t": c["display"], "local": r3(c["start"] + T0 - s0), "local_end": r3(c["end"] + T0 - s0)}
                                    for c in s["chunks"]],
                         # mốc đầu từng từ của bản đọc (tts), để cảnh bám đúng chữ như "tám mươi", "ây một trăm"
                         "words": [r3(w[0] + T0 - s0) for w in s.get("words", [])]})
        scene_timing["scenes"].append({**slots[i], "number": i + 1, "cues": cues})
    (ROOT / "src_build" / "scene_timing.json").write_text(json.dumps(scene_timing, ensure_ascii=False, indent=1), encoding="utf-8")

    # ---------------- index.html
    slot_html, fx_html, js = [], [], []
    for i, sl in enumerate(slots):
        z = 10 + i
        hidden = "" if i == 0 else " opacity: 0;"
        slot_html.append(
            f'      <div\n        id="s{i + 1:02d}"\n        class="scene-slot"\n        style="z-index: {z};{hidden}"\n'
            f'        data-composition-id="{sl["id"]}"\n        data-composition-src="compositions/frames/{sl["id"]}.html"\n'
            f'        data-start="{sl["start"]}"\n        data-duration="{sl["duration"]}"\n        data-track-index="{1 + (i % 2)}"\n'
            f'        data-width="{W}"\n        data-height="{H}"\n      ></div>')
    for i in range(1, len(slots)):
        T = slots[i]["start"]
        kind = slots[i]["transition_in"]
        dt = TRANSITION[kind][0]
        old, new = f"#s{i:02d}", f"#s{i + 1:02d}"
        if kind in ("push", "pushlight"):
            js.append(f'      tl.to("{old}", {{ y: -{H}, duration: {dt}, ease: "power3.inOut" }}, {T});')
            js.append(f'      tl.fromTo("{new}", {{ y: {H}, opacity: 1 }}, {{ y: 0, opacity: 1, duration: {dt}, ease: "power3.inOut" }}, {T});')
        if kind in ("light", "pushlight"):
            fid = f"fx-light-{i + 1:02d}"
            fx_html.append(
                f'      <div\n        id="{fid}"\n        class="fx-slot"\n        style="z-index: {40 + i};"\n'
                f'        data-composition-id="fx-light"\n        data-composition-src="compositions/fx-light.html"\n'
                f'        data-start="{r3(T - 0.25)}"\n        data-duration="1.2"\n        data-track-index="4"\n'
                f'        data-width="{W}"\n        data-height="{H}"\n      ></div>')
            if kind == "light":
                # chỉ hòa mờ, không phóng 1.04: thanh tiêu đề giống hệt ở hai cảnh mới trùng khít (QA 10/10: tiêu đề in đúp)
                js.append(f'      tl.fromTo("{new}", {{ opacity: 0 }}, {{ opacity: 1, duration: {dt}, ease: "power2.out" }}, {T});')
        if kind == "expand":
            ex, ey, ew, eh = slots[i].get("expand_from") or [72, 600, 936, 600]
            ins = f"inset({ey}px {W - ex - ew}px {H - ey - eh}px {ex}px round 36px)"
            js.append(f'      tl.fromTo("{new}", {{ opacity: 1, clipPath: "{ins}" }}, {{ opacity: 1, clipPath: "inset(0px 0px 0px 0px round 0px)", duration: {dt}, ease: "power3.inOut" }}, {T});')
            js.append(f'      tl.to("{old}", {{ scale: 0.94, opacity: 0.55, duration: {dt}, ease: "power2.in" }}, {T});')
        if kind == "zoom":
            js.append(f'      tl.to("{old}", {{ scale: 1.45, opacity: 0, filter: "blur(10px)", duration: {dt}, ease: "power2.in" }}, {T});')
            js.append(f'      tl.fromTo("{new}", {{ scale: 1.22, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: {dt}, ease: "power3.out" }}, {T + 0.05:.3f});')
        if kind == "blur":
            js.append(f'      tl.to("{old}", {{ opacity: 0, filter: "blur(16px)", duration: {dt}, ease: "sine.inOut" }}, {T});')
            js.append(f'      tl.fromTo("{new}", {{ opacity: 0, filter: "blur(16px)" }}, {{ opacity: 1, filter: "blur(0px)", duration: {dt}, ease: "sine.inOut" }}, {T});')

    index = INDEX.replace("%%TOTAL%%", str(total)).replace("%%SLOTS%%", "\n".join(slot_html))
    index = index.replace("%%FX%%", "\n".join(fx_html)).replace("%%JS%%", "\n".join(js))
    (ROOT / "index.html").write_text(index, encoding="utf-8")
    (ROOT / "compositions" / "fx-light.html").write_text(FX_LIGHT, encoding="utf-8")
    # dấu thứ hai (dưới phụ đề) tắt khi vào khung kết, vì khung kết đã có chữ CAAITE lớn và logo vẽ ở vùng đó
    # mốc khung kết = hết câu cuối (cảnh 08 vào khung kết ngay sau "Bình luận cho trung tâm biết nhé"), trừ 0,1 s
    cuoi = sent[scenes[-1]["sentences"][-1]]
    end_mark2 = r3(cuoi["end"] + T0 - 0.1)
    wm = WATERMARK.replace("%%TOTAL%%", str(total)).replace("%%END_MARK2%%", str(end_mark2))
    (ROOT / "compositions" / "watermark.html").write_text(wm, encoding="utf-8")

    # ---------------- audio_plan.json
    sfx = []
    for i in range(1, len(slots)):
        kind = slots[i]["transition_in"]
        _, f, g, shift = TRANSITION[kind]
        if f:
            sfx.append({"t": r3(max(0.0, slots[i]["start"] + shift)), "file": f, "gain_db": g, "why": f"chuyển cảnh {kind} vào {slots[i]['id']}"})
    for i, sc in enumerate(scenes):
        for cue in sc.get("sfx", []):
            t = None
            want = cue["match"].strip().lower()
            for sid in sc["sentences"]:
                chs = sent[sid]["chunks"]
                for k, c in enumerate(chs):
                    if t is None and want and want in c["display"].lower():
                        t = c["start"] + T0
                for k in range(len(chs) - 1):  # chữ cần tìm vắt qua hai cụm liền nhau
                    if t is None and want and want in (chs[k]["display"] + " " + chs[k + 1]["display"]).lower():
                        t = chs[k]["start"] + T0
            if cue.get("at") is not None:
                t = slots[i]["start"] + float(cue["at"])
            # bám đúng một từ của lời đọc: {"sid": "B1S1", "w": 4} = đầu từ thứ 4 của bản đọc (cùng mốc với CUE.S.B1S1.w[4])
            if cue.get("w") is not None and sent[cue["sid"]].get("words"):
                t = sent[cue["sid"]]["words"][int(cue["w"])][0] + T0
            if t is None:
                print(f"CẢNH BÁO: không thấy '{cue['match']}' trong cảnh {sc['id']}")
                continue
            # mốc âm được phép (audio_engine.Track.add cắt đầu clip): dùng để bỏ phần lặng ở đầu tệp hiệu ứng
            item = {"t": r3(t + float(cue.get("shift", 0.0))), "file": cue["file"],
                    "gain_db": float(cue.get("gain_db", -22.0)), "trim": cue.get("trim"), "why": f"{sc['id']}: {cue.get('why_note') or cue['match']}"}
            if cue.get("fade_out") is not None:
                item["fade_out"] = float(cue["fade_out"])
            sfx.append(item)
    music_start = float(cfg.get("music_start", 0.0))
    if cfg.get("music_hit_source_s") is not None and cfg.get("music_hit_scene"):
        hit_scene = next(sl for sl in slots if sl["id"] == cfg["music_hit_scene"])
        hit_t = hit_scene["start"] + float(cfg.get("music_hit_local", 0.0))
        # bám mốc lời đọc: ngôi sao logo lóe ở (đầu cụm "và theo dõi trung tâm") + 1,1 s, như 09-cta.html (tK + 1,1)
        a = cfg.get("music_hit_anchor")
        if a and a.get("w") is not None and sent[a["sid"]].get("words"):  # {"sid", "w"}: đầu từ thứ w của bản đọc
            hit_t = sent[a["sid"]]["words"][int(a["w"])][0] + T0 + float(a.get("plus", 0.0))
        elif a:
            hit_t = sent[a["sid"]]["chunks"][int(a["chunk"])]["start"] + T0 + float(a.get("plus", 0.0))
        music_start = r3(max(0.0, float(cfg["music_hit_source_s"]) - hit_t))
        print(f"nhạc: bắt đầu từ {music_start:.3f} s của bản gốc để cú nhấn {cfg['music_hit_source_s']} s rơi vào {hit_t:.3f} s của phim")
    dips = []
    for d in cfg.get("music_dips", []):  # {"after": "B1S1"} hoặc {"before": "B7S1"}, "dur", "db"
        if d.get("after"):
            t_d = sent[d["after"]]["end"] + T0 + float(d.get("gap", 0.05))
        else:
            # tính từ TỪ ĐẦU TIÊN của câu, không từ mốc đầu câu (QA lượt 2: đầu câu B7S1 còn 0,3 s lặng nên nhạc trở lại
            # kèm một phách mạnh trước chữ "Nhưng")
            s_b = sent[d["before"]]
            t0_b = s_b["words"][0][0] if s_b.get("words") else s_b["start"]
            t_d = t0_b + T0 - float(d["dur"]) - float(d.get("gap", 0.05))
        dips.append({"t": r3(max(0.0, t_d)), "dur": float(d["dur"]), "db": float(d.get("db", -30.0)), "why": d.get("why", "")})
    plan = {"duration": total, "narration": "voice/narration.wav", "narration_offset": T0, "music_dips": dips,
            "music": cfg["music"], "music_start": music_start,
            "music_bed_lufs": float(cfg.get("music_bed_lufs", -23.0)), "duck_db": float(cfg.get("duck_db", -8.0)),
            "music_fade_in": float(cfg.get("music_fade_in", 0.08)), "music_fade_out": float(cfg.get("music_fade_out", 1.8)),
            "sfx": sorted(sfx, key=lambda x: x["t"]), "out": "assets/audio/reel-mix.wav"}
    (ROOT / "src_build" / "audio_plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"index.html: {len(slots)} cảnh, tổng {total:.3f} s; audio_plan: {len(sfx)} SFX")
    for sl in slots:
        print(f"  {sl['id']:<22} {sl['start']:7.3f} -> {sl['end']:7.3f}  ({sl['duration']:.3f} s, vào: {sl['transition_in']})")


INDEX = """<!doctype html>
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>CAAITE reel: Claude cài artifact thành ứng dụng</title>
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      html,
      body {
        margin: 0;
        overflow: hidden;
        background: #f9f9ff;
      }
      #main {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #f9f9ff;
      }
      #main > .scene-slot {
        position: absolute;
        inset: 0;
      }
      #el-captions {
        position: absolute;
        inset: 0;
        z-index: 80;
      }
      #main > .fx-slot {
        position: absolute;
        inset: 0;
        pointer-events: none;
      }
    </style>
  </head>
  <body>
    <!--
      Reel dọc bản tin Claude cài artifact thành ứng dụng (1080x1920, 30 fps). TỆP SINH TỰ ĐỘNG bởi src_build/build_index.py
      từ src_build/scenes.json và voice/narration_timing.json; sửa các tệp đó rồi chạy lại.
      Cảnh: compositions/frames/*.html. Phụ đề: compositions/captions.html. Âm thanh: assets/audio/reel-mix.wav.
    -->
    <div
      id="main"
      data-composition-id="main"
      data-start="0"
      data-duration="%%TOTAL%%"
      data-width="1080"
      data-height="1920"
    >
%%SLOTS%%

%%FX%%

      <div
        id="el-wm"
        style="z-index: 70;"
        data-composition-id="watermark"
        data-composition-src="compositions/watermark.html"
        data-start="0"
        data-duration="%%TOTAL%%"
        data-track-index="6"
        data-width="1080"
        data-height="1920"
      ></div>

      <div
        id="el-captions"
        data-composition-id="captions"
        data-composition-src="compositions/captions.html"
        data-track-kind="captions"
        data-start="0"
        data-duration="%%TOTAL%%"
        data-track-index="5"
        data-width="1080"
        data-height="1920"
      ></div>

      <audio
        id="reel-mix"
        src="assets/audio/reel-mix.wav"
        data-start="0"
        data-duration="%%TOTAL%%"
        data-track-index="10"
        data-volume="1"
      ></audio>
    </div>
    <script>
      // Chuyển cảnh trên timeline gốc; nội dung từng cảnh nằm trong timeline riêng của cảnh đó.
      const tl = gsap.timeline({ paused: true });
%%JS%%
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

FX_LIGHT = """<!doctype html>
<!--
  fx-light: vệt sáng chéo theo dải sáng của template CAAITE + quầng ngôi sao, dùng cho chuyển cảnh "light".
  TỆP SINH TỰ ĐỘNG bởi src_build/build_index.py. Dài 1,2 s; host đặt data-start = mốc cắt - 0,25 s.
-->
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <title>fx-light</title>
  </head>
  <body>
    <template>
      <style>
        #fxl-root {
          position: absolute;
          inset: 0;
          overflow: hidden;
          pointer-events: none;
        }
        #fxl-band {
          position: absolute;
          left: -420px;
          top: 420px;
          width: 2600px;
          height: 1460px;
          mix-blend-mode: screen;
          opacity: 0;
        }
        #fxl-bloom {
          position: absolute;
          left: 90px;
          top: 510px;
          width: 900px;
          height: 900px;
          mix-blend-mode: screen;
          opacity: 0;
        }
      </style>
      <div id="fxl-root" data-composition-id="fx-light" data-width="1080" data-height="1920" data-duration="1.2">
        <img id="fxl-band" src="assets/derived/light-band.png" alt="" />
        <img id="fxl-bloom" src="assets/derived/star-bloom-900.png" alt="" />
      </div>
      <script>
        (function () {
          var tl = gsap.timeline({ paused: true });
          tl.fromTo("#fxl-band", { x: -1400, y: 520, rotation: -28 }, { x: 900, y: -260, rotation: -28, duration: 1.0, ease: "power2.inOut" }, 0);
          tl.fromTo("#fxl-band", { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "power1.out", immediateRender: false }, 0);
          tl.to("#fxl-band", { opacity: 0, duration: 0.3, ease: "power1.in" }, 0.72);
          tl.fromTo("#fxl-bloom", { scale: 0.3, opacity: 0 }, { scale: 1.25, opacity: 0.9, duration: 0.28, ease: "power2.out" }, 0.2);
          tl.to("#fxl-bloom", { scale: 1.6, opacity: 0, duration: 0.45, ease: "power2.in" }, 0.5);
          window.__timelines["fx-light"] = tl;
        })();
      </script>
    </template>
  </body>
</html>
"""

WATERMARK = """<!doctype html>
<!--
  Watermark CAAITE suốt video (người dùng dặn 05/10/2026: gắn logo trung tâm để chống bị lấy video).
  TỆP SINH TỰ ĐỘNG bởi src_build/build_index.py. Viên tối mờ góc trên phải, cùng hàng nhãn trung tâm của các cảnh,
  nên đọc được trên cả nền lụa sáng lẫn nền gradient.
  Dấu thứ hai (QA 05/10): dòng chữ nhỏ "CAAITE · ptitai.org" ngay dưới vùng phụ đề, giữa khung. Cắt mép trên hay
  phóng to 10% để bỏ góc trên phải vẫn còn dấu này; muốn xóa phải che cả vùng phụ đề.
-->
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <title>watermark</title>
  </head>
  <body>
    <template>
      <style>
        @font-face { font-family: "Lexend"; src: url("assets/fonts/Lexend-Variable.ttf") format("truetype"); font-weight: 100 900; font-display: block; }
        #wm-root { position: absolute; inset: 0; overflow: hidden; pointer-events: none; }
        #wm-pill { position: absolute; right: 72px; top: 146px; height: 56px; display: flex; align-items: center; gap: 12px;
          padding: 0 20px 0 16px; border-radius: 999px; background: rgba(18, 20, 58, 0.58); border: 2px solid rgba(255, 255, 255, 0.5); }
        #wm-pill img { display: block; height: 34px; width: auto; }
        #wm-text { font-family: "Lexend", sans-serif; font-size: 24px; font-weight: 600; letter-spacing: 0.12em; margin-right: -0.12em; color: #ffffff; }
        /* dấu thứ hai: canh giữa khung như viên phụ đề, ngay dưới đáy viên phụ đề hai dòng (1446) */
        #wm-mark2 { position: absolute; left: 0; width: 1080px; top: 1478px; display: flex; justify-content: center; }
        #wm-mark2 span { font-family: "Lexend", sans-serif; font-size: 20px; font-weight: 600; letter-spacing: 0.14em; margin-right: -0.14em;
          text-transform: uppercase; color: #ffffff; padding: 6px 18px 7px; border-radius: 999px; background: rgba(18, 20, 58, 0.7); }
      </style>
      <div id="wm-root" data-composition-id="watermark" data-width="1080" data-height="1920" data-duration="%%TOTAL%%">
        <div id="wm-pill"><img src="assets/brand/caaite-logo-white.svg" alt="CAAITE" /><span id="wm-text">CAAITE</span></div>
        <div id="wm-mark2"><span>CAAITE · ptitai.org</span></div>
      </div>
      <script>
        (function () {
          var tl = gsap.timeline({ paused: true });
          tl.fromTo("#wm-pill", { opacity: 0.94 }, { opacity: 0.94, duration: %%TOTAL%%, ease: "none" }, 0);
          tl.fromTo("#wm-mark2", { opacity: 0.85 }, { opacity: 0.85, duration: %%END_MARK2%%, ease: "none" }, 0);
          tl.to("#wm-mark2", { opacity: 0, duration: 0.3, ease: "power1.out" }, %%END_MARK2%%);
          window.__timelines["watermark"] = tl;
        })();
      </script>
    </template>
  </body>
</html>
"""

if __name__ == "__main__":
    main()
