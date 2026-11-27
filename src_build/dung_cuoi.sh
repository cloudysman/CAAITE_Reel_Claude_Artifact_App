#!/bin/bash
# Chạy trên server: render một luồng, mã hóa bản đăng, cho whisper nghe tệp cuối.
cd ~/HieuDT/claude_app_reel/project || exit 1
mkdir -p renders
. ~/.nvm/nvm.sh >/dev/null
export HYPERFRAMES_BROWSER_PATH=/home/hieudt/.cache/hyperframes/chrome/chrome-headless-shell/linux-152.0.7977.30/chrome-headless-shell-linux64/chrome-headless-shell
timeout 900 npx --yes hyperframes@0.8.101 check 2>&1 | grep -E "Check passed|Check failed|WCAG|need 4.5|error\(s\)" | cut -c1-130
timeout 1800 npx --yes hyperframes@0.8.101 render . --workers 1 --quality high -o "./renders/ban2.mp4" > renders/ban2.log 2>&1
echo "RENDER $?"
bash ../work/ma_hoa_ban_dang.sh renders/ban2.mp4 "$1" > ../work/ma_hoa.log 2>&1
echo "MA_HOA $?"
cd ~/HieuDT/claude_app_reel || exit 1
source ~/HieuDT/gpt61_reel/voice/lab/src/env.sh
ffmpeg -v error -y -i project/renders/CAAITE-reel-Claude-artifact-app.mp4 -vn -ac 1 -ar 16000 work/tu_tep_cuoi.wav
$PY work/nghe_cuoi.py 2>&1 | grep -v Warning | cut -c1-900
echo "CUOI_XONG"
