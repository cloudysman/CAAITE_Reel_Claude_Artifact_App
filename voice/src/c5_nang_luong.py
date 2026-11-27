"""Đo ngắt nghỉ và tốc độ bằng NĂNG LƯỢNG (server), thay cho mốc cuối từ của MMS_FA.

Lý do (QA lượt 2, 10/10/2026): MMS_FA đặt mốc cuối của nguyên âm hoặc âm mũi cuối cụm sớm hơn thực tế 0,08-0,17 s, nên
khe ở dấu câu đo theo mốc từ dài hơn khe thật (ví dụ "Lưu ý, bản" ghi 0,19 s nhưng thật ra không ngừng chút nào), và
bước rút nghỉ từng cắt vào đuôi chữ "rõ". Ở đây:
- khe_that(): khe lặng thật ở một dấu câu = đoạn dài nhất các khung 5 ms dưới -40 dB so với đỉnh câu, tìm trong
  [mốc cuối từ trước - 0,05 s; mốc đầu từ sau + 0,10 s];
- toc_do_doan(): tốc độ từng đoạn giữa hai dấu câu = số âm tiết / thời gian có tiếng (khung 5 ms trên -40 dB, lấp các
  khe dưới 60 ms như âm tắc), đúng thước người phản biện dùng.
Cách dùng (chấm các bản đã sinh của vài câu, sau c3b_cham_lai.py):
  $PY src/c5_nang_luong.py B3S2 B8S2
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, "/home/hieudt/HieuDT/claude_app_reel/src")
import c2_giong_mau as c2  # noqa: E402
from tts_f5 import normalize_vi  # noqa: E402

GOC = Path("/home/hieudt/HieuDT/claude_app_reel")
OUT = GOC / "work" / "tts"
BUOC = 0.005
NGUONG = -40.0


def dau_ky_tu(tts: str) -> list[str]:
    """Dấu câu đứng sau từng từ (theo cách tách từ của c2.roman), '' nếu không có."""
    dau = []
    for w in re.findall(r"[^\s]+", normalize_vi(tts)):
        k = len(c2.roman(w))
        m = re.search(r"[,.;:!?…]$", w)
        for i in range(k):
            dau.append(m.group() if (m and i == k - 1) else "")
    return dau


def muc_db(x: np.ndarray, sr: int, buoc: float = BUOC) -> tuple[np.ndarray, int]:
    n = max(1, int(sr * buoc))
    k = len(x) // n
    rms = np.sqrt(np.mean(x[:k * n].reshape(k, n) ** 2, axis=1) + 1e-12)
    return 20 * np.log10(rms / (np.abs(x).max() + 1e-9)), n


def khe_that(x: np.ndarray, sr: int, t_cuoi: float, t_dau_sau: float, nguong: float = NGUONG):
    """(độ dài khe thật, đầu khe, cuối khe) theo giây; (0.0, None, None) nếu không có khung nào dưới ngưỡng."""
    lv, n = muc_db(x, sr)
    a = max(0, int((t_cuoi - 0.05) * sr / n))
    b = min(len(lv), int((t_dau_sau + 0.10) * sr / n))
    best, run = (0, None, None), None
    for j in range(a, b):
        if lv[j] < nguong:
            run = j if run is None else run
            if j - run + 1 > best[0]:
                best = (j - run + 1, run, j + 1)
        else:
            run = None
    L, s, e = best
    if not L:
        return 0.0, None, None
    return L * n / sr, s * n / sr, e * n / sr


def khung_lang_nhat(x: np.ndarray, sr: int, t_cuoi: float, t_dau_sau: float):
    """Khung 10 ms lặng nhất trong khe (giây, mức dB so với đỉnh câu)."""
    lv, n = muc_db(x, sr, 0.01)
    a = max(0, int((t_cuoi - 0.05) * sr / n))
    b = min(len(lv), max(a + 1, int((t_dau_sau + 0.10) * sr / n)))
    j = a + int(np.argmin(lv[a:b]))
    return (j + 0.5) * n / sr, float(lv[j])


def thoi_gian_co_tieng(x: np.ndarray, sr: int, t0: float, t1: float) -> float:
    lv, n = muc_db(x, sr)
    a, b = max(0, int(t0 * sr / n)), min(len(lv), int(t1 * sr / n))
    v = lv[a:b] > NGUONG
    on = np.nonzero(v)[0]
    if not len(on):
        return 0.0
    v = v[on[0]:on[-1] + 1].copy()
    # lấp các khe ngắn hơn 60 ms (âm tắc, chỗ chuyển âm tiết)
    j = 0
    while j < len(v):
        if not v[j]:
            k = j
            while k < len(v) and not v[k]:
                k += 1
            if (k - j) * BUOC < 0.06:
                v[j:k] = True
            j = k
        else:
            j += 1
    return float(v.sum() * BUOC)


def doan_cau(tts: str) -> list[tuple[int, int]]:
    """Các đoạn giữa hai dấu câu: (chỉ số từ đầu, chỉ số từ cuối)."""
    dau = dau_ky_tu(tts)
    doan, a = [], 0
    for i, d in enumerate(dau):
        if d or i == len(dau) - 1:
            doan.append((a, i))
            a = i + 1
    return doan


def toc_do_doan(x: np.ndarray, sr: int, moc: list, tts: str, khe: list | None = None) -> list[dict]:
    """Tốc độ từng đoạn (âm tiết / giây có tiếng). Đoạn kết thúc ở khe thật của dấu câu sau nó (nếu biết)."""
    out = []
    dau = dau_ky_tu(tts)
    for a, b in doan_cau(tts):
        t0 = max(0.0, moc[a][0] - 0.03)
        if b + 1 < len(moc):
            kt = khe_that(x, sr, moc[b][1], moc[b + 1][0])
            t1 = kt[1] if kt[1] is not None else moc[b + 1][0]
        else:
            t1 = min(len(x) / sr, moc[b][1] + 0.25)
        tg = thoi_gian_co_tieng(x, sr, t0, t1)
        n = b - a + 1
        out.append({"tu": [a, b], "am_tiet": n, "dau": dau[b], "giay_co_tieng": round(tg, 3),
                    "toc_do": round(n / tg, 2) if tg > 0 else None})
    return out


def khe_dau_cau(x: np.ndarray, sr: int, moc: list, tts: str) -> list[dict]:
    words = c2.roman(tts)
    dau = dau_ky_tu(tts)
    out = []
    for i in range(len(moc) - 1):
        if dau[i]:
            L, s, e = khe_that(x, sr, moc[i][1], moc[i + 1][0])
            out.append({"sau_tu": words[i], "dau": dau[i], "khe_that": round(L, 3)})
    return out


def nua_cau(moc: list, a: int, b: int) -> float:
    """Tốc độ theo khoảng cách giữa đầu các từ trong [a, b] (để so hai nửa của một đoạn dài)."""
    dt = [moc[j + 1][0] - moc[j][0] for j in range(a, b)]
    return round(1.0 / float(np.mean(dt)), 2) if dt else 0.0


def main() -> None:
    ids = sys.argv[1:]
    lines = {c["id"]: c for c in json.loads((GOC / "src/tts_lines.json").read_text(encoding="utf-8"))["cau"]}
    chon = {g["id"]: g for g in json.loads((OUT / "chon.json").read_text(encoding="utf-8"))}
    sys.path.insert(0, str(GOC / "src"))
    import c3_sinh_loi as c3
    bang = {}
    for sid in ids:
        c = lines[sid]
        g = chon[sid]
        print(f"== {sid}: {c['tts']}")
        rows = []
        for r in g["cac_ban"]:
            x, sr = sf.read(OUT / r["tep"])
            moc = r["moc_tu"]
            td = toc_do_doan(x, sr, moc, c["tts"])
            kd = khe_dau_cau(x, sr, moc, c["tts"])
            row = {"tep": r["tep"], "dat": bool(c3.dat(r)), "cer": r["cer"], "tu_dung": r["tu_dung"], "toc_do_vad": r["toc_do"],
                   "giong": r["giong"], "doan": [d["toc_do"] for d in td], "khe": [(k["sau_tu"], k["dau"], k["khe_that"]) for k in kd],
                   "nghe": r["nghe"], "tu_anh": [(t["tu"], t.get("nghe_en"), t.get("dung_en"), t.get("dung_vi")) for t in r["tu_anh"]]}
            if sid == "B3S2":  # "bản dùng thử miễn phí" (từ 2-6) so với "không có phần Cô lab này" (từ 7-12)
                row["nua"] = [nua_cau(moc, 2, 7), nua_cau(moc, 7, len(moc) - 1)]
            rows.append(row)
            print(f"  {r['tep']}: {'ĐẠT' if row['dat'] else '--'} CER {r['cer']} | VAD {r['toc_do']} | đoạn {row['doan']} | "
                  f"khe {row['khe']} | nửa {row.get('nua')} | giống {r['giong']} | {r['nghe']}")
        bang[sid] = rows
    (GOC / "work" / "c5_nang_luong.json").write_text(json.dumps(bang, ensure_ascii=False, indent=1), encoding="utf-8")
    print("C5_DONE")


if __name__ == "__main__":
    main()
