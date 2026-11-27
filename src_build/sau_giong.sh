#!/bin/bash
# Sau khi server ghép xong lời đọc: kéo về, dựng lại index, mốc cảnh, phụ đề, bản trộn âm thanh.
# Cách dùng (Git Bash): bash src_build/sau_giong.sh   (SSH bằng khóa tới hieudt@171.226.10.153)
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
for f in narration.wav narration_timing.json narration_metrics.json; do
  scp -o BatchMode=yes -q "hieudt@171.226.10.153:HieuDT/claude_app_reel/work/$f" "voice/$f"
done
OFF=$(python -I -X utf8 -c "import json;print(json.load(open('src_build/scenes.json',encoding='utf-8'))['narration_offset'])")
python -I -X utf8 src_build/build_index.py
python -I -X utf8 src_build/tao_canh.py > /dev/null  # mốc media-start ở cảnh 05 lấy từ scene_timing.json vừa ghi
python -I -X utf8 src_build/fill_cues.py
python -I -X utf8 src_build/build_captions.py --offset "$OFF"
mkdir -p assets/audio
python -I -X utf8 src_build/mix_reel.py --plan src_build/audio_plan.json
