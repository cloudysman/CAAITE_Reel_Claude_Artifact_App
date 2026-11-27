"""Bước 4 (server): ghép các câu đã chọn thành narration.wav và xuất mốc từng cụm (narration_timing.json).

- Cắt lặng hai đầu mỗi câu ở ngưỡng -45 dB (giữ 0,12 s đầu và 0,15 s đuôi để không mất đuôi thanh ngã, thanh hỏi).
- Không cắt ghép bên trong câu (mỗi câu là một lượt đọc liền).
- Khoảng nghỉ giữa hai câu: 0,30 s nếu cùng ý (beat), 0,45 s nếu sang ý mới; hai chỗ lặng có chủ ý (sau câu móc, trước
  câu giới hạn) 0,55 s, khớp music_dips trong src_build/scenes.json.
- Mốc cụm lấy từ căn chỉnh MMS_FA của chính bản đã chọn (moc_tu trong chon.json), trừ đi phần lặng đã cắt.
- Số đo: tốc độ từng câu (âm tiết / thời gian nói theo VAD), độ lệch tốc độ (CV), khe lặng lớn nhất trong câu,
  CER, từ tiếng Anh nghe đúng, độ giống giọng.
Đầu ra: work/narration.wav (24 kHz), work/narration_timing.json, work/narration_metrics.json
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, "/home/hieudt/HieuDT/claude_app_reel/src")
import c2_giong_mau as c2  # noqa: E402
from c3b_cham_lai import dau_sau_tu  # noqa: E402
from c5_nang_luong import dau_ky_tu, khe_dau_cau, khe_that, khung_lang_nhat, toc_do_doan  # noqa: E402

GOC = Path("/home/hieudt/HieuDT/claude_app_reel")
W = GOC / "work"
OUT = W / "tts"
NGHI_CUNG_Y, NGHI_Y_MOI = 0.25, 0.35  # 11/10: rút để reel Decision-1 dưới 59 s (khe giữa hai câu đo theo từ còn khoảng 0,6-0,75 s)
NGHI_RIENG = {"B2S1": 0.4, "B4S1": 0.45, "B6S1": 0.45, "B7S1": 0.5, "B8S1": 0.5}  # nghỉ TRƯỚC câu này
MUC_TOC_DO = 5.2  # âm tiết/giây; người dùng dặn 09/10/2026 tốc độ đọc phải hài hòa, đều (reel trước 5,15)
DAU, DUOI = 0.12, 0.15


def toc_do_vad(y: np.ndarray, sr: int, am_tiet: int) -> float:
    """Âm tiết / thời gian đang nói (VAD silero, bỏ khe lặng từ 120 ms), như bước 3."""
    import torch
    import torchaudio
    from faster_whisper.vad import VadOptions, get_speech_timestamps
    opt = VadOptions(threshold=0.5, min_silence_duration_ms=120, speech_pad_ms=10, min_speech_duration_ms=60)
    x16 = torchaudio.functional.resample(torch.tensor(y, dtype=torch.float32), sr, 16000).numpy()
    noi = sum(s["end"] - s["start"] for s in get_speech_timestamps(x16, opt)) / 16000
    return round(am_tiet / max(0.3, noi), 2)


def co_gian(x: np.ndarray, sr: int, speed: float) -> np.ndarray:
    """Đổi tốc độ, giữ cao độ (ffmpeg atempo, WSOLA); speed > 1 là nhanh hơn."""
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        a_, b_ = Path(d) / "a.wav", Path(d) / "b.wav"
        sf.write(a_, x.astype(np.float32), sr, subtype="FLOAT")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(a_), "-filter:a", f"atempo={speed:.5f}", str(b_)], check=True)
        y, _ = sf.read(b_)
    return y.astype(np.float32)


def bien(x: np.ndarray, sr: int, db: float = -45.0) -> tuple[int, int]:
    n = int(sr * 0.01)
    k = len(x) // n
    rms = np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-12)
    lv = 20 * np.log10(rms / (np.abs(x).max() or 1.0))
    on = np.nonzero(lv > db)[0]
    if not len(on):
        return 0, len(x)
    # đầu tiếng: khung đầu tiên của chuỗi ít nhất 3 khung liền trên ngưỡng (QA lượt 2: một tiếng tách 10 ms trước chữ
    # "Nhưng" của B7S1 bị coi là đầu câu, giữ 0,295 s lặng ở đầu câu và kéo dài chỗ lặng trước bước ngoặt)
    tren = lv > db
    dau3 = [j for j in on if j + 2 < len(tren) and tren[j + 1] and tren[j + 2]]
    a0 = dau3[0] if dau3 else on[0]
    a = max(0, a0 * n - int(DAU * sr))
    b = min(len(x), (on[-1] + 1) * n + int(DUOI * sr))
    return a, b


def main() -> None:
    lines = {c["id"]: c for c in json.loads((GOC / "src/tts_lines.json").read_text(encoding="utf-8"))["cau"]}
    chon = json.loads((OUT / "chon.json").read_text(encoding="utf-8"))
    parts, timing, t, sr0, prev_beat = [], [], 0.0, None, None
    la_cau = []  # phần nào trong parts là câu (để cân độ to từng câu), phần nào là khoảng nghỉ
    metrics = []
    for g in chon:
        c = lines[g["id"]]
        r = g["chon"]
        x, sr = sf.read(OUT / r["tep"])
        sr0 = sr0 or sr
        # Ngắt nghỉ ở dấu câu theo KHE THẬT (năng lượng, c5_nang_luong.py), không theo mốc cuối từ của MMS_FA
        # (QA lượt 2, 10/10/2026: mốc MMS_FA kết thúc sớm 0,08-0,17 s nên "Lưu ý, bản" ghi 0,19 s mà thật ra không ngừng,
        # và lần rút ở "ghi rõ:" từng cắt vào đuôi chữ "rõ").
        # - Khe thật > 0,45 s: rút còn 0,35 s, chỉ cắt bên trong đoạn đã lặng, mờ về 0 trong 10 ms hai phía.
        # - Khe thật quá ngắn (dấu phẩy < 0,15 s; dấu hai chấm, chấm, hỏi < 0,22 s): chèn lặng ở khung 10 ms lặng nhất
        #   (phải dưới -45 dB so với đỉnh câu) cho khe đạt 0,20 s (phẩy) hoặc 0,27 s (hai chấm...). Không có chỗ lặng thì
        #   giữ nguyên và ghi lại để sinh lại câu.
        moc = [list(m) for m in r["moc_tu"]]
        dau = dau_ky_tu(c["tts"])
        rut = []
        n10 = int(0.01 * sr)
        for i in range(len(moc) - 2, -1, -1):
            if i >= len(dau) or not dau[i]:
                continue
            L, ks, ke = khe_that(x, sr, moc[i][1], moc[i + 1][0])
            if L > 0.45:
                a0, b0 = ks + 0.175, ke - 0.175
                ia, ib = int(a0 * sr), int(b0 * sr)
                x = x.copy()
                x[max(0, ia - n10):ia] *= np.linspace(1, 0, ia - max(0, ia - n10))
                x[ib:ib + n10] *= np.linspace(0, 1, len(x[ib:ib + n10]))
                x = np.concatenate([x[:ia], x[ib:]])
                d = (ib - ia) / sr
                for j in range(i + 1, len(moc)):
                    moc[j] = [moc[j][0] - d, moc[j][1] - d]
                rut.append((dau[i], round(L, 3), 0.35))
                continue
            phay = dau[i] in ",;"
            if L < (0.15 if phay else 0.22):
                muc = 0.20 if phay else 0.27
                t_cut, db_cut = khung_lang_nhat(x, sr, moc[i][1], moc[i + 1][0])
                if db_cut > -45:
                    rut.append((dau[i], round(L, 3), f"giữ: không có chỗ lặng ({db_cut:.0f} dB)"))
                    continue
                them = muc - L
                cut = int(t_cut * sr)
                x = x.copy()
                lo = max(0, cut - n10)
                x[lo:cut] *= np.linspace(1, 0, cut - lo)
                hi = min(len(x), cut + n10)
                x[cut:hi] *= np.linspace(0, 1, hi - cut)
                x = np.concatenate([x[:cut], np.zeros(int(them * sr), dtype=x.dtype), x[cut:]])
                for j in range(i + 1, len(moc)):
                    moc[j] = [moc[j][0] + them, moc[j][1] + them]
                rut.append((dau[i], round(L, 3), muc))
        # chỉnh tốc độ từng câu về mức chung (góp ý cũ: "lúc nhanh lúc chậm"), co giãn tối đa ±10%
        truoc = toc_do_vad(x, sr, c["am_tiet"])
        speed = min(1.10, max(0.90, MUC_TOC_DO / truoc))
        if abs(speed - 1.0) > 0.015:
            x = co_gian(x, sr, speed)
            moc = [[m0 / speed, m1 / speed] for m0, m1 in moc]
        sau = toc_do_vad(x, sr, c["am_tiet"])
        # lần chỉnh thứ hai: VAD đo lại sau co giãn có thể lệch; sửa tiếp nếu còn lệch quá 2%, tổng không quá ±12%
        if abs(sau - MUC_TOC_DO) / MUC_TOC_DO > 0.02:
            s2 = min(1.12 / speed, max(0.88 / speed, MUC_TOC_DO / sau))
            if abs(s2 - 1.0) > 0.01:
                x = co_gian(x, sr, s2)
                moc = [[m0 / s2, m1 / s2] for m0, m1 in moc]
                speed *= s2
                sau = toc_do_vad(x, sr, c["am_tiet"])
        kd = khe_dau_cau(x, sr, moc, c["tts"])
        td = toc_do_doan(x, sr, moc, c["tts"])
        r = dict(r, moc_tu=moc, rut_nghi=rut, toc_do_goc=truoc, toc_do=sau, co_gian=round(speed, 3))
        if prev_beat is not None:
            nghi = NGHI_RIENG.get(c["id"], NGHI_CUNG_Y if c["beat"] == prev_beat else NGHI_Y_MOI)
            parts.append(np.zeros(int(nghi * sr), dtype=np.float32))
            la_cau.append(False)
            t += nghi
        a, b = bien(x, sr)
        y = x[a:b].astype(np.float32)
        off = a / sr
        # mốc cụm: chỉ số từ (bỏ dấu) của từng cụm
        moc = r["moc_tu"]
        chunks, i = [], 0
        for ch in c["chunks"]:
            n = len(c2.roman(ch["tts"]))
            s0, s1 = moc[i][0] - off, moc[i + n - 1][1] - off
            chunks.append({"display": ch["show"], "start": round(t + max(0.0, s0), 3),
                           "end": round(t + min(len(y) / sr, s1), 3)})
            i += n
        # mốc từng từ (theo bản đọc tts) để cảnh bám đúng chữ, ví dụ số "tám mươi" hay "ây một trăm"
        words = [[round(t + min(len(y) / sr, max(0.0, m0 - off)), 3), round(t + min(len(y) / sr, max(0.0, m1 - off)), 3)]
                 for m0, m1 in moc]
        timing.append({"id": c["id"], "beat": c["beat"], "start": round(t, 3), "end": round(t + len(y) / sr, 3),
                       "display": c["show"], "chunks": chunks, "words": words})
        # tốc độ từng cụm (âm tiết / thời lượng cụm theo mốc căn chỉnh): bắt chỗ đọc vội hay kéo dài bên trong câu
        toc_cum = []
        for ch, cm in zip(c["chunks"], chunks):
            # số âm tiết đọc của cụm (tts_lines.json mới có sẵn; "Anthropic" là 3 âm tiết chứ không phải 1 từ)
            n_at = ch.get("am_tiet", len(c2.roman(ch["tts"])))
            dur = max(0.2, cm["end"] - cm["start"])
            toc_cum.append(round(n_at / dur, 2))
        metrics.append({"id": c["id"], "tep": r["tep"], "dat": g["dat"], "cer": r["cer"], "toc_do": r["toc_do"], "rut_nghi": rut,
                        "toc_do_goc": r["toc_do_goc"], "co_gian": r["co_gian"],
                        "khe_max": r["khe_max"], "ngat_sai": r["ngat_sai"], "lang_la": r["lang_la"],
                        "tu_anh": r["tu_anh"], "giong": r["giong"], "giay": round(len(y) / sr, 2), "nghe": r["nghe"],
                        "toc_do_cum": toc_cum,
                        # khe thật ở từng dấu câu và tốc độ từng đoạn giữa hai dấu câu, đo bằng năng lượng (c5_nang_luong.py)
                        "khe_dau_cau": [(k["sau_tu"], k["dau"], k["khe_that"]) for k in kd],
                        "toc_do_doan": [(d["am_tiet"], d["toc_do"]) for d in td],
                        # khe lớn nhất giữa hai từ SAU khi rút/nới nghỉ và co giãn (khe_max là số của bản thô)
                        "khe_max_sau": round(max([b[0] - a[1] for a, b in zip(r["moc_tu"], r["moc_tu"][1:])] or [0.0]), 3)})
        parts.append(y)
        la_cau.append(True)
        t += len(y) / sr
        prev_beat = c["beat"]
    # cân độ to từng câu về trung vị (±3 dB) trước khi chuẩn cả bài (QA 10/10: câu bước ngoặt nhỏ hơn mặt bằng lời)
    import pyloudnorm as pyln
    met = pyln.Meter(sr0)
    lu = [met.integrated_loudness(pt) if c else None for pt, c in zip(parts, la_cau)]
    trung = float(np.median([v for v in lu if v is not None and np.isfinite(v)]))
    can_bang = []
    for k, (pt, c) in enumerate(zip(parts, la_cau)):
        if c and lu[k] is not None and np.isfinite(lu[k]):
            g_db = float(np.clip(trung - lu[k], -3.0, 3.0))
            parts[k] = (pt * 10 ** (g_db / 20)).astype(np.float32)
            can_bang.append(round(g_db, 2))
    audio = np.concatenate(parts)
    # chuẩn hóa độ to lời đọc về -16 LUFS (mix_reel.py đặt nhạc nền theo mức tuyệt đối nên lời phải đúng mức này)
    import pyloudnorm as pyln
    lufs0 = pyln.Meter(sr0).integrated_loudness(audio)
    g = 10 ** ((-16.0 - lufs0) / 20)
    audio = (audio * g).astype(np.float32)
    # bộ giới hạn đỉnh mềm (nhìn trước 2 ms, nhả 60 ms) thay cho hạ cả bài: trước đây một đỉnh vượt 0,89 kéo cả lời
    # xuống -17,4 LUFS, làm nhạc nền (đặt theo mức tuyệt đối) to lên tương đối 1,4 dB
    if np.abs(audio).max() > 0.89:
        from scipy.ndimage import maximum_filter1d, minimum_filter1d, uniform_filter1d
        env = maximum_filter1d(np.abs(audio), size=2 * int(0.002 * sr0) + 1)
        gain = np.minimum(1.0, 0.89 / np.maximum(env, 1e-9))
        k = int(0.06 * sr0)
        gain = uniform_filter1d(minimum_filter1d(gain, size=k), size=k)
        audio = (audio * np.minimum(gain, 0.89 / np.maximum(np.abs(audio), 1e-9))).astype(np.float32)
    lufs1 = pyln.Meter(sr0).integrated_loudness(audio)
    sf.write(W / "narration.wav", audio, sr0, subtype="PCM_24")
    (W / "narration_timing.json").write_text(json.dumps({"duration": round(t, 3), "sentences": timing},
                                                        ensure_ascii=False, indent=1), encoding="utf-8")
    tocdo = np.array([m["toc_do"] for m in metrics])
    tong = {"thoi_luong": round(t, 2), "lufs_truoc": round(float(lufs0), 2), "lufs_sau": round(float(lufs1), 2),
            "dinh_dbfs": round(float(20 * np.log10(np.abs(audio).max())), 2), "toc_do_tb": round(float(tocdo.mean()), 2),
            "toc_do_cv": round(float(tocdo.std() / tocdo.mean()), 3),
            "toc_do_min_max": [float(tocdo.min()), float(tocdo.max())],
            "cau_dat": f"{sum(m['dat'] for m in metrics)}/{len(metrics)}",
            "tu_anh_dung": f"{sum(t2['dung'] for m in metrics for t2 in m['tu_anh'])}/{sum(len(m['tu_anh']) for m in metrics)}",
            "cer_max": max(m["cer"] for m in metrics), "khe_max_trong_cau": max(m["khe_max"] for m in metrics),
            "khe_max_trong_cau_sau": max(m["khe_max_sau"] for m in metrics), "can_bang_cau_db": can_bang,
            "giong_tb": round(float(np.mean([m["giong"] for m in metrics])), 3),
            "khe_dau_phay_min": min((k[2] for m in metrics for k in m["khe_dau_cau"] if k[1] in ",;"), default=None),
            "khe_dau_hai_cham_min": min((k[2] for m in metrics for k in m["khe_dau_cau"] if k[1] not in ",;"), default=None),
            "toc_do_doan_trung_vi": round(float(np.median([v for m in metrics for n, v in m["toc_do_doan"] if v and n >= 4])), 2),
            # lệch lớn nhất của tốc độ cụm so với mức chung (cụm 1-2 âm tiết bỏ qua vì mốc căn chỉnh quá ngắn để đo)
            "lech_cum_max": round(float(max(abs(v - MUC_TOC_DO) / MUC_TOC_DO for m, cc in zip(metrics, [lines[x["id"]]["chunks"] for x in metrics])
                                            for v, ch in zip(m["toc_do_cum"], cc) if ch.get("am_tiet", len(c2.roman(ch["tts"]))) >= 4)), 3)}
    (W / "narration_metrics.json").write_text(json.dumps({"tong": tong, "cau": metrics}, ensure_ascii=False, indent=1),
                                              encoding="utf-8")
    print(json.dumps(tong, ensure_ascii=False))
    for m in metrics:
        print(f"{m['id']}: {m['toc_do']} ât/s (cụm {m['toc_do_cum']}) | CER {m['cer']} | khe {m['khe_max']} | {'OK' if m['dat'] else 'CHƯA ĐẠT'} | "
              f"{[(x['tu'], x['nghe_en']) for x in m['tu_anh']]} | {m['nghe']}")
    print("C4_DONE")


if __name__ == "__main__":
    main()
