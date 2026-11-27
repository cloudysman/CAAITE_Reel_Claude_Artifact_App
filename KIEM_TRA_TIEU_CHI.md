# Bảng soát tiêu chí: reel "Claude: cài artifact thành ứng dụng trên máy tính"

Soát ngày 25/11/2026 trên toàn bộ chữ người xem thấy: 15 câu lời đọc, các viên phụ đề, chữ trên hình của 8 cảnh, hai ảnh bìa, chữ đăng bài YouTube và TikTok. Danh sách chữ đã soát: `script/soat_van/chu_tren_hinh.txt` và `script/soat_van/loi_doc.txt`.

## Kết quả theo từng tiêu chí

| Tiêu chí | Kết quả | Căn cứ |
|---|---|---|
| 1. Chất lượng tốt nhất, soát từng chữ | Đạt | Đọc từng dòng 201 khối chữ trên hình và 15 câu lời đọc (`script/soat_van/`). Workflow soát 4 góc nhìn trên bản dựng 2 (hình cảnh 1-4, hình cảnh 5-8, chữ và dữ kiện, âm thanh và tiêu chí video ngắn) báo 61 điểm. Đã xử lý hết ở bản cuối, vài điểm làm khác đề xuất: thanh hạn mức bỏ dòng chữ và canh lại +1 thay vì chèn ảnh nút Ask Claude (ảnh gốc 1000 px, phóng lên bị nhòe); con dấu rút thành một dòng "Anthropic không duyệt trước"; nút tự cập nhật thành biểu tượng tròn trên thanh cửa sổ; chữ thanh cửa sổ tăng lên 28 px trong thanh cũ thay vì nới thanh. Lượt soát độc lập trên bản dựng 4 (2 người soát) xác nhận các sửa đã lên hình và báo thêm 18 điểm nhỏ (hộp thoại còn đứng ngắn, tiếng con dấu chìm trên loa điện thoại, khay nền cho 11 biểu tượng, chữ 26 px, ngắt dòng, mô tả còn chữ cũ); đã sửa hết ở bản cuối. Whisper nghe lại tệp cuối cả bài và từng cảnh (`refs/final/nghe_cuoi.txt`). |
| 2. Đúng trọng tâm | Đạt | 15 câu, mỗi câu một ý theo mạch: làm được gì, cài thế nào, ví dụ, việc không phải làm, ứng dụng làm được gì, ai dùng được, quyền, câu hỏi. Chi tiết phụ (Team, Enterprise, HIPAA-ready, cần mạng) để trên hình và trong mô tả. |
| 3. Chi tiết, dễ hiểu | Đạt | Artifact được giải nghĩa ngay lần đầu xuất hiện; hộp thoại cài đặt chiếu cỡ lớn, khoanh nút Install; ba mức quyền có mô tả từng mức; ví dụ là ứng dụng thật (video demo, trang Felix). |
| 4. Viết hoa | Đạt | Chỉ viết hoa đầu câu, đầu nhãn và tên riêng: Claude, Anthropic, macOS, Windows, Felix, Linnet, Phosphor, Marrow, Sift, Vitals, Tern, Debris Space Tracker, Team, Enterprise, HIPAA-ready, Install as app, CAAITE, PTIT. Hàng nhãn trung tâm và dòng khoa ở khung kết in hoa theo template CAAITE. |
| 5. Một thuật ngữ cho một khái niệm | Đạt | ứng dụng, artifact, Claude bản máy tính, dịch vụ đã kết nối, thanh menu, khay hệ thống, hạn mức sử dụng, toàn quyền (tên mức 3: toàn quyền máy tính), trình duyệt, ứng dụng mẫu, kỹ sư Anthropic, link, bản triển khai hybrid. QA tìm ra ba chỗ lệch (kỹ sư làm Claude, đường link, bản hybrid), đã sửa. |
| 6. Văn phong học thuật, giản dị | Đạt | Không có chữ phóng đại; số liệu duy nhất (3,9 triệu lượt xem) ghi kèm mốc đo. |
| 7. Không bôi đậm tùy tiện | Đạt | Chữ đậm chỉ ở tiêu đề, tên thẻ và con số 3,9 triệu ở viên bài X; đã bỏ chữ đậm ở tên ứng dụng trong chú thích cảnh 05. |
| 8. Trình bày đẹp mắt | Đạt | HyperFrames check bản cuối: 0 lỗi, 0 cảnh báo; 46/46 khối chữ đạt tương phản WCAG AA. Phụ đề tối đa hai dòng, canh giữa, ngắt dòng cố định ở 7 cụm; chữ không lấn cột nút bên phải của TikTok, YouTube; chữ thanh cửa sổ 28 px. |
| 9. Liên kết chặt | Đạt | Mỗi cảnh vào bằng một chữ của lời đọc: "chạy" (biểu tượng), "cài" (mục Install as app), "biểu tượng" (phóng vào Dock), "sửa ảnh", "quản lý", "bản đồ" (ba cửa sổ), "chạy", "sửa" (Tern, Phosphor), "không duyệt" (con dấu). |
| 10. Không trùng lặp | Đạt | Không câu đọc nào lặp ý câu khác. Bốn câu mà chữ trên hình đã in đủ ý (B4S1 ba việc bị gạch, B6S1 hai viên điều kiện, B7S1 thẻ mức 1, B8S1 câu hỏi) thì không hiện phụ đề; bỏ các viên chép lại câu đọc (cảnh 03, 05, 06); hộp thoại chỉ chiếu một lần (cảnh 02). Nhãn ngắn chỉ vào hình có thể lặp một chữ của lời đọc. |
| 11. Đầy đủ thông tin | Đạt | Mọi ý của bài Anthropic có trong video hoặc mô tả: cách cài, cập nhật Claude, biểu tượng và cửa sổ riêng, không đóng gói, ký số, khóa API, tài khoản Claude, dịch vụ kết nối, thông báo, thanh menu, tự cập nhật, chia sẻ, bản thử nghiệm, triển khai dần, Team, Enterprise, HIPAA-ready, hybrid, hạn mức, cần mạng và đăng nhập, artifact không cài được, ba mức quyền, toàn quyền chỉ cho ứng dụng của bạn hoặc tổ chức, hỏi lại sau mỗi lần cập nhật, Anthropic không duyệt. |
| 12. Số liệu trung thực, chính xác | Đạt | Bảng đối chiếu bên dưới; bốn chỗ EZAI viết chưa đúng đã sửa (một cú nhấp, quản trị viên, có ở mọi gói, hạn mức). |
| Humanizer, Signs of AI writing | Đạt | `check_ai_signs.py` trên lời đọc, chữ trên hình, chữ đăng bài: chỉ trúng "key" (nhãn tiếng Anh "API key" ở cảnh 04). Không có gạch ngang dài, ngoặc kép cong, ký tự ẩn. Đọc tay từng câu; tiêu đề 3 bỏ khuôn "là gì? ... những điều cần biết". |
| Video ngắn | Đạt | Móc câu 3 giây: tiêu đề và lời nhắn gõ dần trên quả địa cầu 4K, phóng xuyên quả địa cầu, lóe sáng đúng chữ "chạy" cùng nhịp nhạc. Dài 59,4 s. Lời mời bình luận ở 55,8 s, viên Bình luận ở lại tới khung cuối. Không hẹn lịch chiếu. Dấu CAAITE có suốt video. |

## Đối chiếu dữ kiện

| Chữ trong video | Nguồn gốc |
|---|---|
| Một lời nhắn, Claude làm ra ứng dụng theo dõi rác vũ trụ | Video demo của @ClaudeDevs, giây 0-1: lời nhắn "Build me an app that tracks every piece of space junk in orbit.", trả lời "Here's your space junk tracker." |
| Artifact của Claude giờ cài thành ứng dụng; macOS, Windows; bản thử nghiệm trong Claude bản máy tính | Bài A: "Starting today, you can use Claude artifacts to create, run, and share desktop apps. The "Install as app" feature is rolling out in beta in Claude for Mac and Windows." |
| Bài của @ClaudeDevs: 3,9 triệu lượt xem sau 7 giờ | Bài X1 đăng 02:47 ngày 25/11/2026 (giờ Việt Nam); lúc 10:08 cùng ngày ghi 3.906.556 lượt xem |
| Artifact: trang tương tác Claude tạo ra, như biểu đồ hay trang web | Bài A: "Artifacts started out as a work output you'd share, like a chart or a webpage."; trang Felix: "apps are artifacts (our hosted interactive pages)" |
| Chọn mục cài thành ứng dụng; mục Install as app (Beta); hộp thoại Install | Video demo giây 2-6: menu của artifact có mục "Install as app" gắn nhãn "Beta"; hộp thoại "Install "Debris Space Tracker" as an app?" với nút Cancel, Install |
| Hộp thoại Install "Debris Space Tracker" as an app? chiếu cỡ lớn, khoanh nút Install, nhãn "Bấm Install để cài" | Ảnh cắt từ khung 4,6 s của video demo (3840x2160): hộp thoại có nút Cancel, Install; trong video, nút Install được bấm ở khoảng giây 5,6 |
| Cần cập nhật Claude lên bản mới | Bài A: "Update Claude for Mac or Windows, open an artifact you use every day, and choose "Install as app" from the Share menu." |
| Cài xong, ứng dụng có biểu tượng và cửa sổ riêng; không còn mở bên trong Claude | Bài A: "it gets its own icon and opens in its own window instead of inside Claude" |
| Kỹ sư Anthropic làm thử trình sửa ảnh, trình quản lý tệp, bản đồ cơ thể người; không phải sản phẩm chính thức | Bài A: "Linnet, a full layered image editor", "Phosphor, a file manager"; trang Felix: "Marrow, Body Atlas", "They're not official Anthropic products." |
| Felix viết: bạn không cần biết lập trình | Trang Felix: "You, dear reader, need zero programming skills" |
| Không phải đóng gói, ký số ứng dụng hay tạo khóa API; tài khoản Claude của bạn là đủ; trên hình: dùng tài khoản Claude của bạn, không cần đăng nhập riêng | Bài A: "You don't have to package or sign it, and it uses your Claude account, so there's no API key or separate login." |
| Ứng dụng dùng được các dịch vụ bạn đã kết nối như lịch, email; trên hình: viên Claude, chú thích "Sift dùng Claude để sắp xếp tệp" | Bài A: "Each app can use Claude and your connectors"; ví dụ lịch, email lấy từ câu "a meeting prep page that regularly pulls from their calendar and email" |
| Nếu bạn cho phép, gửi thông báo, hiện trên thanh menu hay khay hệ thống | Bài A: "Installed apps can send notifications or add items to your menu bar or system tray."; X1: "if you allow it, send notifications or add a menu bar item" |
| Sửa artifact thì ứng dụng tự cập nhật; muốn chia sẻ thì gửi link | Bài A: "it updates automatically when the underlying artifact is edited", "You can share it with others"; trang Felix: "To share it with friends and colleagues, send them a link." |
| Sift dùng Claude sắp xếp tệp; Vitals báo hiệu năng máy trên thanh menu | Bài A: "Sift, which sets up folder rules and uses Claude to keep your stuff organized", "Vitals, a menu bar and tray app for peeking at your computer's performance" |
| Tính năng đang ở bản thử nghiệm, triển khai dần cho mọi gói; Team bật sẵn, riêng toàn quyền máy tính bị tắt; Enterprise chờ chủ sở hữu tổ chức bật; trừ tổ chức HIPAA-ready và bản triển khai hybrid | Bài A: "Install as app is rolling out in beta on all plans. HIPAA-ready organizations and hybrid deployments can't use it. It's on by default for Team, with full access off. On Enterprise, it's off until an owner turns it on." |
| Hạn mức sử dụng tính cả lúc làm ứng dụng và mỗi lượt Claude làm việc cho ứng dụng | X2: "Building the app and any calls it makes to Claude count toward your usage limits."; bài A: "Requests the app makes to Claude count toward your plan's usage limits." |
| Cần có mạng và đăng nhập Claude để mở ứng dụng; không cài được Claude Docs, Slides, Sheets | Bài A: "You need to be online and signed in to Claude to open an app. Some artifacts can't be installed, including Claude Docs, Slides, and Sheets." |
| Ba mức quyền: mặc định như trong trình duyệt; quyền ứng dụng (thông báo, phím tắt toàn hệ thống, cửa sổ luôn ở trên); toàn quyền máy tính (chạy chương trình; đọc, sửa, xóa tệp, không hỏi từng lần) | Bài A, mục Permissions: "Default: Installed apps can only do what they'd be able to do in a browser." / "App permissions: ... always-on-top windows, listening for global shortcuts, or sending notifications." / "Full computer access: Apps can ask to run programs and read, change, or delete your files without asking each time." |
| Toàn quyền chỉ cho ứng dụng do bạn hoặc tổ chức của bạn làm; sau mỗi lần cập nhật, Claude hỏi lại quyền | Bài A: "You can only give full access to apps you made or, on Team and Enterprise, apps made by people in your organization." / "Your permission only covers the current version of the app, so Claude asks again after every update, even your own edits." |
| Ứng dụng mẫu minh họa ở cảnh 07: Tern (cửa sổ dòng lệnh), Phosphor (quản lý tệp) | Trang Felix: "Tern Terminal", "A terminal with Claude by your side to help and explain."; "Phosphor File Manager". Video chỉ gọi tên và chức năng, không nói hai ứng dụng này xin toàn quyền |
| Anthropic không duyệt ứng dụng trước khi cài, chỉ nên cấp toàn quyền cho ứng dụng mà bạn tin; con dấu "Anthropic không duyệt trước" | Bài A: "Anthropic doesn't review apps before you install them, so only give full access to apps you trust." |

Bài A: Anthropic, "Turn artifacts into Mac and Windows apps", claude.com/resources/articles/install-as-app, 24/11/2026. X1, X2: hai bài của @ClaudeDevs trên X, 25/11/2026. Trang Felix: claude.ai/artifact/9j53nCVcrSdZyCHtxUZkWJ.

## Chưa kiểm được

- Chưa ai nghe bằng tai. Cần nghe kỹ: chữ Claude ở năm vị trí (whisper tiếng Việt viết "cloud", tai tiếng Anh nghe ra Claude); macOS (đọc "mác ô ét"); chữ "tệp" ở câu B3S1, B7S2; cụm "rác vũ trụ" (giọng Bắc đọc r và gi như nhau, whisper nghe từng cảnh có lúc ra "giác"); các tiếng hiệu ứng đã dời mốc; mức nhạc so với giọng trên loa điện thoại.
- Ảnh bìa chưa thử trên ứng dụng TikTok, YouTube thật.
- Chưa xin phép chủ giọng mẫu (@ainius.net).
- Con số 3,9 triệu lượt xem đo lúc 10:08 ngày 25/11/2026, sẽ còn tăng.
- Tính năng đang triển khai dần: tài khoản của người xem có thể chưa thấy mục Install as app.
