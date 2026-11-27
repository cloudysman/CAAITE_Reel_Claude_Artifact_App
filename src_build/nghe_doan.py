"""Server: cho whisper nghe từng đoạn của tệp cuối (work/tu_tep_cuoi.wav), vì nghe cả bài một lượt thì whisper hay bỏ
hoặc bịa câu ở đoạn có nhạc dày (reel Claude Ultra, reel này: bản cả bài dừng ở giây 43).
Mỗi đoạn là một cảnh (mốc ở scene_timing.json), in chữ whisper nghe để so với lời đọc.
Cách dùng (trên server, trong ~/HieuDT/claude_app_reel): $PY work/nghe_doan.py work/scene_timing.json [tệp wav]
(mặc định work/tu_tep_cuoi.wav; truyền project/assets/audio/reel-mix.wav để nghe bản trộn trước khi render)
"""
import json
import sys
from pathlib import Path

import soundfile as sf
from faster_whisper import WhisperModel

G = Path.home() / "HieuDT/claude_app_reel"
st = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
x, sr = sf.read(sys.argv[2] if len(sys.argv) > 2 else G / "work/tu_tep_cuoi.wav")
x = x.mean(axis=1) if x.ndim == 2 else x
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=8)
for sc in st["scenes"]:
    a, b = int(sc["start"] * sr), int(min(sc["end"], len(x) / sr) * sr)
    tmp = G / "work/tmp_canh.wav"
    sf.write(tmp, x[a:b], sr)
    seg, _ = m.transcribe(str(tmp), language="vi", beam_size=5, condition_on_previous_text=False, vad_filter=False)
    print(f"{sc['id']} ({sc['start']:.1f}-{sc['end']:.1f} s): " + " ".join(s.text.strip() for s in seg), flush=True)
