"""Dựng lời đưa vào máy đọc (voice/src/tts_lines.json) từ kịch bản (script/script_final.json) và bảng cách đọc (script/cach_doc.json).

- Mỗi câu = nối các cụm (chunks). Lấy "tts" của cụm nếu có, không thì "show", rồi thay từ tiếng Anh theo cach_doc.json
  (từ dài thay trước: "AI Gateway" trước "AI").
- Ghi vị trí (theo chuỗi từ đã bỏ dấu, đúng cách MMS_FA đếm) của từng từ tiếng Anh để bước 3 cắt riêng đoạn đó cho tai tiếng Anh nghe.
- Đếm âm tiết đọc (để đặt thời lượng sinh và đo tốc độ).
Cách dùng: python script/build_tts_lines.py [--kich-ban script/script_final.json] [--cach-doc script/cach_doc.json] [--ra voice/src/tts_lines.json]
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]


def normalize_vi(text: str) -> str:  # giống tts_f5.normalize_vi trên server
    s = unicodedata.normalize("NFC", text).strip()
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"(?<=\w)-(?=\w)", " ", s)
    return re.sub(r"\s+", " ", s.lower())


def roman(text: str) -> list[str]:  # giống c2_giong_mau.roman
    s = unicodedata.normalize("NFD", normalize_vi(text).replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z' ]", " ", s).split()


def tach(text: str) -> list[tuple[str, str]]:
    """Từ bỏ dấu (đúng thứ tự của roman) kèm từ gốc còn dấu, để so khớp không nhầm "Mặc" (mặc định) với "Mac"."""
    out = []
    for tok in normalize_vi(text).split():
        goc = re.sub(r"[^\w']", "", tok)
        out += [(w, goc) for w in roman(tok)]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kich-ban", default=str(ROOT / "script" / "script_final.json"))
    ap.add_argument("--cach-doc", default=str(ROOT / "script" / "cach_doc.json"))
    ap.add_argument("--ra", default=str(ROOT / "voice" / "src" / "tts_lines.json"))
    a = ap.parse_args()
    kb = json.loads(Path(a.kich_ban).read_text(encoding="utf-8"))
    cd = json.loads(Path(a.cach_doc).read_text(encoding="utf-8"))
    terms = sorted(cd["tu"], key=lambda t: -len(t["goc"]))
    out = {"mau": cd["mau"], "quy_ve": cd["quy_ve"], "regex_vi": {t["goc"]: t["regex_vi"] for t in cd["tu"] if t.get("regex_vi")}, "cau": []}
    for beat in kb["beats"]:
        for s in beat["sentences"]:
            parts = []
            for ch in s["chunks"]:
                # cụm có "tts" (số viết bằng chữ...) vẫn được thay từ tiếng Anh theo bảng, như cụm chỉ có "show"
                t = ch.get("tts", ch["show"])
                for term in terms:
                    t = re.sub(r"(?<![\w])" + re.escape(term["goc"]) + r"(?![\w])", term["doc"], t)
                parts.append(t)
            tts = " ".join(parts)
            cap = tach(tts)
            words = [w for w, _ in cap]
            # vị trí từ tiếng Anh trong chuỗi từ bỏ dấu; từ dài đã chiếm chỗ thì từ ngắn bên trong bỏ qua;
            # so cả từ còn dấu để "Mặc định" không bị tính là "Mac"
            dung = [False] * len(words)
            tu_anh = []
            for term in terms:
                seq = tach(term["doc"])
                n = len(seq)
                for i in range(len(cap) - n + 1):
                    if cap[i:i + n] == seq and not any(dung[i:i + n]):
                        if term.get("kiem", True):
                            tu_anh.append({"tu": term["goc"], "tu_tu": i, "den_tu": i + n - 1, "regex_en": term["regex_en"]})
                        for k in range(i, i + n):
                            dung[k] = True
            def dem(text: str) -> int:  # âm tiết đọc; từ còn giữ chữ gốc (Anthropic...) đếm theo bảng
                return sum(cd["am_tiet_tu_anh"].get(w, 1) for w in re.sub(r"[^\w\s]", " ", normalize_vi(text)).split())
            am_tiet = dem(tts)
            out["cau"].append({"id": s["id"], "beat": beat["id"], "show": " ".join(c["show"] for c in s["chunks"]),
                               "tts": tts, "chunks": [{"show": c["show"], "tts": p, "am_tiet": dem(p)} for c, p in zip(s["chunks"], parts)],
                               "am_tiet": am_tiet, "tu_anh": sorted(tu_anh, key=lambda x: x["tu_tu"])})
    dst = Path(a.ra).resolve()
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    tong = sum(c["am_tiet"] for c in out["cau"])
    print(f"{len(out['cau'])} câu, {tong} âm tiết (~{tong / 4.8:.1f} s lời ở 4,8 âm tiết/giây) -> {dst.relative_to(ROOT)}")
    for c in out["cau"]:
        print(f"  {c['id']}: {c['am_tiet']:3d} ât | {c['tts']} | tiếng Anh: {[t['tu'] for t in c['tu_anh']]}")


if __name__ == "__main__":
    main()
