"""Bộ tổng hợp âm thanh cho intro CAAITE.

Mọi âm thanh tự tổng hợp đều tất định (seed cố định), 48 kHz stereo float32.
Mẫu âm thanh tải về (Mixkit, Pixabay...) được đặt vào timeline qua `place_sample`.
Hàm `master` chuẩn hóa độ to bằng ffmpeg loudnorm hai lượt.
"""
from __future__ import annotations

import json
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 48000
RNG_SEED = 20260929


# ---------------------------------------------------------------- tiện ích
def secs(n: float) -> int:
    return int(round(n * SR))


def silence(duration: float) -> np.ndarray:
    return np.zeros((secs(duration), 2), dtype=np.float32)


def db(x: float) -> float:
    return 10 ** (x / 20)


def midi_hz(m: float) -> float:
    return 440.0 * 2 ** ((m - 69) / 12)


NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6,
        "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def n2m(name: str) -> int:
    """'D4' -> 62"""
    pitch, octave = name[:-1], int(name[-1])
    return 12 * (octave + 1) + NOTE[pitch]


def pan(mono: np.ndarray, p) -> np.ndarray:
    """p in [-1, 1] (vô hướng hoặc mảng), luật công suất bằng nhau."""
    p = np.asarray(p, dtype=np.float32)
    ang = (p + 1) * np.pi / 4
    return np.stack([mono * np.cos(ang), mono * np.sin(ang)], axis=1).astype(np.float32)


def env_adsr(n: int, a: float, d: float, s: float, r: float) -> np.ndarray:
    a_n, d_n, r_n = secs(a), secs(d), secs(r)
    s_n = max(0, n - a_n - d_n - r_n)
    e = np.concatenate([
        np.linspace(0, 1, max(a_n, 1), endpoint=False) ** 1.5,
        np.linspace(1, s, max(d_n, 1), endpoint=False),
        np.full(s_n, s),
        np.linspace(s, 0, max(r_n, 1)) ** 1.2,
    ])
    return e[:n].astype(np.float32) if len(e) >= n else np.pad(e, (0, n - len(e))).astype(np.float32)


def lp(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, min(fc, SR * 0.45), "low", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


def hp(x: np.ndarray, fc: float, order: int = 2) -> np.ndarray:
    sos = signal.butter(order, max(fc, 10), "high", fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0).astype(np.float32)


def bp_sweep(x: np.ndarray, f_start: float, f_end: float, q: float = 1.2, block: int = 256) -> np.ndarray:
    """Lọc thông dải có tần số trung tâm quét theo hàm mũ (xử lý theo khối, giữ trạng thái)."""
    out = np.zeros_like(x)
    n = len(x)
    nblocks = int(np.ceil(n / block))
    zi = None
    for i in range(nblocks):
        frac = i / max(nblocks - 1, 1)
        fc = f_start * (f_end / f_start) ** frac
        bw = fc / q
        lo, hi = max(fc - bw / 2, 20), min(fc + bw / 2, SR * 0.45)
        sos = signal.butter(2, [lo, hi], "bandpass", fs=SR, output="sos")
        seg = x[i * block:(i + 1) * block]
        if zi is None:
            zi = np.zeros((sos.shape[0], 2) + seg.shape[1:])
        y, zi = signal.sosfilt(sos, seg, axis=0, zi=zi)
        out[i * block:(i + 1) * block] = y
    return out.astype(np.float32)


def lp_sweep(x: np.ndarray, f_start: float, f_end: float, block: int = 256) -> np.ndarray:
    out = np.zeros_like(x)
    n = len(x)
    nblocks = int(np.ceil(n / block))
    zi = None
    for i in range(nblocks):
        frac = i / max(nblocks - 1, 1)
        fc = f_start * (f_end / f_start) ** frac
        sos = signal.butter(2, min(fc, SR * 0.45), "low", fs=SR, output="sos")
        seg = x[i * block:(i + 1) * block]
        if zi is None:
            zi = np.zeros((sos.shape[0], 2) + seg.shape[1:])
        y, zi = signal.sosfilt(sos, seg, axis=0, zi=zi)
        out[i * block:(i + 1) * block] = y
    return out.astype(np.float32)


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.standard_normal(n)
    spec = np.fft.rfft(white)
    f = np.fft.rfftfreq(n, 1 / SR)
    f[0] = f[1]
    spec /= np.sqrt(f)
    y = np.fft.irfft(spec, n)
    return (y / (np.abs(y).max() + 1e-9)).astype(np.float32)


def softclip(x: np.ndarray, drive: float = 1.0) -> np.ndarray:
    return (np.tanh(x * drive) / np.tanh(drive)).astype(np.float32)


# ---------------------------------------------------------------- reverb
_IR_CACHE: dict = {}


def reverb_ir(seconds: float = 2.4, damp_hz: float = 7000, predelay: float = 0.018) -> np.ndarray:
    key = (seconds, damp_hz, predelay)
    if key in _IR_CACHE:
        return _IR_CACHE[key]
    rng = np.random.default_rng(RNG_SEED + 7)
    n = secs(seconds)
    t = np.arange(n) / SR
    decay = np.exp(-6.9 * t / seconds)  # -60 dB tại `seconds`
    ir = rng.standard_normal((n, 2)).astype(np.float32) * decay[:, None]
    ir = lp(ir, damp_hz)
    # tần cao tắt nhanh hơn: trộn thêm bản lọc thấp ở đuôi
    tail_lp = lp(ir, damp_hz / 3)
    w = np.clip(t / seconds * 1.6, 0, 1)[:, None]
    ir = ir * (1 - w) + tail_lp * w
    ir = np.concatenate([np.zeros((secs(predelay), 2), np.float32), ir])
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True)) + 1e-9
    _IR_CACHE[key] = ir.astype(np.float32)
    return _IR_CACHE[key]


def apply_reverb(x: np.ndarray, wet: float, seconds: float = 2.4, damp_hz: float = 7000) -> np.ndarray:
    ir = reverb_ir(seconds, damp_hz)
    wet_sig = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[: len(x)] for c in range(2)], axis=1)
    return (x * (1 - wet * 0.5) + wet_sig.astype(np.float32) * wet).astype(np.float32)


# ---------------------------------------------------------------- nhạc cụ
def supersaw_pad(notes: list[str], duration: float, cutoff=(500, 3200), voices: int = 7,
                 detune_cents: float = 14, attack: float = 0.8, release: float = 1.2, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(RNG_SEED + seed)
    n = secs(duration)
    t = np.arange(n) / SR
    out = np.zeros((n, 2), np.float32)
    for note in notes:
        f0 = midi_hz(n2m(note))
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune_cents
            f = f0 * 2 ** (cents / 1200)
            phase = rng.random()
            saw = 2 * ((t * f + phase) % 1.0) - 1
            p = (v - (voices - 1) / 2) / ((voices - 1) / 2) * 0.8
            out += pan(saw.astype(np.float32) / voices, p)
    out /= max(len(notes), 1)
    out = lp_sweep(out, cutoff[0], cutoff[1])
    out = hp(out, 90)
    out *= env_adsr(n, attack, 0.1, 1.0, release)[:, None]
    return out


def sine_pad(notes: list[str], duration: float, attack=0.6, release=1.5) -> np.ndarray:
    n = secs(duration)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for note in notes:
        f = midi_hz(n2m(note))
        out += (np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)).astype(np.float32)
    out /= max(len(notes), 1)
    out *= env_adsr(n, attack, 0.2, 0.9, release)
    return pan(out, 0.0)


def fm_bell(note: str, duration: float = 2.5, ratio: float = 3.5, index: float = 2.2,
            decay: float = 1.6, p: float = 0.0) -> np.ndarray:
    n = secs(duration)
    t = np.arange(n) / SR
    f = midi_hz(n2m(note))
    idx_env = index * np.exp(-t * 3.0)
    mod = np.sin(2 * np.pi * f * ratio * t) * idx_env
    y = np.sin(2 * np.pi * f * t + mod) * np.exp(-t * (6.9 / decay / 3))
    y *= np.minimum(1, t / 0.003)
    return pan(y.astype(np.float32), p)


def pluck(note: str, duration: float = 0.6, bright: float = 4000, p: float = 0.0, seed: int = 0) -> np.ndarray:
    """Tiếng gảy kiểu synth: saw + square lọc thấp với đường bao lọc nhanh."""
    n = secs(duration)
    t = np.arange(n) / SR
    f = midi_hz(n2m(note))
    saw = 2 * ((t * f) % 1.0) - 1
    sq = np.sign(np.sin(2 * np.pi * f * 1.003 * t))
    x = (0.7 * saw + 0.3 * sq).astype(np.float32)
    x = np.stack([x, x], 1)
    x = lp_sweep(x, bright, 400, block=128)[:, 0]
    x *= np.exp(-t * 7) * np.minimum(1, t / 0.002)
    return pan(x.astype(np.float32), p)


def sub_boom(duration: float = 2.2, f_start: float = 110, f_end: float = 34, drive: float = 1.8) -> np.ndarray:
    n = secs(duration)
    t = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-t * 9)
    phase = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(phase) * np.exp(-t * 1.9)
    click_n = secs(0.012)
    rng = np.random.default_rng(RNG_SEED + 3)
    click = np.zeros(n)
    click[:click_n] = rng.standard_normal(click_n) * np.linspace(1, 0, click_n) * 0.5
    y = softclip((body + click).astype(np.float32), drive)
    y *= np.minimum(1, t / 0.001)
    return pan(lp(np.stack([y, y], 1), 4000)[:, 0], 0.0)


def kick(duration: float = 0.5, f_start: float = 150, f_end: float = 48) -> np.ndarray:
    n = secs(duration)
    t = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-t * 28)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    y = softclip(y.astype(np.float32), 1.4)
    return pan(y, 0.0)


def whoosh(duration: float = 1.2, f_start: float = 300, f_end: float = 3500, peak: float = 0.6,
           pan_from: float = -0.7, pan_to: float = 0.7, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(RNG_SEED + 100 + seed)
    n = secs(duration)
    t = np.linspace(0, 1, n)
    x = pink_noise(n, rng)
    x = bp_sweep(np.stack([x, x], 1), f_start, f_end, q=1.4)[:, 0]
    e = np.where(t < peak, (t / peak) ** 2.2, ((1 - t) / (1 - peak)) ** 1.6)
    x = x * e
    x /= np.abs(x).max() + 1e-9
    return pan(x.astype(np.float32), pan_from + (pan_to - pan_from) * t)


def riser(duration: float = 3.0, f_start: float = 180, f_end: float = 1400, seed: int = 0) -> np.ndarray:
    """Tiếng dâng: nhiễu hồng quét lên + sóng sin tăng cao độ; cắt gọn ở cuối để khớp cú hit."""
    rng = np.random.default_rng(RNG_SEED + 200 + seed)
    n = secs(duration)
    t = np.linspace(0, 1, n)
    noise = pink_noise(n, rng)
    noise = bp_sweep(np.stack([noise, noise], 1), 400, 9000, q=0.9)[:, 0]
    f = f_start * (f_end / f_start) ** (t ** 1.3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
    e = t ** 2.4
    y = (0.65 * noise / (np.abs(noise).max() + 1e-9) + 0.35 * tone / 1.4) * e
    y[-secs(0.01):] *= np.linspace(1, 0, secs(0.01))
    left = y.astype(np.float32)
    right = np.roll(left, secs(0.007))
    return np.stack([left, right], 1)


def shimmer(duration: float = 2.8, root: str = "D6", steps=(0, 4, 7, 11, 14, 16), stagger: float = 0.045,
            seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(RNG_SEED + 300 + seed)
    out = silence(duration + 0.5)
    base = n2m(root)
    for i, s in enumerate(steps):
        m = base + s
        name = [k for k, v in NOTE.items() if v == m % 12][0] + str(m // 12 - 1)
        b = fm_bell(name, duration=duration, ratio=2.0 + rng.random() * 2, index=0.8, decay=1.2,
                    p=float(rng.uniform(-0.8, 0.8)))
        o = secs(i * stagger)
        out[o:o + len(b)] += b[: len(out) - o] * (0.85 ** i)
    return hp(out, 1500)


def glitch_blip(duration: float = 0.12, f: float = 2600, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(RNG_SEED + 400 + seed)
    n = secs(duration)
    t = np.arange(n) / SR
    y = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 + np.sin(2 * np.pi * f * 1.5 * t) * 0.5
    y *= (rng.random(n) > 0.15)  # rớt mẫu kiểu số hóa
    y = np.round(y * 6) / 6  # bitcrush
    y *= np.exp(-t * 30)
    return pan(y.astype(np.float32), float(rng.uniform(-0.5, 0.5)))


def tick(f: float = 5200, duration: float = 0.05) -> np.ndarray:
    n = secs(duration)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t * 90)
    return pan(y.astype(np.float32), 0.0)


# ---------------------------------------------------------------- mẫu tải về
def read_audio(path: str | Path) -> np.ndarray:
    """Đọc mọi định dạng qua ffmpeg -> float32 48 kHz stereo."""
    cmd = ["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, 2).copy()


def fade(x: np.ndarray, fin: float = 0.0, fout: float = 0.0) -> np.ndarray:
    x = x.copy()
    if fin > 0:
        k = min(secs(fin), len(x))
        x[:k] *= np.linspace(0, 1, k)[:, None] ** 2
    if fout > 0:
        k = min(secs(fout), len(x))
        x[-k:] *= np.linspace(1, 0, k)[:, None] ** 2
    return x


# ---------------------------------------------------------------- timeline
class Track:
    def __init__(self, duration: float):
        self.buf = silence(duration)

    def add(self, clip: np.ndarray, at: float, gain_db: float = 0.0):
        o = secs(at)
        if o < 0:
            clip = clip[-o:]
            o = 0
        end = min(len(self.buf), o + len(clip))
        if end > o:
            self.buf[o:end] += clip[: end - o] * db(gain_db)
        return self


def sidechain(x: np.ndarray, hits: list[float], depth_db: float = -7, release: float = 0.28) -> np.ndarray:
    g = np.ones(len(x), np.float32)
    for h in hits:
        o = secs(h)
        n = secs(release)
        if o >= len(x):
            continue
        seg = 1 - (1 - db(depth_db)) * (1 - np.linspace(0, 1, n)) ** 2
        end = min(len(x), o + n)
        g[o:end] = np.minimum(g[o:end], seg[: end - o])
    return x * g[:, None]


def bus_compress(x: np.ndarray, threshold_db: float = -14, ratio: float = 2.5, attack: float = 0.01,
                 release: float = 0.15) -> np.ndarray:
    level = np.abs(x).max(axis=1)
    a_c, r_c = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    envl = np.zeros_like(level)
    e = 0.0
    for i, v in enumerate(level):  # chậm nhưng tín hiệu ngắn (~12 s) nên chấp nhận được
        c = a_c if v > e else r_c
        e = c * e + (1 - c) * v
        envl[i] = e
    lvl_db = 20 * np.log10(envl + 1e-9)
    over = np.maximum(lvl_db - threshold_db, 0)
    gain = db(-over * (1 - 1 / ratio))
    return (x * gain[:, None]).astype(np.float32)


def write_wav(path: str | Path, x: np.ndarray):
    x = np.clip(x, -1, 1)
    pcm = (x * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def master(in_wav: str | Path, out_wav: str | Path, lufs: float = -14.0, tp: float = -1.5) -> dict:
    """Chuẩn hóa độ to hai lượt bằng ffmpeg loudnorm, trả số đo."""
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(in_wav), "-af",
                         f"loudnorm=I={lufs}:TP={tp}:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    txt = p1.stderr
    meas = json.loads(txt[txt.rfind("{"): txt.rfind("}") + 1])
    af = (f"loudnorm=I={lufs}:TP={tp}:LRA=11:measured_I={meas['input_i']}:measured_TP={meas['input_tp']}"
          f":measured_LRA={meas['input_lra']}:measured_thresh={meas['input_thresh']}"
          f":offset={meas['target_offset']}:linear=true:print_format=json")
    p2 = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-i", str(in_wav), "-af", af, "-ar", str(SR),
                         "-c:a", "pcm_s16le", str(out_wav)], capture_output=True, text=True)
    txt2 = p2.stderr
    return json.loads(txt2[txt2.rfind("{"): txt2.rfind("}") + 1])
