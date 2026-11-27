"""Ước mốc lời đọc từ voice/src/tts_lines.json khi chưa có giọng thật, ghi voice/narration_timing_est.json.

Dùng để dựng index, phụ đề, mốc cảnh và chụp thử bố cục trong lúc server còn đang sinh giọng. Có giọng thật thì
build_index.py và build_captions.py tự chuyển sang voice/narration_timing.json.
Giả định: mỗi âm tiết 1/5,0 giây, từ tiếng Anh tính theo am_tiet_tu_anh của cach_doc.json, dấu phẩy nghỉ 0,12 s,
khoảng nghỉ giữa câu như c4_ghep.py (0,25 s cùng đoạn, 0,35 s sang đoạn mới, NGHI của dat_nghi.py nếu có).
Cách dùng: python -X utf8 src_build/uoc_moc_loi.py
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOC_DO = 5.0
NGHI_PHAY = 0.12
NGHI_CUNG_Y, NGHI_Y_MOI = 0.25, 0.35


def main() -> None:
    lines = json.loads((ROOT / "voice" / "src" / "tts_lines.json").read_text(encoding="utf-8"))
    cach_doc = json.loads((ROOT / "script" / "cach_doc.json").read_text(encoding="utf-8"))
    am_anh = {k.lower(): v for k, v in cach_doc.get("am_tiet_tu_anh", {}).items()}
    m = re.search(r"^NGHI = (\{.*\})", (ROOT / "voice" / "src" / "dat_nghi.py").read_text(encoding="utf-8"), re.M)
    nghi_rieng = json.loads(m.group(1)) if m else {}
    t, prev_beat, out = 0.12, None, []
    for c in lines["cau"]:
        if prev_beat is not None:
            t += nghi_rieng.get(c["id"], NGHI_CUNG_Y if c["beat"] == prev_beat else NGHI_Y_MOI)
        prev_beat = c["beat"]
        start, words, chunks = t, [], []
        for ch in c["chunks"]:
            c0 = t
            for w in re.sub(r"[^\w\s]", " ", ch["tts"]).split():
                d = am_anh.get(w.lower(), 1) / TOC_DO
                words.append([round(t, 3), round(t + d * 0.92, 3)])
                t += d
            chunks.append({"display": ch["show"], "start": round(c0, 3), "end": round(t, 3)})
            if ch["tts"].rstrip().endswith(","):
                t += NGHI_PHAY
        out.append({"id": c["id"], "beat": c["beat"], "start": round(start, 3), "end": round(t, 3),
                    "display": c["show"], "chunks": chunks, "words": words})
    res = {"duration": round(t + 0.15, 3), "uoc_luong": True, "sentences": out}
    (ROOT / "voice" / "narration_timing_est.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"ước {len(out)} câu, lời dài {res['duration']} s")


if __name__ == "__main__":
    main()
