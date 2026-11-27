#!/bin/bash
# Lượt 2: sinh lại B1S2, B2S1, B4S2, B6S1, B8S2 (độ giống giọng thấp hoặc "Thâm quyền"), chọn bản giống giọng nhất, gộp, ghép lại.
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
rm -f work/tts/chon_c.json
$PY src/c3_sinh_loi.py --chi B1S2,B2S1,B4S2,B6S1,B8S2 --toc-do 5.0 --vong 1 --du 5 --seed-tu 300 --chon work/tts/chon_c.json 2>&1 | grep -aE "^  B|^B[0-9]S[0-9]: |Traceback|Error"
$PY src/chon_theo_giong.py
$PY src/ghep_lai.py
$PY src/c4_ghep.py 2>&1 | grep -vE "Warning|warn" | cut -c1-260 | tail -18
echo "GHEP_XONG"
