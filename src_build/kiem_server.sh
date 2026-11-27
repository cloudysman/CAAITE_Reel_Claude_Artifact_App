#!/bin/bash
# Chạy trên server: lint, check, chụp khung ở các mốc cho trước, gói ảnh để kéo về.
# Cách dùng: bash kiem_server.sh "0.6,2.2,3.6,..."
cd ~/HieuDT/claude_app_reel/project || exit 1
. ~/.nvm/nvm.sh >/dev/null
export HYPERFRAMES_BROWSER_PATH=/home/hieudt/.cache/hyperframes/chrome/chrome-headless-shell/linux-152.0.7977.30/chrome-headless-shell-linux64/chrome-headless-shell
timeout 600 npx --yes hyperframes@0.8.101 lint 2>&1 | tail -30
timeout 900 npx --yes hyperframes@0.8.101 check > check_full.log 2>&1; grep -E "error|warning|Check|WCAG|need 4.5" check_full.log | head -60
rm -rf snapshots
timeout 900 npx --yes hyperframes@0.8.101 snapshot --at "$1" 2>&1 | tail -4
ls snapshots | head -60
tar -cf ../work/snap.tar snapshots
echo "KIEM_XONG"
