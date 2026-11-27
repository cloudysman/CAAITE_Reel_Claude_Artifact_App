"""Gộp lượt sinh lại (work/tts/chon_c.json) vào work/tts/chon.json: thay hẳn mục của câu đó."""
import json
from pathlib import Path

T = Path("work/tts")
d = {g["id"]: g for g in json.loads((T / "chon.json").read_text(encoding="utf-8"))}
for g in json.loads((T / "chon_c.json").read_text(encoding="utf-8")):
    print(g["id"], "thay bằng", g["chon"]["tep"], "CER", g["chon"]["cer"], "giống", g["chon"]["giong"])
    d[g["id"]] = g
thu = [c["id"] for c in json.loads(Path("src/tts_lines.json").read_text(encoding="utf-8"))["cau"]]
(T / "chon.json").write_text(json.dumps([d[i] for i in thu], ensure_ascii=False, indent=1), encoding="utf-8")
