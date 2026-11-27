# Nguồn tin và tư liệu

## Nguồn tin

| Nguồn | Dùng cho | Ghi chú |
|---|---|---|
| Bài của EZAI người dùng dán ngày 25/11/2026 | Điểm xuất phát | Bản tin tiếng Việt về tính năng Install as app của Claude |
| Anthropic, "Turn artifacts into Mac and Windows apps", claude.com/resources/articles/install-as-app, 24/11/2026 | F01 đến F15 | Đọc qua trình duyệt ngày 25/11/2026; nội dung chép để đối chiếu ở `research/nguon/claude_com_install_as_app.txt` |
| @ClaudeDevs trên X, chuỗi hai bài, 02:47 ngày 25/11/2026 giờ Việt Nam (https://x.com/ClaudeDevs/status/2125315491522650299) | F01 đến F06, F12, F13 | Bài 1 kèm video demo 27,6 s; số liệu lúc 10:08 ngày 25/11/2026: 3.906.556 lượt xem, 41.888 lượt thích, 4.208 lượt đăng lại |
| Trang "Felix's Demo Apps" (claude.ai/artifact/9j53nCVcrSdZyCHtxUZkWJ) | F07, F15, F16 | Bài của Anthropic dẫn tới trang này ("demo apps made by one of our engineers"); trang ghi "Content is user-generated and unverified" và "They're not official Anthropic products" |

Câu gốc của từng dữ kiện ở `research/facts.json`; bảng đối chiếu ở `KIEM_TRA_TIEU_CHI.md`.

## Chỗ reel nói rõ hơn bài EZAI

- EZAI viết "chỉ bằng một cú nhấp chuột". Video demo cho thấy phải mở menu của artifact, chọn Install as app rồi bấm Install trong hộp thoại xác nhận, nên reel không nói "một cú nhấp".
- EZAI viết "quản trị viên cần bật" ở gói Enterprise. Nguồn ghi owner, tức chủ sở hữu tổ chức, phải bật; admin của Team, Enterprise chỉ bật tắt quyền ứng dụng và toàn quyền.
- EZAI viết "có trên tất cả các gói". Nguồn ghi tính năng đang triển khai dần (rolling out) ở mọi gói, và tổ chức HIPAA-ready, bản triển khai hybrid không dùng được.
- EZAI viết "việc sử dụng các ứng dụng" tính vào hạn mức. Bài thứ hai của @ClaudeDevs ghi cả lúc làm ứng dụng lẫn mọi lượt ứng dụng dùng Claude.
- EZAI không nói về ba mức quyền, việc Anthropic không duyệt ứng dụng trước khi cài, ứng dụng tự cập nhật, chia sẻ bằng đường link, điều kiện có mạng và đăng nhập, và các artifact không cài được (Claude Docs, Slides, Sheets). Reel nói hoặc ghi trên hình các ý này.
- EZAI nêu ứng dụng thiên văn trong video demo: đúng, ở giây 12,4 của video là ứng dụng "Ravi's night at the dome" điều khiển kính thiên văn.

## Tư liệu hình

| Tệp | Cảnh | Tác giả | Giấy phép, ghi chú |
|---|---|---|---|
| `assets/stock/video/claude-demo-*.mp4` (5 đoạn cắt) | 01, 02 | Anthropic (@ClaudeDevs) | Cắt từ video demo bản 3840x2160 trong bài X; cách cắt ghi trong tệp `.json` kèm mỗi đoạn. Dùng đoạn ngắn để đưa tin, ghi "Video: @ClaudeDevs (Anthropic)" trên hình |
| `assets/web/claude/hop_thoai_cai.png`, `menu_giu.jpg`, `menu_install.png`, `khung_globe.jpg`, `khung_ung_dung.jpg` | 02, ảnh bìa | Anthropic | Khung hình cắt từ video demo trên (hộp thoại cắt từ khung 4,6 s bản 4K) |
| `assets/web/claude/x_post.png` | không dùng trong video (bản cuối bỏ ảnh thu nhỏ ở viên số lượt xem) | @ClaudeDevs | Ảnh chụp bài trên X lúc 10:08 ngày 25/11/2026, giữ làm bằng chứng số lượt xem |
| `assets/web/claude/hero_pixel.jpg` | Ảnh bìa bản phụ | Anthropic | Ảnh đầu bài trên claude.com |
| `assets/web/felix/` (màn hình, 11 biểu tượng, 34 ảnh ứng dụng) | 03, 05, 07, 08 | Felix, kỹ sư Anthropic | Chụp bằng `src_build/chup_felix.py` từ trang công khai, không đăng nhập; ghi nguồn trên hình |
| `music-pop-track-03-lily-j-mixkit-729-48k.wav` ("Pop Track 03") | Toàn bài | Lily J, Mixkit #729 | Mixkit Stock Music Free License |
| `sfx-*-mixkit-*.wav` | Toàn bài | Mixkit | Mixkit Sound Effects Free License; nguồn từng tệp ghi trong `.json` kèm theo |
| `sfx-*-pixabay-48k.wav` | Chuyển cảnh, khung kết | Pixabay | Pixabay Content License (dùng lại từ các reel trước) |

Tư liệu của Anthropic và trang của Felix không có giấy phép mở; reel chỉ dùng đoạn ngắn để đưa tin, ghi nguồn trên hình và trong mô tả, như cách các reel trước dùng hình của hãng.

Không vẽ logo Claude hay Anthropic; tên hãng viết bằng chữ Lexend. Không dùng ảnh do AI tạo (Codex) hay video do AI tạo (Muse): mọi hình là tư liệu thật của Anthropic, trang của Felix, hoặc chữ và hình khối tự dựng.

Giọng đọc nhân bản bằng F5-TTS từ video TikTok @ainius.net (mẫu A, như các reel trước). Chưa xin phép chủ giọng.
