"""Sinh script_final.json và cach_doc.json cho reel "Claude: cài artifact thành ứng dụng trên máy tính".

Kịch bản viết một chỗ ở đây, sửa rồi chạy lại: python -X utf8 script/tao_kich_ban.py && python -X utf8 script/build_tts_lines.py
Nguồn chính (dữ kiện F01-F17 ở research/facts.json):
- Anthropic, "Turn artifacts into Mac and Windows apps", claude.com/resources/articles/install-as-app, 24/11/2026.
- Chuỗi bài của @ClaudeDevs trên X (02:47 ngày 25/11/2026 giờ Việt Nam) và video demo kèm theo.
- Trang "Felix's Demo Apps" của Felix, kỹ sư Anthropic, được bài trên dẫn tới.
Điểm xuất phát: bài EZAI người dùng dán ngày 25/11/2026.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# (mã câu, mã dữ kiện, [(chữ hiện trên phụ đề, chữ cho máy đọc nếu khác)])
S = [
    ("B1", "01-hook", "Móc câu: một lời nhắn, Claude làm ứng dụng theo dõi rác vũ trụ chạy trên máy tính", [
        ("B1S1", ["F01", "F17"], [("Một lời nhắn,", None), ("Claude làm ra ứng dụng", None), ("theo dõi rác vũ trụ chạy trên máy tính.", None)]),
    ]),
    ("B2", "02-cai-dat", "Cách cài: Claude bản máy tính làm artifact, chọn Install as app; ứng dụng có biểu tượng, cửa sổ riêng", [
        ("B2S1", ["F02"], [("Bạn bảo Claude bản máy tính", None), ("làm ra một artifact,", None), ("rồi chọn mục cài thành ứng dụng.", None)]),
        ("B2S2", ["F03", "F01"], [("Cài xong, ứng dụng có biểu tượng", None), ("và cửa sổ riêng", None),
                                  ("trên macOS hay Windows.", "trên mác ô ét hay Windows.")]),
    ]),
    ("B3", "03-vi-du", "Ứng dụng mẫu do kỹ sư Anthropic làm thử", [
        ("B3S1", ["F15"], [("Một kỹ sư Anthropic đã làm thử", None), ("trình sửa ảnh, trình quản lý tệp", None), ("và bản đồ cơ thể người.", None)]),
    ]),
    ("B4", "04-khong-dong-goi", "Không phải đóng gói, ký số, tạo khóa API; tài khoản Claude là đủ", [
        ("B4S1", ["F04"], [("Bạn không phải đóng gói,", None), ("ký số ứng dụng hay tạo khóa API,", None),
                           ("tài khoản Claude của bạn là đủ.", None)]),
    ]),
    ("B5", "05-lam-duoc-gi", "Ứng dụng làm được gì: Claude và dịch vụ đã kết nối, thông báo, thanh menu hay khay hệ thống, tự cập nhật, chia sẻ", [
        ("B5S1", ["F05"], [("Ứng dụng dùng được các dịch vụ", None), ("bạn đã kết nối như lịch, email.", None)]),
        ("B5S2", ["F06"], [("Nếu bạn cho phép,", None), ("nó gửi được thông báo,", None), ("hiện trên thanh menu hay khay hệ thống.", None)]),
        ("B5S3", ["F07"], [("Bạn sửa artifact", None), ("thì ứng dụng tự cập nhật,", None), ("muốn chia sẻ thì gửi link.", None)]),
    ]),
    ("B6", "06-dieu-kien", "Điều kiện dùng: bản thử nghiệm, triển khai dần cho mọi gói; làm và dùng ứng dụng đều tính vào hạn mức", [
        ("B6S1", ["F12"], [("Tính năng đang ở bản thử nghiệm,", None), ("triển khai dần cho mọi gói.", None)]),
        ("B6S2", ["F13"], [("Hạn mức sử dụng tính cả lúc làm ứng dụng", None), ("và mỗi lượt Claude làm việc cho nó.", None)]),
    ]),
    ("B7", "07-quyen", "Ba mức quyền; Anthropic không duyệt trước", [
        ("B7S1", ["F08"], [("Mặc định, ứng dụng chỉ có quyền", None), ("như khi chạy trong trình duyệt.", None)]),
        ("B7S2", ["F08", "F11"], [("Muốn chạy chương trình khác", None), ("hay sửa, xóa tệp,", None), ("nó phải xin toàn quyền.", None)]),
        ("B7S3", ["F10"], [("Vì Anthropic không duyệt ứng dụng", None), ("trước khi cài,", None), ("chỉ nên cấp toàn quyền", None), ("cho ứng dụng mà bạn tin.", None)]),
    ]),
    ("B8", "08-ket", "Hỏi người xem", [
        ("B8S1", [], [("Bạn có cấp toàn quyền", None), ("cho ứng dụng mình làm không?", None)]),
        ("B8S2", [], [("Bình luận cho trung tâm biết nhé.", None)]),
    ]),
]

kb = {
    "version": "v2, 25/11/2026: sửa theo workflow soát 4 góc nhìn (dữ kiện, văn phong, giữ chân người xem, rủi ro giọng đọc; research/soat_kich_ban_v1.txt): đổi móc câu, đưa ví dụ lên sớm, kết bằng câu hỏi về toàn quyền. Tên tiếng Anh theo phép đo ở cach_doc.json. v2.1 (QA bản dựng 2): B7S2 bỏ chữ \"bạn\" (whisper nghe \"xin bạn\" thành \"sinh bản\"), B7S3 thêm \"mà\" (\"bạn tin\" bị nghe \"bản tin\").",
    "target_seconds": 57,
    "structure": "Móc câu (một lời nhắn, ứng dụng theo dõi rác vũ trụ chạy trên máy), cách cài (Claude bản máy tính, artifact, Install as app, biểu tượng và cửa sổ riêng), ví dụ của kỹ sư Anthropic, không phải đóng gói, ký số, tạo khóa API, ứng dụng làm được gì, điều kiện dùng và hạn mức, ba mức quyền, hỏi người xem có cấp toàn quyền không",
    "khong_dung": "Không nói 'một cú nhấp' (phải mở menu, chọn Install as app, bấm Install); không nói 'quản trị viên' bật ở Enterprise (nguồn ghi owner, tức chủ sở hữu); không nói 'đã có ở mọi gói' (đang mở dần, tổ chức HIPAA-ready và bản hybrid chưa dùng được); không gọi ứng dụng mẫu là sản phẩm chính thức của Anthropic.",
    "beats": [{"id": b, "scene": sc, "purpose": pu, "sentences": [{"id": i, "facts": fa, "chunks": [({"show": s, "tts": t} if t else {"show": s}) for s, t in ch]} for i, fa, ch in ss]} for b, sc, pu, ss in S],
}
(ROOT / "script/script_final.json").write_text(json.dumps(kb, ensure_ascii=False, indent=1), encoding="utf-8")
p = ROOT / "script/cach_doc.json"
c = json.loads(p.read_text(encoding="utf-8"))
c["ghi_chu"] = "Cách viết cho máy đọc trong reel Claude cài artifact thành ứng dụng, đo 25/11/2026 bằng voice/src/c2_giong_mau.py (tu_vong1.json, tu_vong2.json), giọng mẫu A: artifact, Anthropic, email, menu, link, ây pi ai đạt 2/2 ở tai tiếng Anh; Claude viết Claud (4/11, chữ gốc 2/11); macOS viết mác ô ét (2/3; Mac 0/9 ở mọi cách viết khác); Windows giữ chữ gốc (2/5). Claude và API chỉ tính đạt theo tai tiếng Anh."
c["tu"] = [
    {"goc": "API", "doc": "ây pi ai", "regex_en": r"\ba\W?p\W?i\b"},
    {"goc": "Claude", "doc": "Claud", "regex_en": r"\bclaude?s?\b|\bclod\b"},
    {"goc": "Anthropic", "doc": "Anthropic", "regex_en": r"\banthropic\b", "regex_vi": "anthropic"},
    {"goc": "artifact", "doc": "artifact", "regex_en": r"\bartifacts?\b|\bartefacts?\b"},
    {"goc": "Windows", "doc": "Windows", "regex_en": r"\bwindows?\b", "regex_vi": "windows"},
    {"goc": "email", "doc": "email", "regex_en": r"\be-?mails?\b", "regex_vi": "email"},
    {"goc": "menu", "doc": "menu", "regex_en": r"\bmenus?\b", "regex_vi": "menu"},
    {"goc": "link", "doc": "link", "regex_en": r"\blinks?\b", "regex_vi": "link"},
]
c["khong_doc"] = {"Install as app": "để trên hình, lời đọc nói 'mục cài thành ứng dụng'", "Enterprise": "để trên hình (chờ chủ sở hữu bật)"}
c["am_tiet_tu_anh"] = {"claud": 1, "claude": 1, "anthropic": 3, "artifact": 3, "windows": 2, "email": 2, "menu": 2, "link": 1}
c["quy_ve"] = [["(?<![a-z])ây pi ai(?![a-z])", "api"], ["(?<![a-z])cloud(?![a-z])", "claude"], ["(?<![a-z])claud(?![a-z])", "claude"],
               ["(?<![a-z])mác ô ét(?![a-z])", "macos"], ["(?<![a-z])mac os(?![a-z])", "macos"], ["(?<![a-z])khoá(?![a-z])", "khóa"],
               ["(?<![a-z])kí(?![a-z])", "ký"], ["(?<![a-z])lí(?![a-z])", "lý"]]
p.write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
print("đã ghi kịch bản", sum(len(b[3]) for b in S), "câu")
