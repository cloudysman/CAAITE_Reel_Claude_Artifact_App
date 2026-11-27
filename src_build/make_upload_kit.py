"""Dựng thư mục DANG_BAI/ để đăng một lượt lên TikTok và YouTube Shorts.

- Chép video bản đăng và ảnh bìa (đặt tên theo nền tảng) vào DANG_BAI/.
- Điền phần mô tả và thẻ của YouTube vào DANG_BAI/2-YouTube-Shorts.txt từ DANG_BAI_tieu_de_mo_ta.txt (một nguồn duy nhất,
  sửa ở đó rồi chạy lại), từ bản mẫu src_build/upload_kit/2-YouTube-Shorts.tmpl.txt.
- Kiểm tra giới hạn của nền tảng: tiêu đề YouTube <= 100 ký tự, mô tả YouTube <= 5000 ký tự, tổng thẻ <= 500 ký tự,
  mô tả TikTok <= 4000 ký tự; không có gạch ngang dài, ngoặc kép cong, ký tự ẩn.
Cách dùng: python src_build/make_upload_kit.py
"""
import re
import shutil
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "DANG_BAI"
VIDEO = "CAAITE-reel-Claude-artifact-app.mp4"
ANH = {
    "anh-bia-TikTok.jpg": "thumbnail/CAAITE-Claude-artifact-app-anh-bia.jpg",
    "anh-bia-YouTube.jpg": "thumbnail/CAAITE-Claude-artifact-app-anh-bia-ban-phu.jpg",
    "anh-bia-YouTube-ban-khac.jpg": "thumbnail/CAAITE-Claude-artifact-app-anh-bia.jpg",
}
CAM = re.compile(r"[—–“”‘’​-‏⁠﻿]")


def khoi(text: str, dau: str, cuoi: str) -> str:
    a = text.index(dau) + len(dau)
    b = text.index(cuoi, a)
    return text[a:b].strip("\n")


def main() -> None:
    nguon = (ROOT / "DANG_BAI_tieu_de_mo_ta.txt").read_text(encoding="utf-8")
    mo_ta = khoi(nguon, "Mô tả (YouTube, dán nguyên phần dưới đây; TikTok dùng bản ngắn trong DANG_BAI/1-TikTok.txt)\n",
                 "\n\n\nThẻ (YouTube").strip()
    the = nguon.split('Thẻ (YouTube, dán vào ô "Thẻ")', 1)[1].strip()
    # chỉ lấy ba dòng trong khối tiêu đề (mục "Ba mức quyền" của mô tả cũng đánh số 1., 2., 3.)
    tieu_de = re.findall(r"^\d\. (.+)$", khoi(nguon, "Tiêu đề (YouTube Shorts, chọn một; dưới 100 ký tự)\n", "\n\n"), re.M)

    khung = re.search(r"chọn khung hình (.+?)\. Không chọn khung đang chuyển cảnh", nguon).group(1)
    tmpl = (ROOT / "src_build" / "upload_kit" / "2-YouTube-Shorts.tmpl.txt").read_text(encoding="utf-8")
    yt = tmpl.replace("%%MO_TA%%", mo_ta).replace("%%THE%%", the).replace("%%KHUNG_DU_PHONG%%", khung)
    # ba tiêu đề lấy từ nguồn duy nhất (soát bản dựng 3: bản mẫu từng viết cứng tiêu đề cũ)
    for k, t in enumerate(tieu_de, start=1):
        yt = yt.replace(f"%%TIEU_DE_{k}%%", t)
    tt = (KIT / "1-TikTok.txt").read_text(encoding="utf-8")
    # Không ghi tệp nào nếu còn ký hiệu giữ chỗ (QA lượt 2: %%KHUNG_DU_PHONG%% từng bị thay bằng chính nó)
    for ten, text in (("2-YouTube-Shorts.txt", yt), ("1-TikTok.txt", tt), ("DANG_BAI_tieu_de_mo_ta.txt", nguon)):
        if "%%" in text:
            sys.exit(f"{ten} còn ký hiệu giữ chỗ %%...%%: điền trước khi dựng bộ đăng bài")
    (KIT / "2-YouTube-Shorts.txt").write_text(yt, encoding="utf-8")

    tt_mo_ta = tt.split("----------------------------------------\n")[1].strip()

    loi = []
    for t in tieu_de:
        if len(t) > 100:
            loi.append(f"tiêu đề YouTube dài {len(t)} > 100: {t}")
    if len(mo_ta) > 5000:
        loi.append(f"mô tả YouTube dài {len(mo_ta)} > 5000")
    if len(the) > 500:
        loi.append(f"thẻ YouTube dài {len(the)} > 500")
    if len(tt_mo_ta) > 4000:
        loi.append(f"mô tả TikTok dài {len(tt_mo_ta)} > 4000")
    for ten, text in (("YouTube", yt), ("TikTok", tt)):
        for m in CAM.finditer(text):
            loi.append(f"{ten}: ký tự nên tránh U+{ord(m.group()):04X} ở vị trí {m.start()}")

    shutil.copyfile(ROOT / VIDEO, KIT / VIDEO)
    for dst, src in ANH.items():
        shutil.copyfile(ROOT / src, KIT / dst)
    print(f"tiêu đề YouTube: {[len(t) for t in tieu_de]} ký tự; mô tả YouTube {len(mo_ta)}; thẻ {len(the)}; mô tả TikTok {len(tt_mo_ta)}")
    print("DANG_BAI/:", ", ".join(sorted(p.name for p in KIT.iterdir())))
    print("lỗi:", loi or "không")


if __name__ == "__main__":
    main()
