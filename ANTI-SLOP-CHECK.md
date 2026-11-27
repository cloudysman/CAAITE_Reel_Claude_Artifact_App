# Sổ soát reel "Claude: cài artifact thành ứng dụng trên máy tính"

## Dữ kiện

- Đối chiếu từng câu với bài của Anthropic trên claude.com (24/11/2026), chuỗi bài @ClaudeDevs trên X và trang demo của Felix. Câu gốc chép ở `research/facts.json` và `research/nguon/`, bảng đối chiếu ở `KIEM_TRA_TIEU_CHI.md`.
- Không nói "một cú nhấp": video demo cho thấy phải mở menu, chọn Install as app, rồi bấm Install trong hộp thoại.
- Gói Enterprise chờ chủ sở hữu tổ chức (owner) bật, không phải quản trị viên; tính năng "đang triển khai dần" cho mọi gói, không phải "đã có ở mọi gói".
- Hạn mức: nói cả lúc làm ứng dụng lẫn mỗi lượt Claude làm việc cho ứng dụng, đúng bài thứ hai của @ClaudeDevs.
- Ứng dụng mẫu ghi rõ là của Felix, kỹ sư Anthropic, và không phải sản phẩm chính thức của Anthropic.
- Con số 3,9 triệu lượt xem là số đo lúc 10:08 ngày 25/11/2026, khoảng 7 giờ 20 phút sau khi đăng; trên hình ghi "sau 7 giờ".

## Tư liệu

- Toàn bộ hình là tư liệu thật: video demo bản 4K của @ClaudeDevs (cắt dọc từng đoạn), khung hình hộp thoại và menu cắt từ video đó, ảnh chụp bài trên X, ảnh đầu bài trên claude.com, ảnh chụp trang Felix (chụp không đăng nhập, không lộ tài khoản người dùng). Không dùng ảnh do Codex vẽ hay video do Muse tạo, vì tư liệu thật đã đủ cho mọi câu.
- Không vẽ logo Claude hay Anthropic. Chữ, khung, vòng tô, con dấu là đồ họa tự dựng trên tư liệu, không giả giao diện của hãng.

## Văn

- Chạy `check_ai_signs.py` (danh sách từ của trang "Signs of AI writing" bản 24/11/2026 và skill humanizer) trên lời đọc, chữ trên hình và chữ đăng bài: chỉ trúng "key" (nhãn tiếng Anh "API key" ở cảnh 04, là thuật ngữ). Không có gạch ngang dài, ngoặc kép cong, dấu ba chấm một ký tự hay ký tự ẩn.
- Đọc tay từng câu theo humanizer: không có câu "không chỉ... mà còn", không gom ba ý cho đủ nhịp, không có lời khen hay kết sáo. Tiêu đề 3 bỏ khuôn "là gì? ... những điều cần biết".
- Workflow soát chữ trên bản dựng 2 tìm ra: chữ trên hình chép lại nguyên câu đang đọc (cảnh 03, 04, 05, 06, 08), ba thuật ngữ lệch (kỹ sư làm Claude, đường link, bản hybrid), thẻ mức 3 "không hỏi lại" đọc như ngược với ghi chú "Claude hỏi lại quyền". Đã sửa cả ở video, mô tả YouTube và mô tả TikTok.

## Giọng

- F5-TTS, giọng mẫu A (@ainius.net), chạy trên server. Bản cuối: 15/15 câu đạt, tên tiếng Anh 13/13 qua tai tiếng Anh, CER lớn nhất 0, tốc độ trung bình 5,19 âm tiết/giây (hệ số biến thiên 0,007, từ 5,13 đến 5,23).
- Câu B7S2, B7S3 đổi lời sau QA vì whisper nghe "xin bạn" thành "sinh bản" và "bạn tin" thành "bản tin"; bản sinh lại nghe đúng cả hai câu (CER 0).
- Dấu phẩy ở "Một lời nhắn," và "Cài xong," đọc dính (khe 0,01 s): bước ghép chèn lặng cho đủ 0,19 s.
- Tiếng hiệu ứng đặt theo đỉnh của tệp, không theo đầu tệp: tiếng nổ của con dấu từng kêu muộn 2 giây, tiếng phóng ở câu móc từng đè chữ "máy tính"; đã dời. Bỏ một tiếng vút đúp ở cuối cảnh 02. Tiếng nổ trầm của con dấu chìm trên loa điện thoại (đo theo dải tần): thêm một tiếng chạm dải trung đúng lúc dấu chạm; tiếng cửa sổ Marrow đổi sang cùng loại với hai cửa sổ trước.

Chưa ai nghe bằng tai.

## Hình

- Toàn bộ hình là tư liệu thật (video demo 4K của @ClaudeDevs, ảnh hộp thoại cắt từ khung 4K, ảnh chụp trang Felix). Không dùng ảnh Codex hay video Muse.
- Đo điểm ảnh để đặt khung tô: mục Install as app (hàng xám x 229-936, y 831-909 trên ảnh menu), khung artifact, nút Install trên hộp thoại. Bản dựng 2 từng lệch 196 px và 100 px; bản cuối đã khớp.
- Chữ không hiện quá ngắn: các khối chữ từng chỉ đứng 0,3-0,6 s (dịch hộp thoại, câu của Felix, nhãn "Không còn mở bên trong Claude", chú thích cảnh 06) đã bỏ hoặc cho vào sớm.
- Cảnh 06, 07 từng chỉ có chữ: thêm hai ứng dụng mẫu thật (Tern, Phosphor) bật đúng chữ, vệt tô dưới mức 1, thanh hạn mức nhảy theo từng lượt.
- Lượt soát độc lập trên bản dựng 4 (một người xem hình, một người xem chữ và âm thanh) xác nhận các sửa đã lên hình, báo thêm: hộp thoại còn đứng ngắn, khung đầu còn lộ chữ tiếng Anh bị cắt ở nửa dưới, chữ 26 px ở cảnh 06, 07, Dock phóng to mà không khoanh biểu tượng mới, 11 biểu tượng ở cảnh kết lệch màu nền. Đã sửa hết.
- HyperFrames check bản cuối: 0 lỗi, 0 cảnh báo, 46/46 khối chữ đạt WCAG AA.
