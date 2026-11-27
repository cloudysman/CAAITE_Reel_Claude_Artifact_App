#!/bin/bash
# Server: mã hóa bản đăng từ bản render HyperFrames + bản trộn WAV, rồi đo thông số và tách khung kiểm tra.
# Cách dùng (trên server): bash ma_hoa_ban_dang.sh <bản render .mp4> "<mốc khung khóa, cách nhau bởi dấu phẩy>"
set -e
cd ~/HieuDT/claude_app_reel/project
RENDER="$1"
KEYS="$2"
F=renders/CAAITE-reel-Claude-artifact-app.mp4
cp -f "$RENDER" renders/CAAITE-reel-Claude-artifact-app.render.mp4
DUR=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 renders/CAAITE-reel-Claude-artifact-app.render.mp4)
ffmpeg -v error -y -i renders/CAAITE-reel-Claude-artifact-app.render.mp4 -i assets/audio/reel-mix.wav -map 0:v:0 -map 1:a:0 \
  -c:v libx264 -preset slow -crf 18 -profile:v high -level 4.2 -pix_fmt yuv420p \
  -x264-params keyint=600:min-keyint=1:scenecut=0 -force_key_frames "$KEYS" \
  -c:a aac -b:a 192k -ar 48000 -af apad -t "$DUR" -movflags +faststart -threads 8 "$F"
mkdir -p ../work/final
O=../work/final/thong_so.txt
{
  echo "# Thông số bản đăng $F"
  echo "(mã hóa lại từ renders/CAAITE-reel-Claude-artifact-app.render.mp4, tiếng lấy thẳng từ assets/audio/reel-mix.wav)"
  echo
  echo "## ffprobe"
  ffprobe -v error -show_entries format=duration,size,bit_rate,format_name -show_entries stream=index,codec_name,profile,level,width,height,pix_fmt,r_frame_rate,avg_frame_rate,nb_frames,sample_rate,channels,channel_layout,bit_rate,duration -of default=nw=0 "$F"
  echo
  echo "## moov đặt đầu tệp (faststart)"
  python3 -c "d=open('$F','rb').read(1<<20); i=d.find(b'moov'); j=d.find(b'mdat'); print('moov ở byte', i, '| mdat ở byte', j, '| faststart:', 0 <= i < j)"
  echo
  echo "## Khung khóa (giây, theo cờ K của gói hình)"
  ffprobe -v error -select_streams v:0 -show_entries packet=pts_time,flags -of csv=p=0 "$F" | awk -F, '$2 ~ /K/ {printf "%s ", $1}'
  echo
  echo "(mốc bắt đầu cảnh trong scene_timing.json: $KEYS; khung khóa rơi vào khung hình gần nhất ở 30 fps)"
  echo
  echo "## Độ to EBU R128 (ffmpeg ebur128, peak=true)"
  ffmpeg -nostats -i "$F" -vn -af ebur128=peak=true -f null - 2>&1 | sed -n '/Summary:/,$p'
} > "$O" 2>&1
for t in 0.0 10.5 22.5 50.0; do ffmpeg -v error -y -ss $t -i "$F" -frames:v 1 -q:v 3 ../work/final/khung_$t.jpg; done
cat "$O"
ls -la renders ../work/final
