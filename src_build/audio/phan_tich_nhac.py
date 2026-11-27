"""Tải và đo các bản nhạc nền ứng viên (chạy trên server, venv có librosa + pyloudnorm).

  $PY phan_tich_nhac.py nhac_ung_vien.json out_dir

Mỗi mục: id, ten, url. Ghi out_dir/<id>.mp3, out_dir/<id>_48k.wav và out_dir/phan_tich.json gồm:
- bpm và lưới phách (librosa.beat), độ ổn định nhịp (độ lệch chuẩn khoảng cách phách);
- độ to tích hợp LUFS (pyloudnorm);
- đường năng lượng RMS theo cửa sổ 1 giây (dB) và cửa sổ 58 giây "đều nhất" (độ lệch chuẩn thấp nhất);
- tỉ lệ năng lượng dải 1-4 kHz (dải giọng nói dễ bị lấn) so với toàn dải.
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm as pyln

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
WIN = 58.0


def main():
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    ket = []
    for it in items:
        mp3 = out / f"{it['id']}.mp3"
        if not mp3.exists():
            req = urllib.request.Request(it["url"], headers={"User-Agent": UA, "Referer": "https://mixkit.co/"})
            with urllib.request.urlopen(req, timeout=120) as r:
                mp3.write_bytes(r.read())
        wav = out / f"{it['id']}_48k.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "48000", "-ac", "2", str(wav)], check=True)
        y, sr = librosa.load(str(wav), sr=48000, mono=True)
        dur = len(y) / sr
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
        bt = librosa.frames_to_time(beats, sr=sr, hop_length=512)
        ibi = np.diff(bt) if len(bt) > 2 else np.array([0.0])
        yst, _ = librosa.load(str(wav), sr=48000, mono=False)
        meter = pyln.Meter(sr)
        lufs = float(meter.integrated_loudness(yst.T))
        hop = sr  # 1 giây
        rms = np.array([np.sqrt(np.mean(y[i:i + hop] ** 2) + 1e-12) for i in range(0, len(y) - hop + 1, hop)])
        db = 20 * np.log10(rms + 1e-9)
        best = None
        n = int(WIN)
        for s in range(0, max(1, len(db) - n + 1)):
            seg = db[s:s + n]
            sc = float(np.std(seg))
            if best is None or sc < best[1]:
                best = (s, sc, float(np.mean(seg)), float(np.min(seg)))
        S = np.abs(librosa.stft(y[: int(min(dur, 90) * sr)], n_fft=4096, hop_length=2048)) ** 2
        f = librosa.fft_frequencies(sr=sr, n_fft=4096)
        mid = float(S[(f >= 1000) & (f <= 4000)].sum() / S.sum())
        cen = float(np.mean(librosa.feature.spectral_centroid(y=y[: int(min(dur, 90) * sr)], sr=sr)))
        ket.append({
            "id": it["id"], "ten": it["ten"], "thoi_luong_s": round(dur, 2),
            "bpm": round(float(np.atleast_1d(tempo)[0]), 2), "so_phach": int(len(bt)),
            "lech_chuan_khoang_phach_s": round(float(np.std(ibi)), 4),
            "phach_dau_s": [round(float(t), 3) for t in bt[:8]],
            "lufs": round(lufs, 2),
            "rms_db_moi_giay": [round(float(v), 1) for v in db],
            "cua_so_58s_deu_nhat": {"bat_dau_s": best[0], "lech_chuan_db": round(best[1], 2), "tb_db": round(best[2], 1), "min_db": round(best[3], 1)},
            "ti_le_nang_luong_1_4kHz": round(mid, 4), "trong_tam_pho_hz": round(cen, 1),
        })
        print(it["id"], it["ten"], "bpm", ket[-1]["bpm"], "lufs", ket[-1]["lufs"], "deu", ket[-1]["cua_so_58s_deu_nhat"], "mid", ket[-1]["ti_le_nang_luong_1_4kHz"], flush=True)
    (out / "phan_tich.json").write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
