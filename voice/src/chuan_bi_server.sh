#!/bin/bash
# Đo cách đọc tên tiếng Anh của reel Claude cài artifact thành ứng dụng, mẫu giọng A (@ainius.net),
# trong đúng câu sẽ đọc, mỗi cách viết 2 seed, chỉ nghe đoạn tên bằng tai tiếng Anh (BO_VI=1).
# 25/11/2026: GPU L40S dùng chung còn khoảng 8,7 GB trống (người khác dùng 100%), F5 cần khoảng 3 GB nên vẫn chạy GPU;
# whisper và căn chỉnh chạy CPU.
B=~/HieuDT/claude_app_reel
cd $B || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
$PY - <<'PYEOF'
from pathlib import Path
p = Path("src/c2_giong_mau.py")
s = p.read_text(encoding="utf-8")
moi = '"artifact": 3, "enterprise": 3, "menu": 2, "link": 1, "claud": 1, '
if '"artifact": 3' not in s:
    s = s.replace("AM_TIET_ANH = {", "AM_TIET_ANH = {" + moi, 1)
    p.write_text(s, encoding="utf-8")
print([l for l in s.splitlines() if l.startswith("AM_TIET_ANH")][0][:120])
PYEOF
nvidia-smi --query-gpu=memory.free --format=csv,noheader
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src BO_VI=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$PY src/c2_giong_mau.py --chi-phan-2 A --tu src/tu_vong1.json --seeds 11,22 --ten tu_v1
echo "CB_XONG $?"
