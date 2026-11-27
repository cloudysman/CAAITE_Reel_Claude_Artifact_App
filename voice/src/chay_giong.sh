#!/bin/bash
# Sinh lời cả bài rồi chấm và ghép, mẫu giọng A (@ainius.net), reel Claude cài artifact thành ứng dụng.
# 25/11/2026: L40S dùng chung (người khác chạy 100%), còn khoảng 12 GB trống; F5 cần khoảng 3 GB mỗi tiến trình,
# nên chạy hai tiến trình c3 song song (mỗi tiến trình một nhóm câu, tệp chọn riêng), rồi gộp lại trước khi ghép.
# Whisper và căn chỉnh chạy CPU. Claude và API chỉ tính đạt khi tai tiếng Anh nghe đúng (không có regex_vi).
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
nvidia-smi --query-gpu=memory.free --format=csv,noheader
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src OMP_NUM_THREADS=6 MKL_NUM_THREADS=6
mkdir -p work/tts
NHOM_A="B1S1,B2S1,B2S2,B3S1,B4S1,B5S1,B5S2"
NHOM_B="B5S3,B6S1,B6S2,B7S1,B7S2,B7S3,B8S1,B8S2"
$PY src/c3_sinh_loi.py --toc-do 5.0 --vong 3 --du 2 --chi "$NHOM_A" --chon work/tts/chon_a.json > work/giong_a.log 2>&1 &
$PY src/c3_sinh_loi.py --toc-do 5.0 --vong 3 --du 2 --chi "$NHOM_B" --chon work/tts/chon_b.json > work/giong_b.log 2>&1 &
wait
grep -ahE "^B[0-9]S[0-9]: |Traceback|Error" work/giong_a.log work/giong_b.log
$PY - <<'PYEOF'
import json
from pathlib import Path
thu_tu = [c["id"] for c in json.loads(Path("src/tts_lines.json").read_text(encoding="utf-8"))["cau"]]
gop = {}
for f in ("work/tts/chon_a.json", "work/tts/chon_b.json"):
    for r in json.loads(Path(f).read_text(encoding="utf-8")):
        gop[r["id"]] = r
thieu = [i for i in thu_tu if i not in gop]
Path("work/tts/chon.json").write_text(json.dumps([gop[i] for i in thu_tu if i in gop], ensure_ascii=False, indent=1), encoding="utf-8")
print("gộp chon.json:", len(gop), "câu; thiếu:", thieu)
PYEOF
echo "GIONG_XONG"
$PY src/dat_nghi.py
$PY src/c4_ghep.py 2>&1 | grep -vE "Warning|warn" | cut -c1-260 | tail -24
echo "GHEP_XONG"
