"""Whisper nghe tiếng trên tệp cuối (không gợi ý), so với lời đọc bằng hàm chuẩn hóa của c3_sinh_loi."""
import json
import sys
from pathlib import Path

from faster_whisper import WhisperModel

G = Path.home() / "HieuDT/claude_app_reel"
sys.path.insert(0, str(G / "src"))
import c3_sinh_loi as c3  # noqa: E402

lines = json.loads((G / "src/tts_lines.json").read_text(encoding="utf-8"))
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=8)
seg, _ = m.transcribe(str(G / "work/tu_tep_cuoi.wav"), language="vi", beam_size=5, condition_on_previous_text=False, vad_filter=False)
nghe = " ".join(s.text.strip() for s in seg)
print("whisper:", nghe)
goc = " ".join(c["tts"] for c in lines["cau"])
print("CER:", round(c3.cer_tok(c3.chuan(goc, lines["quy_ve"]), c3.chuan(nghe, lines["quy_ve"])), 4))
