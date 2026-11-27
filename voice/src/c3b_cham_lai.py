"""Bước 3b (server): chấm lại các bản đã sinh (không sinh lại, không nghe lại) rồi chọn lại.

Lý do chấm lại sau lượt đầu:
1. CER phạt nhầm: whisper viết "0,25" mà máy đọc "không phẩy hai lăm"; giọng Bắc không phân biệt tr/ch, r/d/gi, s/x
   ("giá chênh" bị viết "giá trình"). c3_sinh_loi.chuan() đã sửa cả hai (bỏ chữ "mươi", quy phụ âm đầu về một dạng).
2. Tên riêng (Brave, Tavily, Exa, Ceramic, Linkup): tai tiếng Anh hay tách thành từ khác ("Tavili" -> "That will eat").
   Khán giả là người Việt, nên tên riêng đạt nếu tai tiếng Anh nghe đúng HOẶC whisper tiếng Việt (nghe cả câu) viết ra
   đúng tên (regex_vi trong cach_doc.json). API, AI, Cloudflare... vẫn phải qua tai tiếng Anh, vì whisper tiếng Việt
   vẫn viết "API" dù máy đọc "a pi".
3. Ngắt nghỉ tính lại từ mốc từ (moc_tu) đã lưu: chỗ không có dấu câu mà nghỉ > 0,25 s là ngắt sai; chỗ không dấu
   > 0,55 s hoặc có dấu > 0,90 s là lặng lạ. Khoảng nghỉ ở dấu câu dài hơn 0,45 s sẽ được bước 4 rút còn 0,35 s.
Đọc/ghi work/tts/chon.json. Cách dùng: $PY src/c3b_cham_lai.py
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/hieudt/HieuDT/claude_app_reel/src")
import c2_giong_mau as c2  # noqa: E402
import c3_sinh_loi as c3  # noqa: E402
from tts_f5 import normalize_vi  # noqa: E402

GOC = Path("/home/hieudt/HieuDT/claude_app_reel")


def dau_sau_tu(tts: str) -> list[bool]:
    dau = []
    for w in re.findall(r"[^\s]+", normalize_vi(tts)):
        k = len(c2.roman(w))
        for i in range(k):
            dau.append(bool(re.search(r"[,.;:!?…]$", w)) and i == k - 1)
    return dau


def cham(r: dict, cau: dict, quy_ve: list, vi_ok: dict) -> dict:
    r["cer_cu"] = r.get("cer_cu", r["cer"])
    r["cer"] = round(c3.cer_tok(c3.chuan(cau["tts"], quy_ve), c3.chuan(r["nghe"], quy_ve)), 3)
    words = c2.roman(cau["tts"])
    dau = dau_sau_tu(cau["tts"])
    moc = r["moc_tu"]
    ngat, lang = [], []
    for i in range(len(moc) - 1):
        g = moc[i + 1][0] - moc[i][1]
        co_dau = i < len(dau) and dau[i]
        if (not co_dau and g > 0.55) or (co_dau and g > 0.90):
            lang.append((words[i], words[i + 1], round(g, 2)))
        elif not co_dau and g > 0.25:
            ngat.append((words[i], words[i + 1], round(g, 2)))
    r["ngat_sai"], r["lang_la"] = ngat, lang
    for t in r["tu_anh"]:
        t["dung_en"] = t.get("dung_en", t["dung"])
        pat = vi_ok.get(t["tu"])
        t["dung_vi"] = bool(pat and re.search(pat, r["nghe"].lower()))
        t["dung"] = t["dung_en"] or t["dung_vi"]
    r["tu_dung"] = all(t["dung"] for t in r["tu_anh"])
    return r


def main() -> None:
    data = json.loads((GOC / "src/tts_lines.json").read_text(encoding="utf-8"))
    quy_ve = [(p, r) for p, r in data["quy_ve"]]
    vi_ok = data.get("regex_vi", {})
    cau = {c["id"]: c for c in data["cau"]}
    path = c3.OUT / "chon.json"
    chon = json.loads(path.read_text(encoding="utf-8"))
    p_tay = c3.OUT / "chon_tay.json"
    chon_tay = json.loads(p_tay.read_text(encoding="utf-8")) if p_tay.exists() else {}
    for g in chon:
        c = cau[g["id"]]
        if c2.roman(c["tts"]) != c2.roman(g["chon"].get("tts", c["tts"])) and len(g["chon"]["moc_tu"]) != len(c2.roman(c["tts"])):
            print(f"{g['id']}: lời đã đổi, cần sinh lại")
            g["dat"] = False
            continue
        for r in g["cac_ban"]:
            cham(r, c, quy_ve, vi_ok)
        hop = [r for r in g["cac_ban"] if c3.dat(r)]
        if hop:
            tot = min(hop, key=lambda r: (r["cer"] > 0, abs(r["toc_do"] - 5.0) > 0.4, -r["giong"]))
        else:
            tot = max(g["cac_ban"], key=lambda r: (r["tu_dung"], -len(r["lang_la"]), -len(r["ngat_sai"]), -r["cer"], r["giong"]))
        # chọn tay (work/tts/chon_tay.json): bản đạt mà hai tai đều nghe đúng tên và tốc độ gốc gần 5,0 nhất,
        # để bước ghép không phải co giãn nhiều; chỉ áp khi bản đó đạt
        tay = chon_tay.get(g["id"])
        if tay:
            ung = [r for r in hop if r["tep"] == tay["tep"]]
            if ung:
                tot = ung[0]
                print(f"{g['id']}: chọn tay {tay['tep']} ({tay.get('ly_do', '')})")
            else:
                print(f"{g['id']}: CẢNH BÁO bản chọn tay {tay['tep']} không đạt, giữ bản tự chọn")
        g["dat"], g["chon"] = bool(hop), tot
        print(f"{g['id']}: {len(hop)}/{len(g['cac_ban'])} đạt, chọn {tot['tep']} | CER {tot['cer']} (cũ {tot['cer_cu']}) | "
              f"tên {[(t['tu'], t['dung_en'], t['dung_vi']) for t in tot['tu_anh']]} | ngắt {tot['ngat_sai']} | "
              f"lặng {tot['lang_la']} | {tot['toc_do']} ât/s | giống {tot['giong']} | {tot['nghe']}")
    path.write_text(json.dumps(chon, ensure_ascii=False, indent=1), encoding="utf-8")
    print("C3B_DONE")


if __name__ == "__main__":
    main()
