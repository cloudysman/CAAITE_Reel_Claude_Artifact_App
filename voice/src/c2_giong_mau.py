"""Bước 2 (server): chọn đoạn giọng mẫu cho F5-TTS và đo cách viết nào làm từ tiếng Anh được đọc đúng.

Góp ý người nghe (05/10/2026): "API" phải đọc "ây pi ai", "token" phải đọc "tô cừn", câu phải liền mạch.
Whisper tiếng Việt không phân biệt được "API" đọc đúng hay đọc "A pi" (nó vẫn viết "API"), nên phép đo chính ở đây là:
  1. căn chỉnh cưỡng bức MMS_FA (torchaudio) chữ đưa vào máy đọc với âm thanh để lấy đúng đoạn của từ cần đo;
  2. cắt riêng đoạn đó (đệm 0,5 s lặng hai đầu) rồi cho whisper nghe bằng tiếng Anh: tai nghe tiếng Anh viết ra
     đúng từ (API, Cloudflare, agent...) thì cách đọc đủ gần âm tiếng Anh; viết "a pie", "token" thành "to ken"... là trượt;
  3. cho whisper nghe chính đoạn đó bằng tiếng Việt để biết người Việt nghe ra chữ gì.

Phần 1. Đoạn mẫu: cắt 3 đoạn (A, B, C) từ stem giọng, mỗi đoạn sinh 4 câu thử x 2 seed; đo CER (whisper tiếng Việt),
        độ giống giọng (cosine ECAPA với một đoạn giọng thật không dùng làm mẫu), khe lặng lớn nhất trong câu (VAD),
        tốc độ nói. Chọn đoạn giống giọng nhất trong các đoạn CER trung bình <= 0,05.
Phần 2. Với đoạn mẫu đã chọn: mỗi cách viết của từng từ tiếng Anh x 4 seed, đo như trên.
Đầu ra: work/giong/*.wav, work/giong_mau.json
Cách chạy: source env.sh; $PY src/c2_giong_mau.py [--chi-phan-2 MAU]
"""
import argparse
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio

sys.path.insert(0, "/home/hieudt/HieuDT/gpt61_reel/voice/lab/src")
from tts_f5 import F5Engine, normalize_vi, seed_everything  # noqa: E402

W = Path("/home/hieudt/HieuDT/claude_app_reel/work")
OUT = W / "giong"
OUT.mkdir(parents=True, exist_ok=True)
VOCALS = W / "sep/htdemucs/giong_mau/vocals.wav"  # stem giọng (htdemucs) của video TikTok @ainius.net 7630631174901157141
TMP = W / "tmp_doan.wav"

# (đầu, cuối, lời đúng). Lời lấy từ whisper rồi sửa chính tả ("danh giới" -> "ranh giới").
MAU = {
    "A": (124.27, 132.13, "Và các công ty như Google đang đưa phỏng vấn trực tiếp quay trở lại, vì AI đang che ranh giới "
                          "giữa kỹ năng thật và output được trợ giúp."),
    "B": (160.15, 166.65, "Giải pháp mà bài báo đề xuất không phải là cấm AI, mà là thiết kế giao diện hiển thị rõ phần "
                          "nào do AI sinh."),
    "C": (152.61, 159.69, "Nhưng mọi khái niệm, mọi khẳng định lý thuyết là do con người quyết định. Họ công khai ranh "
                          "giới đó ngay trong phần phương pháp."),
}
GIU_LAI = (88.84, 100.22)  # đoạn giọng thật để đo độ giống, không dùng làm mẫu

CAU_THU = [
    "Muốn trợ lý trả lời đúng, nó phải đọc được thông tin mới nhất trên mạng.",
    "Mỗi lượt tìm kiếm được tính tiền thẳng vào tài khoản, không cộng thêm phí.",
    "Nhưng trước khi dùng thật, hãy kiểm tra xem kết quả có kèm đường dẫn nguồn hay không.",
    "Bạn đã thử chưa? Bình luận cho trung tâm biết nhé.",
]

# (mã, từ đo, câu đưa vào máy đọc có đúng một chỗ {X}, các cách viết, regex whisper tiếng Anh phải ra)
TU = [
    ("api", "Giờ chỉ cần gọi một {X} là agent tìm được web.", ["ây pi ai", "API", "ê pi ai"], r"\bapi\b|a\.? ?p\.? ?i\b"),
    ("ai", "Tin mới về {X} trong tuần này.", ["ây ai", "AI"], r"\bai\b|a\.? ?i\.?\b"),
    ("cloudflare", "Hôm qua, {X} vừa ra một dịch vụ mới.",
     ["Cloudflare", "clao phle", "clau phle", "cờ lao phle", "clao phle ơ"], r"cloud ?flare"),
    ("agent", "Đây là mảnh ghép còn thiếu cho {X} lập trình.", ["agent", "ây giần", "ê giần", "ây dần"], r"\bagents?\b"),
    ("web", "Nó tìm trên {X} rồi mới trả lời.", ["web", "uép", "quép"], r"\bweb\b"),
    ("beta", "Dịch vụ đang ở bản {X}, chưa chính thức.", ["beta", "bê ta"], r"\bbeta\b"),
    ("gateway", "Mọi lượt tìm đều đi qua {X} của hãng.", ["AI Gateway", "ây ai ghết uây", "ây ai ghết guây"],
     r"gate ?way"),
    ("ceramic", "Rẻ nhất là {X}, chỉ một phần tư đô.", ["Ceramic", "xơ ram mích", "xê ram mích", "xơ ra mích"],
     r"ceramic"),
    ("exa", "Nhà cung cấp thứ hai là {X}.", ["Exa", "éc xa", "ếch xa", "ếch sa"], r"\bexa\b|\bexxa\b|\bexa\.ai\b"),
    ("linkup", "Nhà cung cấp thứ ba là {X}.", ["Linkup", "linh cắp", "lin cắp", "linh ắp"], r"link ?up"),
    ("brave", "Còn {X} thì lấy năm đô.", ["Brave", "brây", "bờ rây", "brêi"], r"\bbrave\b"),
    ("tavily", "Gói cơ bản của {X} là tám đô.", ["Tavily", "ta vi li", "tơ vi li", "tê vi li"], r"tav[ae]?l[iy]|tavily"),
    ("token", "Giá mỗi triệu {X} đã rẻ hơn nhiều.", ["tô cừn", "token"], r"\btokens?\b"),
]
SEEDS2 = (11, 22, 33, 44)


def chuan(text: str) -> str:
    s = unicodedata.normalize("NFC", text).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


def cer(ref: str, hyp: str) -> float:
    r, h = chuan(ref).replace(" ", ""), chuan(hyp).replace(" ", "")
    d = list(range(len(h) + 1))
    for i, rc in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hc in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rc != hc))
    return d[len(h)] / max(1, len(r))


def roman(text: str) -> list[str]:
    s = unicodedata.normalize("NFD", normalize_vi(text).replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z' ]", " ", s).split()


# Số âm tiết đọc của từ tiếng Anh viết nguyên dạng (từ không có ở đây tính 1)
AM_TIET_ANH = {"meta": 2, "rope": 1, "gqa": 3, "sebastian": 3, "raschka": 2, "amd": 3, "mit": 3, "nvidia": 4, "tencent": 2, "deepseek": 2, "blender": 2, "cad": 1, "gigapixel": 4, "openrouter": 4, "ultra": 2, "pro": 1, "max": 1, "claude": 1, "anthropic": 3, "settings": 2, "usage": 2, "current": 2, "session": 2, "email": 2, "api": 3, "ai": 2, "cloudflare": 3, "agent": 2, "web": 1, "beta": 2, "gateway": 2, "ceramic": 3,
               "exa": 2, "linkup": 2, "brave": 1, "tavily": 3, "token": 2, "google": 2, "output": 2,
               "unsloth": 2, "deepseek": 2, "gguf": 4, "ssd": 3, "ram": 1, "gb": 2, "engram": 2, "mac": 1,
               "studio": 3, "desktop": 2, "benchmark": 2, "flash": 1, "dynamic": 3, "llama": 2, "cpp": 3,
               "microsoft": 3, "windows": 2, "linux": 2, "macos": 3, "gpu": 3, "cpu": 3, "bit": 1, "rem": 1}


def am_tiet(text: str) -> int:
    """Số âm tiết đọc: chữ Việt 1; từ tiếng Anh viết nguyên dạng tra AM_TIET_ANH (không có thì 1)."""
    n = 0
    for w in re.sub(r"[^\w\s]", " ", normalize_vi(text)).split():
        n += AM_TIET_ANH.get(w, 1) if re.fullmatch(r"[a-z]+", w) else 1
    return n


def cat(start: float, end: float, path: Path, sr_out: int = 24000) -> float:
    x, sr = sf.read(VOCALS)
    x = x.mean(axis=1) if x.ndim == 2 else x
    y = x[int(start * sr):int(end * sr)]
    t = torchaudio.functional.resample(torch.tensor(y, dtype=torch.float32), sr, sr_out).numpy()
    fade = int(0.02 * sr_out)
    t[:fade] *= np.linspace(0, 1, fade)
    t[-fade:] *= np.linspace(1, 0, fade)
    t = t * (0.89 / (np.abs(t).max() or 1.0))
    sf.write(path, t, sr_out, subtype="PCM_16")
    return len(t) / sr_out


class May:
    def __init__(self) -> None:
        from faster_whisper import WhisperModel
        from faster_whisper.vad import VadOptions
        from speechbrain.inference.speaker import EncoderClassifier

        # GPU dùng chung, hay đầy: WHISPER_CPU=1 thì chạy whisper trên CPU; lỗi bộ nhớ giữa chừng cũng tự chuyển CPU
        self._WhisperModel = WhisperModel
        if os.environ.get("WHISPER_CPU"):
            self.asr = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=8)
        else:
            try:
                self.asr = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
            except Exception:
                self.asr = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=8)
        self.vad_opt = VadOptions(threshold=0.5, min_silence_duration_ms=120, speech_pad_ms=10, min_speech_duration_ms=60)
        self.ecapa = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",
                                                    savedir="/home/hieudt/HieuDT/gpt61_reel/voice/models/ecapa",
                                                    run_opts={"device": "cpu"})
        bundle = torchaudio.pipelines.MMS_FA
        self.fa_sr = bundle.sample_rate
        self.fa_dev = os.environ.get("MMS_DEVICE", "cuda")
        self.mms = bundle.get_model(with_star=False).to(self.fa_dev).eval()
        self.tok, self.aligner = bundle.get_tokenizer(), bundle.get_aligner()
        self.eng = F5Engine(device=os.environ.get("F5_DEVICE", "cuda"))  # GPU dùng chung đầy thì đặt F5_DEVICE=cpu
        f = OUT / "giu_lai.wav"
        cat(*GIU_LAI, f)
        x, sr = sf.read(f)
        self.e_that = self.emb(x, sr)

    def emb(self, x: np.ndarray, sr: int) -> np.ndarray:
        t = torchaudio.functional.resample(torch.tensor(x, dtype=torch.float32), sr, 16000)
        e = self.ecapa.encode_batch(t.unsqueeze(0)).squeeze().numpy()
        return e / np.linalg.norm(e)

    def sinh(self, ref: Path, ref_text: str, text: str, seed: int, path: Path, rate: float = 4.6) -> float:
        U = self.eng.U
        quiet = lambda *a, **k: None  # noqa: E731
        ref_a, ref_t = U.preprocess_ref_audio_text(str(ref), normalize_vi(ref_text), show_info=quiet)
        ref_len = sf.info(ref_a).duration
        phay = len(re.findall(r"[,;:]", text.strip().rstrip(".!?…")))
        cham = len(re.findall(r"[.!?…](?=\s+\S)", text))
        gen = am_tiet(text) / rate + 0.18 * phay + 0.32 * cham + 0.12
        seed_everything(seed)
        wav, sr, _ = U.infer_process(ref_a, ref_t, normalize_vi(text), self.eng.model, self.eng.vocoder,
                                     mel_spec_type="vocos", show_info=quiet, progress=None, nfe_step=32,
                                     cfg_strength=2.0, sway_sampling_coef=-1.0, speed=1.0,
                                     fix_duration=ref_len + gen, device=self.eng.device)
        wav = np.asarray(wav, dtype=np.float32)
        sf.write(path, wav * min(1.0, 0.89 / (np.abs(wav).max() or 1.0)), sr, subtype="PCM_16")
        return len(wav) / sr

    def nghe(self, x: np.ndarray, sr: int, lang: str, pad: float = 0.0) -> str:
        if pad:
            z = np.zeros(int(pad * sr), dtype=np.float32)
            x = np.concatenate([z, x.astype(np.float32), z])
        sf.write(TMP, x, sr)
        try:
            segs, _ = self.asr.transcribe(str(TMP), language=lang, beam_size=5, condition_on_previous_text=False,
                                          vad_filter=False)
            return " ".join(s.text.strip() for s in segs).strip()
        except RuntimeError as ex:
            if "out of memory" not in str(ex).lower():
                raise
            print("  (GPU hết bộ nhớ: chuyển whisper sang CPU)", flush=True)
            self.asr = self._WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=8)
            segs, _ = self.asr.transcribe(str(TMP), language=lang, beam_size=5, condition_on_previous_text=False,
                                          vad_filter=False)
            return " ".join(s.text.strip() for s in segs).strip()

    def khe_lang(self, x: np.ndarray, sr: int) -> float:
        from faster_whisper.vad import get_speech_timestamps
        x16 = torchaudio.functional.resample(torch.tensor(x, dtype=torch.float32), sr, 16000).numpy()
        ts = get_speech_timestamps(x16, self.vad_opt)
        gaps = [(b["start"] - a["end"]) / 16000 for a, b in zip(ts, ts[1:])]
        return round(max(gaps, default=0.0), 3)

    def can_chinh(self, x: np.ndarray, sr: int, words: list[str]) -> list[tuple[float, float]]:
        x16 = torchaudio.functional.resample(torch.tensor(x, dtype=torch.float32), sr, self.fa_sr)
        with torch.inference_mode():
            em, _ = self.mms(x16.unsqueeze(0).to(self.fa_dev))
            spans = self.aligner(em[0], self.tok(words))
        r = x16.shape[0] / em.shape[1] / self.fa_sr
        return [(s[0].start * r, s[-1].end * r) for s in spans]


def phan_1(may: May) -> dict:
    ket = {}
    for key, (s, e, text) in MAU.items():
        p = OUT / f"mau_{key}.wav"
        dur = cat(s, e, p)
        x, sr = sf.read(p)
        hyp = may.nghe(x, sr, "vi")
        rows = []
        for k, cau in enumerate(CAU_THU):
            for seed in (11, 22):
                f = OUT / f"thu_{key}_{k}_s{seed}.wav"
                d = may.sinh(p, text, cau, seed, f)
                y, sr2 = sf.read(f)
                h = may.nghe(y, sr2, "vi")
                rows.append({"cau": k, "seed": seed, "giay": round(d, 2), "cer": round(cer(cau, h), 3),
                             "giong": round(float(may.emb(y, sr2) @ may.e_that), 3), "khe_lang_max": may.khe_lang(y, sr2),
                             "am_tiet_giay": round(am_tiet(cau) / d, 2), "nghe": h})
        ket[key] = {"doan": [s, e], "giay": round(dur, 2), "cer_cua_mau": round(cer(text, hyp), 3), "mau_nghe": hyp,
                    "giong_tb": round(float(np.mean([r["giong"] for r in rows])), 3),
                    "cer_tb": round(float(np.mean([r["cer"] for r in rows])), 3),
                    "khe_lang_max": max(r["khe_lang_max"] for r in rows), "chi_tiet": rows}
        print(key, {k: v for k, v in ket[key].items() if k != "chi_tiet"}, flush=True)
    return ket


def phan_2(may: May, key: str, tu=None, seeds=SEEDS2) -> list:
    s, e, text = MAU[key]
    p = OUT / f"mau_{key}.wav"
    rows = []
    for ma, khung, cach_viet, pat in (tu or TU):
        for cv in cach_viet:
            cau = khung.replace("{X}", cv)
            words = roman(cau)
            n_truoc = len(roman(khung.split("{X}")[0]))
            n_tu = len(roman(cv))
            ct = []
            for seed in seeds:
                f = OUT / f"tu_{ma}_{re.sub(r'[^a-z]', '', roman(cv) and ''.join(roman(cv)) or 'x')}_s{seed}.wav"
                may.sinh(p, text, cau, seed, f)
                y, sr = sf.read(f)
                # BO_VI=1: bỏ phần nghe bằng tiếng Việt (whisper chạy CPU chậm; tai tiếng Việt nghe đoạn cắt ngắn hay bịa câu)
                bo_vi = bool(os.environ.get("BO_VI"))
                nghe_cau = "" if bo_vi else may.nghe(y, sr, "vi")
                try:
                    spans = may.can_chinh(y, sr, words)
                    a, b = spans[n_truoc][0], spans[n_truoc + n_tu - 1][1]
                    doan = y[max(0, int((a - 0.03) * sr)):int((b + 0.03) * sr)]
                    en = may.nghe(doan, sr, "en", pad=0.5)
                    vi = "" if bo_vi else may.nghe(doan, sr, "vi", pad=0.5)
                    giay_tu = round(b - a, 2)
                except Exception as ex:  # căn chỉnh hỏng: ghi lại, tính là trượt
                    en, vi, giay_tu = f"(lỗi căn chỉnh: {ex})", "", None
                ok = bool(re.search(pat, en.lower()))
                ct.append({"seed": seed, "cau_nghe": nghe_cau, "doan_en": en, "doan_vi": vi, "giay_tu": giay_tu, "dung": ok,
                           "cer_cau": round(cer(cau, nghe_cau), 3)})
            dung = sum(c["dung"] for c in ct)
            rows.append({"ma": ma, "cach_viet": cv, "cau": cau, "dung": f"{dung}/{len(ct)}", "chi_tiet": ct})
            print(f"{ma:10s} {cv:16s} {dung}/{len(ct)} | " + " / ".join(f"{c['doan_en']} ~ {c['doan_vi']}" for c in ct),
                  flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chi-phan-2", default="", help="bỏ phần 1, đo cách viết với đoạn mẫu này (A/B/C)")
    ap.add_argument("--tu", default="", help="tệp JSON [[mã, câu có {X}, [cách viết], regex tiếng Anh], ...] thay cho TU")
    ap.add_argument("--seeds", default="", help="ví dụ 11,22,33,44,55,66")
    ap.add_argument("--ten", default="tu", help="khóa lưu kết quả trong giong_mau.json (tu, tu2...)")
    a = ap.parse_args()
    may = May()
    out_path = W / "giong_mau.json"
    ket = json.loads(out_path.read_text(encoding="utf-8")) if out_path.exists() else {}
    if not a.chi_phan_2:
        ket["mau"] = phan_1(may)
        hop_le = {k: v for k, v in ket["mau"].items() if v["cer_tb"] <= 0.05} or ket["mau"]
        ket["mau_chon"] = max(hop_le, key=lambda k: hop_le[k]["giong_tb"])
        print("CHỌN MẪU", ket["mau_chon"], flush=True)
        out_path.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    key = a.chi_phan_2 or ket["mau_chon"]
    tu = json.loads(Path(a.tu).read_text(encoding="utf-8")) if a.tu else None
    seeds = tuple(int(x) for x in a.seeds.split(",")) if a.seeds else SEEDS2
    ket[a.ten] = {"mau": key, "ket_qua": phan_2(may, key, tu, seeds)}
    out_path.write_text(json.dumps(ket, ensure_ascii=False, indent=1), encoding="utf-8")
    print("C2_DONE")


if __name__ == "__main__":
    main()
