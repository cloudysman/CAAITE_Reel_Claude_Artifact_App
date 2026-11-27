#!/bin/bash
# Sinh lại B7S2, B7S3 sau khi đổi lời (QA bản dựng 2, 25/11/2026): B7S2 bỏ chữ "bạn" (whisper nghe "xin bạn" thành "sinh bản"),
# B7S3 thêm "mà" ("bạn tin" bị nghe "bản tin"). Kết quả vào work/tts/chon_h.json; ghep_cuoi.sh gộp tệp này sau chon_tay.
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
nvidia-smi --query-gpu=memory.free --format=csv,noheader
export WHISPER_CPU=1 MMS_DEVICE=cpu PYTHONPATH=$PROJ/voice/lab/src OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
$PY src/c3_sinh_loi.py --toc-do 5.0 --vong 3 --du 2 --seed-tu 1700 --chi "B7S2,B7S3" --chon work/tts/chon_h.json > work/giong_h2.log 2>&1
grep -ahE "^B[0-9]S[0-9]: |Traceback|Error" work/giong_h2.log
echo "SINH_B7_XONG"
