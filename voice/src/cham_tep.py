"""Server: chấm lại một bản đã sinh (đọc tệp wav có sẵn, không sinh lại) rồi ghi làm bản chọn tay cho câu đó.

Dùng khi lượt c3 bị dừng giữa chừng nên chưa ghi tệp chọn, mà log đã cho thấy một bản tốt (ví dụ whisper nghe đúng
chữ "tệp" ở câu B3S1, B7S2 của reel này). Kết quả ghi vào work/tts/chon_tay.json; ghep_cuoi.sh gộp tệp này sau cùng.
Cách dùng (trong ~/HieuDT/claude_app_reel): $PY src/cham_tep.py B3S1:B3S1_s1311.wav [B7S2:B7S2_s1511.wav ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/home/hieudt/HieuDT/claude_app_reel/src")
import c2_giong_mau as c2  # noqa: E402
import c3_sinh_loi as c3  # noqa: E402

GOC = Path("/home/hieudt/HieuDT/claude_app_reel")
lines = json.loads((GOC / "src/tts_lines.json").read_text(encoding="utf-8"))
cau = {c["id"]: c for c in lines["cau"]}
quy_ve = [(p, r) for p, r in lines["quy_ve"]]
c3.REGEX_VI.update(lines.get("regex_vi", {}))
may = c2.May()
p_tay = GOC / "work/tts/chon_tay.json"
tay = {r["id"]: r for r in json.loads(p_tay.read_text(encoding="utf-8"))} if p_tay.exists() else {}
for cap in sys.argv[1:]:
    sid, ten = cap.split(":")
    r = c3.danh_gia(may, GOC / "work/tts" / ten, cau[sid], quy_ve)
    r.update({"tep": ten, "seed": int(ten.rsplit("_s", 1)[1].split(".")[0])})
    tay[sid] = {"id": sid, "dat": c3.dat(r), "chon": r, "so_ban": 1, "cac_ban": [r], "chon_tay": True}
    print(f"{sid} {ten}: CER {r['cer']} | tiếng Anh {[t['nghe_en'] for t in r['tu_anh']]} {r['tu_dung']} | "
          f"{r['toc_do']} ât/s | giống {r['giong']} | {r['nghe']}", flush=True)
p_tay.write_text(json.dumps(list(tay.values()), ensure_ascii=False, indent=1), encoding="utf-8")
