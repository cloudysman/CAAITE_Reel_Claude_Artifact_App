"""Xuất script/KICH_BAN_LOI_DOC.md từ script_final.json, tts_lines.json và số đo giọng (voice/narration_metrics.json)."""
import json
from pathlib import Path

R = Path(__file__).resolve().parents[1]
kb = json.loads((R / "script/script_final.json").read_text(encoding="utf-8"))
tl = {c["id"]: c for c in json.loads((R / "voice/src/tts_lines.json").read_text(encoding="utf-8"))["cau"]}
do = json.loads((R / "voice/narration_metrics.json").read_text(encoding="utf-8"))
m = {c["id"]: c for c in do["cau"]}


def so(x) -> str:
    """Số thập phân viết theo kiểu Việt Nam (dấu phẩy)."""
    return str(x).replace(".", ",")


ra = ["# Kịch bản lời đọc: reel Claude cài artifact thành ứng dụng trên máy tính", "",
      "Mỗi câu: chữ trên phụ đề, chữ đưa vào máy đọc nếu khác, mã dữ kiện (research/facts.json), số đo sau khi ghép.", ""]
for b in kb["beats"]:
    ra += [f"## Cảnh {b['scene']}: {b['purpose']}", ""]
    for s in b["sentences"]:
        hien = " ".join(c["show"] for c in s["chunks"])
        doc = tl[s["id"]]["tts"]
        ra.append(f"- {s['id']}: {hien}")
        if doc != hien:
            ra.append(f"  - Máy đọc: {doc}")
        if s["facts"]:
            ra.append(f"  - Dữ kiện: {', '.join(s['facts'])}")
        k = m[s["id"]]
        tu = ", ".join(f"{t['tu']} nghe '{t['nghe_en']}'" for t in k.get("tu_anh", []))
        ra.append(f"  - Đo: {so(k['toc_do'])} âm tiết/giây, giống giọng {so(k['giong'])}, co giãn {so(k['co_gian'])}"
                  + (f"; tai tiếng Anh: {tu}" if tu else "") + f"; whisper nghe cả câu: {k['nghe']}")
    ra.append("")
t = do["tong"]
ra += ["## Số đo cả bài", "",
       f"- Thời lượng lời {so(t['thoi_luong'])} s, tốc độ trung bình {so(t['toc_do_tb'])} âm tiết/giây (thấp nhất {so(t['toc_do_min_max'][0])}, cao nhất {so(t['toc_do_min_max'][1])}), hệ số biến thiên {so(t['toc_do_cv'])}.",
       f"- Câu đạt {t['cau_dat']}, từ tiếng Anh đạt {t['tu_anh_dung']}, độ giống giọng trung bình {so(t['giong_tb'])}, CER lớn nhất {so(t['cer_max'])}.",
       f"- Khe nghỉ ngắn nhất ở dấu phẩy: {so(t['khe_dau_phay_min'])} s; khe dài nhất trong câu sau khi ghép: {so(t['khe_max_trong_cau_sau'])} s.",
       "- Claude chỉ tính đạt khi tai tiếng Anh nghe ra Claude; whisper tiếng Việt nghe cả câu thường viết \"Cloud\" (xem cột tai tiếng Anh ở từng câu).",
       "- Chưa ai nghe bằng tai.", ""]
(R / "script/KICH_BAN_LOI_DOC.md").write_text("\n".join(ra), encoding="utf-8", newline="\n")
print("đã xuất", len(ra), "dòng")
