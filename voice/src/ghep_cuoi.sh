#!/bin/bash
# Gộp tệp chọn của các lượt sinh (a, b: chay_giong.sh; d: câu B6S2 viết lại "mỗi lượt Claude làm việc cho nó";
# chon_tay: bản chọn tay chấm lại bằng src/cham_tep.py (whisper nghe đúng chữ "tệp");
# f: câu B5S1 viết lại không có chữ Claude ("dùng được Claude và/cùng" bị nghe "Cloud" 9/9 bản); g: câu B5S2)
# rồi đặt khoảng nghỉ và ghép cả bài. src/tts_lines.json phải đã mang lời mới của B5S1, B6S2.
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src OMP_NUM_THREADS=12 MKL_NUM_THREADS=12
$PY - <<'PYEOF'
import json
from pathlib import Path
lines = json.loads(Path("src/tts_lines.json").read_text(encoding="utf-8"))
thu_tu = [c["id"] for c in lines["cau"]]
gop = {}
for f in ("work/tts/chon_a.json", "work/tts/chon_b.json", "work/tts/chon_d.json", "work/tts/chon_f.json", "work/tts/chon_g.json", "work/tts/chon_tay.json", "work/tts/chon_h.json"):
    p = Path(f)
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            gop[r["id"]] = r
b6 = [c for c in lines["cau"] if c["id"] == "B6S2"][0]
print("B6S2 trong tts_lines:", b6["tts"])
thieu = [i for i in thu_tu if i not in gop]
Path("work/tts/chon.json").write_text(json.dumps([gop[i] for i in thu_tu if i in gop], ensure_ascii=False, indent=1), encoding="utf-8")
print("gộp chon.json:", len(gop), "câu; thiếu:", thieu, "; chưa đạt:", [i for i in thu_tu if i in gop and not gop[i]["dat"]])
PYEOF
$PY src/dat_nghi.py
$PY src/c4_ghep.py 2>&1 | grep -vE "Warning|warn" | cut -c1-260 | tail -24
echo "GHEP_XONG"
