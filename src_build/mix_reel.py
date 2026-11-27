"""Trộn âm thanh cho reel (bản tin Unsloth + DeepSeek-V4.1-Flash): lời đọc + nhạc nền + hiệu ứng, chuẩn hóa -14 LUFS.

Cách dùng:
  python src_build/mix_reel.py --plan src_build/audio_plan.json

audio_plan.json (do build_index.py sinh ra, sửa tay được):
{
  "duration": 66.0,                       # độ dài video (giây)
  "narration": "voice/narration.wav",     # lời đọc đã chuẩn hóa -16 LUFS
  "narration_offset": 0.45,               # lời đọc bắt đầu ở giây này của video
  "music": "assets/stock/audio/<bản nhạc>-48k.wav",
  "music_start": 12.0,                    # lấy nhạc từ giây này của bản gốc
  "music_bed_lufs": -23.0,                # độ to nhạc khi không có lời
  "duck_db": -8.0,                        # hạ thêm khi có lời
  "music_fade_out": 1.6,
  "sfx": [{"t": 0.0, "file": "assets/stock/audio/sfx-...-48k.wav", "gain_db": -18.0}, ...],
  "out": "assets/audio/reel-mix.wav"
}

Nhạc được "khoét" dải 1-4 kHz theo đúng lúc có lời (trộn giữa bản khô và bản đã cắt EQ theo mức hạ),
nên giọng rõ mà nhạc không phải hạ quá sâu. Kết quả đo (ebur128 + loudnorm) ghi ra <out>.json.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
from scipy import signal

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_engine as ae  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SR = ae.SR


def peaking(x: np.ndarray, f0: float, gain_db: float, q: float) -> np.ndarray:
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a, -2 * np.cos(w0), 1 - alpha * a]
    den = [1 + alpha / a, -2 * np.cos(w0), 1 - alpha / a]
    return signal.lfilter(b, den, x, axis=0).astype(np.float32)


def env_follow(level: np.ndarray, attack: float, release: float) -> np.ndarray:
    """Bộ bám đường bao một cực, attack/release khác nhau (vòng lặp numpy trên khung 1 ms)."""
    hop = SR // 1000
    frames = level[: len(level) // hop * hop].reshape(-1, hop).max(axis=1)
    a_c, r_c = np.exp(-1 / (attack * 1000)), np.exp(-1 / (release * 1000))
    out = np.zeros_like(frames)
    e = 0.0
    for i, v in enumerate(frames):
        c = a_c if v > e else r_c
        e = c * e + (1 - c) * v
        out[i] = e
    full = np.repeat(out, hop)
    if len(full) < len(level):
        full = np.concatenate([full, np.full(len(level) - len(full), full[-1] if len(full) else 0.0)])
    return full


def ebur128(path: Path) -> dict:
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-filter_complex", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    t = p.stderr
    tail = t[t.rfind("Summary:"):]

    def grab(pat):
        m = re.search(pat, tail)
        return float(m.group(1)) if m else None
    return {"integrated_lufs": grab(r"I:\s+(-?[\d.]+) LUFS"), "lra_lu": grab(r"LRA:\s+(-?[\d.]+) LU"),
            "true_peak_dbtp": grab(r"Peak:\s+(-?[\d.]+) dBFS")}


def lufs_of(x: np.ndarray, tmp: Path) -> float:
    ae.write_wav(tmp, x)
    return ebur128(tmp)["integrated_lufs"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default=str(ROOT / "src_build" / "audio_plan.json"))
    a = ap.parse_args()
    plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
    D = float(plan["duration"])
    n = ae.secs(D)
    tmp = ROOT / "src_build" / "_mix_tmp.wav"

    # 1) Lời đọc
    voice = ae.read_audio(ROOT / plan["narration"])
    vt = ae.Track(D).add(voice, float(plan["narration_offset"]))
    v = vt.buf[:n]

    # 2) Nhạc nền: cắt đoạn, đưa về music_bed_lufs
    music = ae.read_audio(ROOT / plan["music"])
    ms = ae.secs(float(plan.get("music_start", 0.0)))
    m = music[ms: ms + n]
    if len(m) < n:
        m = np.concatenate([m, np.zeros((n - len(m), 2), np.float32)])
    m = ae.fade(m, fin=float(plan.get("music_fade_in", 0.08)), fout=float(plan.get("music_fade_out", 1.6)))
    m_lufs = lufs_of(m, tmp)
    m = m * ae.db(float(plan.get("music_bed_lufs", -23.0)) - m_lufs)

    # 3) Hạ nhạc và khoét 1-4 kHz khi có lời (đường bao theo lời đọc)
    lvl = np.abs(v).max(axis=1)
    envl = env_follow(lvl, attack=0.035, release=0.38)
    env_db = 20 * np.log10(envl + 1e-9)
    amount = np.clip((env_db + 50) / 20, 0, 1)            # 0 khi dưới -50 dBFS, 1 khi trên -30 dBFS
    amount = signal.lfilter([1 - 0.995], [1, -0.995], amount).astype(np.float32)  # làm mượt thêm
    duck = ae.db(float(plan.get("duck_db", -8.0)))
    gain = 1 - (1 - duck) * amount
    m_eq = peaking(peaking(m, 2600, -5.0, 0.9), 1200, -2.5, 1.1)
    m_carved = (m * (1 - amount[:, None]) + m_eq * amount[:, None]) * gain[:, None]

    # 3b) Khoảng lặng có chủ ý (lemo-opuscar DIRECTOR mục 6): hạ nhạc gần như tắt trong music_dips
    #     [{"t": giây, "dur": giây, "db": -30}], vào/ra mượt 0,08 s; âm thanh đầu tiên sau lặng là SFX của cảnh sau
    dip = np.ones(n, np.float32)
    for d in plan.get("music_dips", []):
        a0, a1 = ae.secs(float(d["t"])), ae.secs(float(d["t"]) + float(d["dur"]))
        r = ae.secs(0.08)
        g_low = ae.db(float(d.get("db", -30.0)))
        env = np.ones(n, np.float32)
        lo, hi = max(0, a0 - r), min(n, a1 + r)
        env[a0:a1] = g_low
        if a0 > lo:
            env[lo:a0] = np.linspace(1, g_low, a0 - lo)
        if hi > a1:
            env[a1:hi] = np.linspace(g_low, 1, hi - a1)
        dip = np.minimum(dip, env)
    m_carved = m_carved * dip[:, None]

    # 4) Hiệu ứng âm thanh
    fx = ae.Track(D)
    for c in plan.get("sfx", []):
        clip = ae.read_audio(ROOT / c["file"])
        if c.get("trim"):
            clip = clip[: ae.secs(float(c["trim"]))]
        clip = ae.fade(clip, fin=float(c.get("fade_in", 0.0)), fout=float(c.get("fade_out", 0.05)))
        fx.add(clip, float(c["t"]), float(c.get("gain_db", -18.0)))

    mix = v + m_carved + fx.buf[:n]
    # đỉnh an toàn trước loudnorm (loudnorm chế độ tuyến tính cần đỉnh thấp)
    peak = np.abs(mix).max()
    if peak > 0.89:
        mix = np.tanh(mix / 0.89) * 0.89
    raw = ROOT / "src_build" / "_mix_raw.wav"
    ae.write_wav(raw, mix)
    out = ROOT / plan["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    ln = ae.master(raw, out, lufs=-14.0, tp=-1.5)
    meas = ebur128(out)
    report = {"plan": a.plan, "music_source_lufs": m_lufs, "loudnorm": ln, "ebur128": meas, "duration_s": D,
              "sfx_count": len(plan.get("sfx", []))}
    Path(str(out) + ".json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    for p in (tmp, raw):
        try:
            p.unlink()
        except OSError:
            pass
    print(f"mix -> {out}: I {meas['integrated_lufs']} LUFS, TP {meas['true_peak_dbtp']} dBTP, LRA {meas['lra_lu']} LU "
          f"(loudnorm type {ln.get('normalization_type')})")


if __name__ == "__main__":
    main()
