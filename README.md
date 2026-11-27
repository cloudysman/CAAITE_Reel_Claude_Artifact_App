# Reel bản tin: Claude cài artifact thành ứng dụng trên máy tính

Reel dọc 1080x1920, 30 khung hình/giây, dưới 60 giây, cho kênh của Trung tâm Đào tạo AI Chuyên sâu (CAAITE), Khoa Trí tuệ nhân tạo, PTIT. Làm từ bài của EZAI người dùng dán ngày 25/11/2026, đối chiếu với bài của Anthropic trên claude.com (24/11/2026), chuỗi bài và video demo của @ClaudeDevs trên X, và trang demo của Felix, kỹ sư Anthropic.

Reel nói năm ý:
1. Từ một lời nhắn, Claude làm ra ứng dụng (ví dụ trong video demo: theo dõi rác vũ trụ) rồi cài lên máy tính chạy macOS hoặc Windows bằng mục Install as app; ứng dụng có biểu tượng và cửa sổ riêng.
2. Ví dụ thật: kỹ sư Anthropic làm thử trình sửa ảnh, trình quản lý tệp, bản đồ cơ thể người (không phải sản phẩm chính thức).
3. Không phải đóng gói, ký số hay tạo khóa API; ứng dụng dùng Claude, dịch vụ đã kết nối, gửi thông báo, hiện trên thanh menu hay khay hệ thống nếu được phép; tự cập nhật, chia sẻ bằng link.
4. Bản thử nghiệm, triển khai dần cho mọi gói; lúc làm ứng dụng và mỗi lượt Claude làm việc cho ứng dụng đều tính vào hạn mức.
5. Ba mức quyền; Anthropic không duyệt ứng dụng trước khi cài, nên chỉ cấp toàn quyền cho ứng dụng bạn tin.

## Tệp chính

| Tệp | Nội dung |
|---|---|
| `CAAITE-reel-Claude-artifact-app.mp4` | Bản đăng (thông số ở `refs/final/thong_so.txt`) |
| `DANG_BAI/` | Video, ba ảnh bìa, `1-TikTok.txt`, `2-YouTube-Shorts.txt` |
| `DANG_BAI_tieu_de_mo_ta.txt` | Nguồn duy nhất của tiêu đề, mô tả, thẻ |
| `KIEM_TRA_TIEU_CHI.md` | Bảng soát từng tiêu chí người dùng đặt ra, bảng đối chiếu dữ kiện |
| `research/facts.json`, `research/nguon/` | 17 dữ kiện kèm câu gốc; bản chép nguồn để đối chiếu |
| `research/soat_kich_ban_v1.txt` | Kết quả workflow soát kịch bản 4 góc nhìn (dữ kiện, văn phong, giữ chân người xem, rủi ro giọng đọc) |
| `SOURCES.md`, `TREATMENT.md`, `ANTI-SLOP-CHECK.md` | Nguồn và giấy phép, dàn dựng, sổ soát |
| `tu_lieu_tai_ve/` | Video demo 4K, ảnh chụp bài X, ảnh đầu bài claude.com, ảnh chụp trang Felix |
| `refs/final/` | Thông số bản đăng (`thong_so.txt`), whisper nghe tệp cuối cả bài và từng cảnh (`nghe_cuoi.txt`), khung kiểm tra |
| `refs/qa/` | Ảnh chụp các lượt check trên server (v0 đến v3) |
| `script/KICH_BAN_LOI_DOC.md` | Lời đọc từng câu, chữ đưa vào máy đọc, mã dữ kiện, số đo giọng |

## Dựng lại

1. Kịch bản: sửa `script/tao_kich_ban.py`, chạy nó rồi `script/build_tts_lines.py`. Khi chưa có giọng, `src_build/uoc_moc_loi.py` ước mốc lời để dựng thử cảnh và phụ đề.
2. Đo cách đọc tên tiếng Anh trên server `~/HieuDT/claude_app_reel`: `src/chuan_bi_server.sh`, `src/chuan_bi_v2.sh` (bài đo ở `voice/src/tu_vong1.json`, `tu_vong2.json`).
3. Giọng: `src/chay_giong.sh` (hai tiến trình c3 song song, gộp tệp chọn, c4 ghép; F5 chạy GPU); câu sinh lại riêng dùng `--lines`, `--chon` (ví dụ `src/sinh_b6s2.sh`).
4. Tư liệu: video demo tải từ bài X (bản 4K), cắt bằng ffmpeg (cách cắt ghi trong `.json` cạnh mỗi đoạn); `src_build/chup_felix.py` chụp trang Felix không đăng nhập.
5. `bash src_build/sau_giong.sh`: kéo lời đọc về, dựng index, cảnh (mốc video lấy từ mốc lời đọc), mốc cảnh, phụ đề, bản trộn âm thanh. Mốc âm thanh trong `src_build/scenes.json` ghi theo chữ ("tu": "chạy"), không theo số thứ tự từ.
6. Đẩy `index.html`, `compositions`, `assets` lên `project/`, chạy `work/kiem_server.sh "<các mốc chụp>"` (kết quả đầy đủ ở `project/check_full.log`), rồi `work/dung_cuoi.sh "<mốc đầu cảnh>"` để render, mã hóa và cho whisper nghe tệp cuối.
7. Ảnh bìa: `python -I -X utf8 src_build/render_thumbnail.py v1 v2 --final v1 --alt v2`. Bộ đăng: `python -I -X utf8 src_build/make_upload_kit.py`.

Chạy Python trên laptop bằng `python -I -X utf8` để in được tiếng Việt. Tệp `.sh` phải giữ xuống dòng kiểu LF (CRLF làm bash trên server báo lỗi).

## Dùng repo này để làm reel mới

Repo có đủ mã, tư liệu đã cắt, lời đọc và bản trộn âm thanh để dựng lại reel này. Ba thứ chỉ để ở máy (xem `.gitignore`):
- `refs/qa/`, `refs/demo_khung/`: ảnh chụp các lượt kiểm tra, khoảng 425 MB.
- `tu_lieu_tai_ve/`: video demo 4K và ảnh trang Felix tải gốc. Các đoạn đã cắt để dùng trong phim nằm ở `assets/stock/video/` và `assets/web/`.
- `DANG_BAI/*.mp4`: bản sao video đăng, trùng với `CAAITE-reel-Claude-artifact-app.mp4`.

Cần có:
- Python 3 với Pillow, numpy, scipy, soundfile, playwright; ffmpeg; Node.js để chạy HyperFrames 0.8.101.
- Quyền SSH vào server GPU. Lời đọc (F5-TTS, giọng mẫu A) và bước render chạy ở `~/HieuDT/claude_app_reel`; `voice/src/` là bản sao các script ở `src/` trên server. Giọng mẫu và mô hình không nằm trong repo.

Làm reel mới: chép repo sang thư mục mới; sửa lời đọc trong `script/tao_kich_ban.py`, nguồn và dữ kiện trong `research/`, cảnh trong `src_build/tao_canh.py`, âm thanh trong `src_build/scenes.json`; rồi đi theo các bước ở mục "Dựng lại". Tên thư mục server (`claude_app_reel`) và tên tệp đăng (`CAAITE-reel-Claude-artifact-app`) nằm rải rác trong các script, nhớ đổi hết một lượt. Các bài học khi làm reel này (đặt hiệu ứng âm thanh theo đỉnh tệp, đo điểm ảnh khi đặt khung tô, ẩn phụ đề khi chữ trên hình đã đủ ý) ghi ở `TREATMENT.md`, `ANTI-SLOP-CHECK.md` và `KIEM_TRA_TIEU_CHI.md`.
