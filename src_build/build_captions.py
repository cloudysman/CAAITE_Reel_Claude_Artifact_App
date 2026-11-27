"""Sinh compositions/captions.html (phụ đề chạy theo cụm chữ) từ voice/narration_timing.json.

Cách dùng:  python src_build/build_captions.py [--timing voice/narration_timing.json] [--offset 0.0]

- Mỗi câu trong tệp mốc thời gian có danh sách "chunks" (cụm 1-3 từ hiển thị, có start/end tính theo giây
  của narration.wav). Bộ dựng gom các cụm thành nhóm phụ đề (tối đa ~24 ký tự, một dòng), không gom qua
  ranh giới câu, ngắt khi khoảng lặng giữa hai cụm vượt 0,15 s.
- Cụm đang được đọc sáng lên (karaoke); cụm có số hoặc tên mô hình được tô màu mint.
- --offset: độ lệch (giây) giữa đầu video và đầu narration.wav, cộng vào mọi mốc.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]

MAX_CHARS = 24          # một dòng ở cỡ 60px trong bề rộng 858px
MAX_WORDS = 5
GAP_BREAK = 0.15        # khoảng lặng giữa hai cụm thì tách nhóm
LEAD_IN = 0.06          # nhóm hiện sớm hơn cụm đầu một chút
TAIL = 0.28             # giữ nhóm sau cụm cuối nếu nhóm sau chưa tới
BRIDGE = 0.6            # khe giữa hai nhóm ngắn hơn mức này thì nối liền (phụ đề chạy liên tục)

# cụm từ không được tách khi phụ đề xuống dòng (text-wrap: balance có thể chia "mô hình" thành "mô / hình")
NO_BREAK = ["ứng dụng", "máy tính", "ý tưởng", "biểu tượng", "cửa sổ", "đóng gói", "ký số", "khóa API", "tài khoản", "kết nối",
            "thông báo", "thanh menu", "cập nhật", "đường link", "kỹ sư", "sửa ảnh", "quản lý tệp", "bản đồ", "cơ thể người", "mặc định",
            "trình duyệt", "chương trình", "toàn quyền", "thử nghiệm", "chủ sở hữu", "hạn mức", "sử dụng", "trung tâm", "bình luận", "công cụ"]

# từ khóa được tô màu BÊN TRONG viên (không tô cả viên): số kèm đơn vị và CAAITE.
EMPHASIS = re.compile(
    r"(?<![\w.-])\d+(?:[.,]\d+)*\s?(?:%|GB|tỉ|lượt|đô|điểm)?(?![\w-])|CAAITE",
)

# ngắt dòng cố định cho viên hai dòng ('|' = xuống dòng), để text-wrap: balance không tách đôi cụm
# (QA bản dựng 2: "dùng / được", "không / duyệt", "tính / cả" bị tách; dòng dài nhất 685 px ở Lexend 600 cỡ 54, viên chứa 716 px)
LINE_BREAKS: dict[str, str] = {
    "rồi chọn mục cài thành ứng dụng.": "rồi chọn mục|cài thành ứng dụng.",
    "Cài xong, ứng dụng có biểu tượng": "Cài xong,|ứng dụng có biểu tượng",
    "Ứng dụng dùng được các dịch vụ": "Ứng dụng dùng được|các dịch vụ",
    "bạn đã kết nối như lịch, email.": "bạn đã kết nối|như lịch, email.",
    "hiện trên thanh menu hay khay hệ thống.": "hiện trên thanh menu|hay khay hệ thống.",
    "Hạn mức sử dụng tính cả lúc làm ứng dụng": "Hạn mức sử dụng|tính cả lúc làm ứng dụng",
    "Vì Anthropic không duyệt ứng dụng": "Vì Anthropic|không duyệt ứng dụng",
    "Bạn bảo Claude bản máy tính": "Bạn bảo|Claude bản máy tính",
    "Bình luận cho trung tâm biết nhé.": "Bình luận|cho trung tâm biết nhé.",
}

# cụm lời đọc quá dài cho một viên hai dòng: tách thành nhiều viên, mốc từng viên lấy từ mốc từ ("words");
# số đi kèm là số từ của bản đọc (tts, sau khi thay cách đọc: 'ây pi ai' 3 từ, 'mác ô ét' 3 từ); chạy script/build_tts_lines.py trước để kiểm số từ
CAP_SPLIT: dict[str, list] = {}

# viên ngắn cố ý đứng riêng, không gộp với viên sau
KHONG_GOP: set[str] = set()

# câu không hiện phụ đề vì trên hình đã in đủ ý của câu đó cỡ lớn (cảnh 08: câu hỏi cho người xem;
# cảnh 04: ba việc bị gạch đúng chữ và thẻ tài khoản Claude, QA bản dựng 2; cảnh 06: viên bản thử nghiệm, triển khai dần;
# cảnh 07: thẻ mức 1 "Chỉ làm được như khi chạy trong trình duyệt", soát bản dựng 3)
AN_CAU: set[str] = {"B8S1", "B4S1", "B6S1", "B7S1"}


def mau(text: str) -> str:
    """text đã escape; bọc từ khóa trong span.em rồi giữ các cụm không được tách."""
    return no_break(EMPHASIS.sub(lambda m: f'<span class="em">{m.group(0)}</span>', text))


def chu_vien(t: str) -> str:
    phan = LINE_BREAKS.get(t, t).split("|")
    return "<br>".join(mau(html.escape(x)) for x in phan)


def load_chunks(timing_path: Path, offset: float):
    data = json.loads(timing_path.read_text(encoding="utf-8"))
    lines = json.loads((ROOT / "voice" / "src" / "tts_lines.json").read_text(encoding="utf-8"))
    so_tu = {c["id"]: [len(re.sub(r"[^\w\s]", " ", ch["tts"]).split()) for ch in c["chunks"]] for c in lines["cau"]}
    sentences = []
    for s in data["sentences"]:
        if s["id"] in AN_CAU:
            continue
        chunks = []
        for k, c in enumerate(s["chunks"]):
            text = c["display"].strip()
            if not text:
                continue
            if text in CAP_SPLIT:
                words = s["words"]
                i = sum(so_tu[s["id"]][:k])
                assert sum(n for _, n in CAP_SPLIT[text]) == so_tu[s["id"]][k], f"CAP_SPLIT lệch số từ: {text}"
                for phan, n in CAP_SPLIT[text]:
                    chunks.append({"text": phan, "start": round(words[i][0] + offset, 3), "end": round(words[i + n - 1][1] + offset, 3)})
                    i += n
                continue
            chunks.append({"text": text, "start": round(c["start"] + offset, 3), "end": round(c["end"] + offset, 3)})
        if chunks:
            sentences.append({"id": s["id"], "chunks": chunks})
    return data.get("duration", 0.0) + offset, sentences


def group_sentence(chunks):
    groups, cur = [], []
    for i, c in enumerate(chunks):
        if cur:
            text_len = len(" ".join(x["text"] for x in cur + [c]))
            words = sum(len(x["text"].split()) for x in cur + [c])
            gap = c["start"] - cur[-1]["end"]
            if text_len > MAX_CHARS or words > MAX_WORDS or gap > GAP_BREAK:
                groups.append(cur)
                cur = []
        cur.append(c)
    if cur:
        groups.append(cur)
    # tránh nhóm cuối chỉ có một từ ngắn: gộp ngược nếu vẫn vừa một dòng
    if len(groups) >= 2 and len(" ".join(x["text"] for x in groups[-1])) <= 6:
        merged = groups[-2] + groups[-1]
        if len(" ".join(x["text"] for x in merged)) <= MAX_CHARS + 6:
            groups[-2:] = [merged]
    # nhóm ngắn (≤ 3 từ) giữa câu chỉ nháy qua chưa tới 1 s ("Bình luận nhé,"): gộp với nhóm sau nếu vẫn vừa hai dòng
    i = 0
    while i < len(groups) - 1:
        a = " ".join(x["text"] for x in groups[i])
        b = " ".join(x["text"] for x in groups[i + 1])
        if a not in KHONG_GOP and len(a.split()) <= 3 and len(a + " " + b) <= 2 * MAX_CHARS - 8:
            groups[i:i + 2] = [groups[i] + groups[i + 1]]
        else:
            i += 1
    return groups


def no_break(text: str) -> str:
    for phrase in NO_BREAK:
        text = text.replace(phrase, f'<span class="nb">{phrase}</span>')
    return text


def build(timing_path: Path, offset: float, out_path: Path):
    duration, sentences = load_chunks(timing_path, offset)
    groups = []
    for s in sentences:
        for g in group_sentence(s["chunks"]):
            groups.append(g)
    # mốc nhóm: bắt đầu sớm LEAD_IN, kết thúc ở min(cụm cuối + TAIL, nhóm sau - 0.02)
    plan = []
    for i, g in enumerate(groups):
        start = max(0.0, g[0]["start"] - LEAD_IN)
        end = g[-1]["end"] + TAIL
        if i + 1 < len(groups):
            # nhóm sau hiện đúng lúc nhóm trước tắt hẳn: không bao giờ có hai viên phụ đề cùng lúc
            nxt = max(0.0, groups[i + 1][0]["start"] - LEAD_IN)
            # khe ngắn giữa hai nhóm (nghỉ dấu phẩy, nghỉ giữa câu < BRIDGE): giữ nhóm trước tới lúc nhóm sau hiện,
            # để phụ đề chạy liên tục, không nháy tắt 1-2 khung (snapshot 09/10: khe 0,02-0,54 s)
            end = nxt if nxt - end < BRIDGE else max(start + 0.25, min(end, nxt))
        plan.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "words": [{"t": c["text"], "s": c["start"], "e": c["end"], "em": bool(EMPHASIS.search(c["text"]))} for c in g],
        })

    groups_html = []
    for gi, g in enumerate(plan):
        spans = "".join(
            f'<span class="cw" id="captions-w{gi}-{wi}">{chu_vien(w["t"])}</span>'
            for wi, w in enumerate(g["words"])
        )
        groups_html.append(f'<div class="cg" id="captions-g{gi}"><div class="cg-pill">{spans}</div></div>')

    data_json = json.dumps(plan, ensure_ascii=False)
    total = max(duration, plan[-1]["end"] if plan else 0.0)
    page = TEMPLATE.replace("%%GROUPS%%", "\n        ".join(groups_html)).replace("%%DATA%%", data_json)
    page = page.replace("%%DURATION%%", f"{total:.3f}")
    out_path.write_text(page, encoding="utf-8")
    print(f"captions: {len(plan)} nhóm, {sum(len(g['words']) for g in plan)} cụm, kết thúc {total:.2f} s -> {out_path}")


TEMPLATE = r"""<!doctype html>
<!--
  captions: phụ đề chạy theo cụm chữ cho reel bản tin Claude cài artifact thành ứng dụng. TỆP SINH TỰ ĐỘNG bởi src_build/build_captions.py
  từ voice/narration_timing.json; sửa bộ dựng rồi chạy lại, đừng sửa tay.
  Vùng phụ đề: viên canh giữa, rộng tối đa 780 px (x 150-930, chừa cột nút của nền tảng ở mép phải), đỉnh 1268 px.
-->
<html lang="vi">
  <head>
    <meta charset="UTF-8" />
    <title>captions</title>
  </head>
  <body>
    <template>
      <style>
        @font-face {
          font-family: "Lexend";
          src: url("assets/fonts/Lexend-Variable.ttf") format("truetype");
          font-weight: 100 900;
          font-style: normal;
          font-display: block;
        }
        #captions-root {
          position: absolute;
          inset: 0;
          pointer-events: none;
          font-family: "Lexend", sans-serif;
        }
        #captions-root .cg {
          position: absolute;
          left: 0;
          width: 1080px;
          top: 1268px;
          height: 180px;
          display: flex;
          align-items: flex-start;
          justify-content: center;
          opacity: 0;
          overflow: visible;
        }
        #captions-root .cg-pill {
          display: block;
          max-width: 780px;
          box-sizing: border-box;
          padding: 14px 30px 18px;
          border-radius: 30px;
          background: rgba(24, 27, 102, 0.9);
          border: 2px solid rgba(255, 255, 255, 0.28);
          box-shadow: 0 18px 40px rgba(18, 20, 58, 0.28);
          text-align: center;
          line-height: 1.22;
          text-wrap: balance;
        }
        #captions-root .cw {
          display: inline-block;
          margin: 0 0.2em;
          font-size: 54px;
          font-weight: 600;
          letter-spacing: -0.005em;
          color: #ffffff;
          opacity: 0.58;
          transform-origin: 50% 70%;
          /* cụm dài hơn một dòng tự xuống dòng bên trong viên: chia hai dòng đều nhau, không để một chữ mồ côi */
          text-wrap: balance;
        }
        #captions-root .nb {
          white-space: nowrap;
        }
        /* màu nhấn chữ số trong phụ đề (trên nền xanh đậm), giữ như các reel trước */
        #captions-root .cw .em {
          color: #ffd98a;
        }
      </style>

      <div id="captions-root" data-composition-id="captions" data-width="1080" data-height="1920" data-duration="%%DURATION%%">
        %%GROUPS%%
      </div>

      <script>
        (function () {
          // Chỉ dùng chuỗi bộ chọn (GSAP tự tìm phần tử lúc tween chạy): khi script của composition con
          // chạy, các phần tử có thể chưa gắn vào trang nên getElementById trả về null.
          var PLAN = %%DATA%%;
          var tl = gsap.timeline({ paused: true });
          PLAN.forEach(function (g, gi) {
            var el = "#captions-g" + gi;
            tl.fromTo(el, { opacity: 0, y: 26 }, { opacity: 1, y: 0, duration: 0.16, ease: "power3.out", immediateRender: false }, g.start);
            g.words.forEach(function (w, wi) {
              var span = "#captions-w" + gi + "-" + wi;
              var on = Math.max(g.start, w.s - 0.03);
              tl.fromTo(span, { opacity: 0.58, scale: 1 }, { opacity: 1, scale: w.em ? 1.05 : 1.03, duration: 0.12, ease: "power2.out", immediateRender: false }, on);
              tl.to(span, { scale: 1, duration: 0.18, ease: "power2.inOut" }, on + 0.12);
            });
            var fadeAt = Math.max(g.start + 0.2, g.end - 0.1);
            tl.to(el, { opacity: 0, y: -10, duration: 0.1, ease: "power2.in" }, fadeAt);
            tl.set(el, { opacity: 0, visibility: "hidden" }, g.end);
          });
          window.__timelines["captions"] = tl;
        })();
      </script>
    </template>
  </body>
</html>
"""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    real = ROOT / "voice" / "narration_timing.json"
    ap.add_argument("--timing", default=str(real if real.exists() else ROOT / "voice" / "narration_timing_est.json"))
    ap.add_argument("--offset", type=float, default=0.0)
    ap.add_argument("--out", default=str(ROOT / "compositions" / "captions.html"))
    a = ap.parse_args()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    build(Path(a.timing), a.offset, Path(a.out))
