"""Bước 3 (server): sinh lời đọc từng câu bằng F5-TTS (giọng mẫu đã chọn ở bước 2) và chọn bản tốt nhất.

Mỗi câu sinh trọn một lượt (không cắt ghép giữa câu, để đọc liền mạch). Mỗi bản được đo:
- CER: whisper large-v3 tiếng Việt, không gợi ý, so với lời đưa vào máy (cách viết phiên âm quy về từ gốc:
  "ây pi ai" -> api, "ây ai" -> ai...; số viết bằng chữ);
- từ tiếng Anh: căn chỉnh cưỡng bức MMS_FA, cắt riêng đoạn của từng từ (đệm 0,5 s lặng), whisper nghe bằng tiếng Anh
  phải ra đúng từ (regex của từ); đây là phép đo chính cho góp ý "API đọc ây pi ai, token đọc tô cừn";
- ngắt nghỉ: khe giữa hai từ liền nhau (theo MMS_FA). Khe > 0,22 s ở chỗ không có dấu câu là ngắt sai chỗ;
  khe > 0,55 s ở bất kỳ đâu là lặng lạ;
- tốc độ: âm tiết / thời gian đang nói (VAD silero, bỏ khe lặng từ 120 ms);
- độ giống giọng: cosine ECAPA với đoạn giọng thật giữ lại.
Bản đạt: mọi từ tiếng Anh nghe đúng, CER <= 0,03, không ngắt sai chỗ, không lặng lạ. Trong các bản đạt chọn bản có tốc độ gần
mức mục tiêu nhất rồi giống giọng nhất. Không bản nào đạt thì sinh thêm (tối đa --vong vòng, mỗi vòng 6 seed).

Đầu vào: src/tts_lines.json (dựng ở máy local bằng script/build_tts_lines.py)
Đầu ra: work/tts/<câu>_s<seed>.wav, work/tts/chon.json
Cách chạy: source env.sh; $PY src/c3_sinh_loi.py [--chi B1S1,B4S2] [--toc-do 4.8] [--vong 3] [--seed-tu 0]
           [--lines src/tts_lines_x.json --chon work/tts/chon_x.json]  (thử một cách viết khác cho vài câu, không đè chon.json)
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio

sys.path.insert(0, "/home/hieudt/HieuDT/claude_app_reel/src")
import c2_giong_mau as c2  # noqa: E402
from tts_f5 import normalize_vi, seed_everything  # noqa: E402

GOC = Path("/home/hieudt/HieuDT/claude_app_reel")
W = GOC / "work"
OUT = W / "tts"
REGEX_VI: dict = {}  # nạp từ tts_lines.json (regex_vi của cach_doc.json) trong main()
SO = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]


def doc_so(n: int) -> list[str]:
    if n == 0:
        return ["không"]
    out = []
    for g, ten in ((n // 1_000_000, "triệu"), (n // 1000 % 1000, "nghìn"), (n % 1000, "")):
        if not g:
            continue
        tram, chuc, dv = g // 100, g // 10 % 10, g % 10
        day_du = bool(out)
        if tram or day_du:
            out += [SO[tram], "trăm"]
        if chuc == 0 and dv and (tram or day_du):
            out += ["linh"]
        elif chuc == 1:
            out += ["mười"]
        elif chuc > 1:
            out += [SO[chuc], "mươi"]
        if dv:
            out += ["mốt" if dv == 1 and chuc > 1 else "lăm" if dv == 5 and chuc >= 1 else SO[dv]]
        if ten:
            out += [ten]
    return out


def chu_hoa_so(s: str) -> str:
    def thay(m: re.Match) -> str:
        t = m.group(0)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", t):
            return " ".join(doc_so(int(t.replace(".", ""))))
        if re.fullmatch(r"\d+,\d+", t):
            a, b = t.split(",")
            # số không ở đầu phần thập phân đọc từng chữ: "0,042" là "không phẩy không bốn hai" (reel Decision-1:
            # bỏ số không thì mọi bản của câu giá bị CER 0,09 dù đọc đúng)
            dau0 = len(b) - len(b.lstrip("0"))
            phan = ["không"] * dau0 + (doc_so(int(b)) if b.lstrip("0") else [])
            return " ".join(doc_so(int(a)) + ["phẩy"] + phan)
        if re.fullmatch(r"\d+\.\d+", t):
            # trong reel này chữ số có dấu chấm chỉ là số phiên bản ("Haiku 4.5" đọc "bốn chấm năm"); số thập phân
            # tiếng Việt dùng dấu phẩy (nhánh trên), số nghìn "100.000" đã khớp nhánh đầu
            a, b = t.split(".")
            return " ".join(doc_so(int(a)) + ["chấm"] + doc_so(int(b)))
        return " ".join(doc_so(int(re.sub(r"\D", "", t))))
    return re.sub(r"\d+(?:[.,]\d+)*", thay, s)


def chuan(text: str, quy_ve: list) -> list[str]:
    s = unicodedata.normalize("NFC", text).lower()
    s = s.replace("%", " phần trăm ").replace("$", " đô ")
    s = re.sub(r"(\d)\s*/\s*(\d)", r"\1 trên \2", s)
    # tách số khỏi chữ dính liền ("80gb", "a100"): không tách thì "80gb" thành "tám mươigb", chữ "mươi" không bị bỏ
    # và CER phạt nhầm (reel Colab 10/10: mọi bản của câu có "80 GB" đều bị CER 0,07-0,10)
    s = re.sub(r"(\d+(?:[.,]\d+)*)", r" \1 ", s)
    s = chu_hoa_so(s)
    # hai cách viết cùng một âm tiết: whisper viết "tỷ", lời đọc viết "tỉ"
    s = re.sub(r"\btỷ\b", "tỉ", s)
    s = re.sub(r"(?<=\w)[-.](?=\w)", " ", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for pat, rep in quy_ve:
        s = re.sub(pat, rep, s)
    # giọng Bắc không phân biệt tr/ch, r/d/gi, s/x: quy về một dạng ở cả hai phía để CER không phạt nhầm
    out = []
    for w in s.split():
        w = re.sub(r"^tr", "ch", w)
        w = re.sub(r"^gi(?=[aàáảãạăằắẳẵặâầấẩẫậeèéẻẽẹêềếểễệoòóỏõọôồốổỗộơờớởỡợuùúủũụưừứửữự])", "d", w)
        w = re.sub(r"^r", "d", w)
        w = re.sub(r"^s", "x", w)
        if w == "mươi":  # "hai lăm" (cách đọc tắt) và "hai mươi lăm" (whisper viết 25) coi như nhau
            continue
        out.append(w)
    return out


def cer_tok(a: list[str], b: list[str]) -> float:
    r, h = "".join(a), "".join(b)
    d = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hc in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rc != hc))
    return d[len(h)] / max(1, len(r))


def danh_gia(may: "c2.May", path: Path, cau: dict, quy_ve: list, nguong_ngat: float = 0.22) -> dict:
    y, sr = sf.read(path)
    nghe = may.nghe(y, sr, "vi")
    cer = round(cer_tok(chuan(cau["tts"], quy_ve), chuan(nghe, quy_ve)), 3)
    words = c2.roman(cau["tts"])
    spans = may.can_chinh(y, sr, words)
    # dấu câu sau mỗi từ (theo thứ tự từ đã la-tinh hóa)
    raw = re.findall(r"[^\s]+", normalize_vi(cau["tts"]))
    dau = []
    for w in raw:
        k = len(c2.roman(w))
        for i in range(k):
            dau.append(bool(re.search(r"[,.;:!?…]$", w)) and i == k - 1)
    ngat_sai, lang_la, khe = [], [], []
    for i in range(len(spans) - 1):
        g = spans[i + 1][0] - spans[i][1]
        khe.append(round(g, 3))
        if g > 0.55:
            lang_la.append((words[i], words[i + 1], round(g, 2)))
        elif g > nguong_ngat and not (i < len(dau) and dau[i]):
            ngat_sai.append((words[i], words[i + 1], round(g, 2)))
    tu = []
    for t in cau.get("tu_anh", []):
        a_i, b_i = t["tu_tu"], t["den_tu"]
        a, b = spans[a_i][0], spans[b_i][1]
        doan = y[max(0, int((a - 0.03) * sr)):int((b + 0.03) * sr)]
        en = may.nghe(doan, sr, "en", pad=0.5)
        dung_en = bool(re.search(t["regex_en"], en.lower()))
        # tên riêng (và "rem"): đạt nếu tai tiếng Anh nghe đúng HOẶC whisper tiếng Việt nghe cả câu viết ra đúng tên,
        # giống c3b_cham_lai.cham(); từ không có regex_vi (GB) vẫn phải qua tai tiếng Anh
        pat = REGEX_VI.get(t["tu"])
        dung_vi = bool(pat and re.search(pat, nghe.lower()))
        tu.append({"tu": t["tu"], "nghe_en": en, "dung_en": dung_en, "dung_vi": dung_vi, "dung": dung_en or dung_vi})
    from faster_whisper.vad import get_speech_timestamps
    x16 = torchaudio.functional.resample(torch.tensor(y, dtype=torch.float32), sr, 16000).numpy()
    ts = get_speech_timestamps(x16, may.vad_opt)
    noi = sum(s["end"] - s["start"] for s in ts) / 16000
    return {"nghe": nghe, "cer": cer, "tu_anh": tu, "tu_dung": all(t["dung"] for t in tu),
            "ngat_sai": ngat_sai, "lang_la": lang_la, "khe_max": max(khe, default=0.0),
            "toc_do": round(cau["am_tiet"] / max(0.3, noi), 2), "giay": round(len(y) / sr, 2),
            "giong": round(float(may.emb(y, sr) @ may.e_that), 3),
            "moc_tu": [[round(a, 3), round(b, 3)] for a, b in spans]}


def dat(r: dict) -> bool:
    return r["tu_dung"] and r["cer"] <= 0.03 and not r["ngat_sai"] and not r["lang_la"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi", default="")
    ap.add_argument("--toc-do", type=float, default=4.8, help="âm tiết/giây dùng để đặt thời lượng sinh")
    ap.add_argument("--vong", type=int, default=3)
    ap.add_argument("--seed-tu", type=int, default=0)
    ap.add_argument("--du", type=int, default=2, help="dừng khi có ngần này bản đạt")
    ap.add_argument("--lines", default=str(GOC / "src/tts_lines.json"))
    ap.add_argument("--chon", default=str(OUT / "chon.json"))
    a = ap.parse_args()
    data = json.loads(Path(a.lines).read_text(encoding="utf-8"))
    quy_ve = [(p, r) for p, r in data["quy_ve"]]
    REGEX_VI.update(data.get("regex_vi", {}))
    mau = data["mau"]
    OUT.mkdir(parents=True, exist_ok=True)
    chon_path = Path(a.chon)
    ket = {r["id"]: r for r in json.loads(chon_path.read_text(encoding="utf-8"))} if chon_path.exists() else {}
    chi = set(filter(None, a.chi.split(",")))
    may = c2.May()
    ref = W / "giong" / f"mau_{mau['ma']}.wav"
    for cau in data["cau"]:
        if chi and cau["id"] not in chi:
            continue
        ban = []
        for vong in range(a.vong):
            for s in (11, 22, 33, 44, 55, 66):
                seed = a.seed_tu + s + 100 * vong
                f = OUT / f"{cau['id']}_s{seed}.wav"
                may.sinh(ref, mau["text"], cau["tts"], seed, f, rate=a.toc_do)
                r = danh_gia(may, f, cau, quy_ve)
                r.update({"tep": f.name, "seed": seed})
                ban.append(r)
                print(f"  {cau['id']} s{seed}: CER {r['cer']} | tiếng Anh {[t['nghe_en'] for t in r['tu_anh']]} "
                      f"{'OK' if r['tu_dung'] else '--'} | ngắt sai {r['ngat_sai']} | lặng {r['lang_la']} | "
                      f"{r['toc_do']} ât/s | giống {r['giong']} | {r['nghe']}", flush=True)
                if sum(dat(x) for x in ban) >= a.du:  # đủ số bản đạt thì dừng sớm (GPU dùng chung, đo trên CPU chậm)
                    break
            if sum(dat(r) for r in ban) >= a.du:
                break
        hop = [r for r in ban if dat(r)]
        if hop:
            muc = float(np.median([r["toc_do"] for r in hop]))
            tot = min(hop, key=lambda r: (abs(r["toc_do"] - a.toc_do) > 0.35, -r["giong"]))
        else:
            tot = max(ban, key=lambda r: (r["tu_dung"], -len(r["ngat_sai"]), -len(r["lang_la"]), -r["cer"], r["giong"]))
        ket[cau["id"]] = {"id": cau["id"], "dat": bool(hop), "chon": tot, "so_ban": len(ban), "cac_ban": ban}
        print(f"{cau['id']}: {len(ban)} bản, {len(hop)} đạt, chọn {tot['tep']} | CER {tot['cer']} | "
              f"tiếng Anh {tot['tu_dung']} | {tot['toc_do']} ât/s | giống {tot['giong']} | {tot['nghe']}", flush=True)
        thu_tu = [c["id"] for c in data["cau"]]
        chon_path.write_text(json.dumps([ket[i] for i in thu_tu if i in ket], ensure_ascii=False, indent=1),
                             encoding="utf-8")
    print("C3_DONE")


if __name__ == "__main__":
    main()
