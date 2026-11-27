#!/bin/bash
# Sinh lại câu B6S2 sau khi đổi lời (Claude chuyển xuống cuối câu: ở bản cũ "dùng Claude đều" 18/18 bản bị tai
# tiếng Anh nghe "Cloud"). Chờ nhóm câu B của chay_giong.sh chạy xong để GPU dùng chung còn đủ chỗ (cần khoảng 3 GB
# + 1 GB dư), rồi sinh B6S2, gộp ba tệp chọn (a, b, c; c đè b ở câu B6S2) và ghép lại cả bài.
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
while pgrep -f "chon_b.json" > /dev/null; do sleep 20; done
nvidia-smi --query-gpu=memory.free --format=csv,noheader
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$PY src/c3_sinh_loi.py --toc-do 5.0 --vong 3 --du 2 --seed-tu 300 --lines src/tts_lines_b6s2.json --chon work/tts/chon_c.json > work/giong_c.log 2>&1
grep -ahE "^B[0-9]S[0-9]: |Traceback|Error" work/giong_c.log
while pgrep -f "chon_a.json" > /dev/null; do sleep 20; done
$PY - <<'PYEOF'
import json
from pathlib import Path
thu_tu = [c["id"] for c in json.loads(Path("src/tts_lines.json").read_text(encoding="utf-8"))["cau"]]
gop = {}
for f in ("work/tts/chon_a.json", "work/tts/chon_b.json", "work/tts/chon_c.json"):
    p = Path(f)
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8")):
            gop[r["id"]] = r
thieu = [i for i in thu_tu if i not in gop]
Path("work/tts/chon.json").write_text(json.dumps([gop[i] for i in thu_tu if i in gop], ensure_ascii=False, indent=1), encoding="utf-8")
print("gộp chon.json:", len(gop), "câu; thiếu:", thieu, "; chưa đạt:", [i for i in thu_tu if i in gop and not gop[i]["dat"]])
PYEOF
echo "GIONG_XONG"
$PY src/dat_nghi.py
$PY src/c4_ghep.py 2>&1 | grep -vE "Warning|warn" | cut -c1-260 | tail -24
echo "GHEP_XONG"
