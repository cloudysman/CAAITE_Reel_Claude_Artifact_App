"""Điền mốc thời gian vào các cảnh từ src_build/scene_timing.json (chạy sau build_index.py, trước lint/render).

Trong mỗi compositions/frames/<cảnh>.html:
- đoạn giữa /*CUE*/ và /*END_CUE*/ được thay bằng JSON: {"D": thời lượng cảnh, "S": {mã câu: {"t0", "t1", "c": [mốc đầu
  từng cụm], "e": [mốc cuối từng cụm], "w": [mốc đầu từng từ của bản đọc tts]}}} (giờ cục bộ của cảnh, giây);
- thẻ nào có thuộc tính data-fill-d thì data-duration được đặt bằng D (gốc #root và lớp nền suốt cảnh).
Nhờ vậy cảnh viết một lần, đổi giọng (mốc mới) chỉ cần chạy lại build_index.py rồi tệp này.
Cách dùng: python src_build/fill_cues.py [mã cảnh ...]
"""
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    st = json.loads((ROOT / "src_build" / "scene_timing.json").read_text(encoding="utf-8"))
    chi = set(sys.argv[1:])  # tùy chọn: chỉ điền cho các cảnh được nêu, ví dụ 01-hook 02-news
    for sc in st["scenes"]:
        if chi and sc["id"] not in chi:
            continue
        p = ROOT / "compositions" / "frames" / f"{sc['id']}.html"
        if not p.exists():
            print(f"(chưa có) {p.name}")
            continue
        D = round(sc["duration"], 3)
        cue = {"D": D, "S": {}}
        for c in sc["cues"]:
            cue["S"][c["sentence"]] = {"t0": c["local_start"], "t1": c["local_end"],
                                       "c": [ch["local"] for ch in c["chunks"]], "e": [ch["local_end"] for ch in c["chunks"]],
                                       "w": c.get("words", [])}
        t = p.read_text(encoding="utf-8")
        n_cue = len(re.findall(r"/\*CUE\*/.*?/\*END_CUE\*/", t, flags=re.S))
        t = re.sub(r"/\*CUE\*/.*?/\*END_CUE\*/", "/*CUE*/" + json.dumps(cue, ensure_ascii=False) + "/*END_CUE*/", t,
                   flags=re.S)

        def dat_d(m: re.Match) -> str:
            tag = m.group(0)
            return re.sub(r'data-duration="[^"]*"', f'data-duration="{D}"', tag)

        t, n_d = re.subn(r"<[^<>]*data-fill-d[^<>]*>", dat_d, t)
        p.write_text(t, encoding="utf-8")
        print(f"{p.name}: D={D}, CUE {n_cue}, data-duration {n_d}")


if __name__ == "__main__":
    main()
