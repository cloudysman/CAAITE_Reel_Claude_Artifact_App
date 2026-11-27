"""Chụp tư liệu từ trang công khai "Felix's Demo Apps" (claude.ai/artifact/9j53nCVcrSdZyCHtxUZkWJ), không đăng nhập.

Trang là một artifact do Felix (kỹ sư Anthropic) đăng, bài của Anthropic trên claude.com dẫn tới; trang tự ghi
"Content is user-generated and unverified" và "They're not official Anthropic products".
Ra (tu_lieu_tai_ve/felix_demo/):
- man_hinh.png: cả màn hình nền pixel lúc vừa mở, DPR 2 (3840x2070, đã bỏ thanh tiêu đề của claude.ai).
- bieu_tuong/<ten>.png: từng biểu tượng ứng dụng, DPR 2.
- cua_so/<ten>.png: cửa sổ của từng ứng dụng (sau khi bấm biểu tượng), DPR 2.
- anh/<ten>_<i>.png: ảnh chụp ứng dụng thứ i trong cửa sổ, DPR 2, kèm chú thích trong anh/chu_thich.json.
- quay.webm: video thao tác mở lần lượt các ứng dụng (Playwright quay ở 1920x1080).
Cách dùng: python -I -X utf8 src_build/chup_felix.py
"""
import json
import re
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tu_lieu_tai_ve" / "felix_demo"
URL = "https://claude.ai/artifact/9j53nCVcrSdZyCHtxUZkWJ"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"


def khung(g):
    return [x for x in g.frames if "claudeusercontent" in x.url][0]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def main() -> None:
    for d in ("bieu_tuong", "cua_so", "anh"):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    chu_thich = {}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        # 1) ảnh tĩnh nét (DPR 2)
        c = b.new_context(user_agent=UA, locale="en-US", viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        g = c.new_page()
        g.goto(URL, wait_until="domcontentloaded", timeout=60000)
        g.wait_for_timeout(9000)
        f = khung(g)
        app = f.locator("main#app")
        app.screenshot(path=str(OUT / "man_hinh.png"))
        icons = f.locator("a.ia.k")
        ten_ung_dung = [icons.nth(i).inner_text().split("\n")[0].strip() for i in range(icons.count())]
        for i, ten in enumerate(ten_ung_dung):
            icons.nth(i).screenshot(path=str(OUT / "bieu_tuong" / f"{slug(ten)}.png"))
        for i, ten in enumerate(ten_ung_dung):
            icons.nth(i).click()
            g.wait_for_timeout(1200)
            # cửa sổ vừa mở nằm trên cùng: lấy section.win.app có z-index lớn nhất
            wid = f.evaluate("""() => { const ws = [...document.querySelectorAll('section.win.app')];
                ws.sort((a, b) => (+getComputedStyle(b).zIndex || 0) - (+getComputedStyle(a).zIndex || 0));
                return ws.length ? ws[0].id : null; }""")
            if not wid:
                print(ten, ": không thấy cửa sổ")
                continue
            w = f.locator(f"section#{wid}")
            w.screenshot(path=str(OUT / "cua_so" / f"{slug(ten)}.png"))
            nut = w.locator("button[title]").filter(has_not=w.locator(".ct"))
            tieu_de = [t for t in w.locator("button[title]").evaluate_all("els => els.map(e => e.title)") if not t.startswith("Close")]
            for k, td in enumerate(tieu_de):
                w.locator(f"button[title=\"{td}\"]").first.click()
                g.wait_for_timeout(700)
                w.locator("div.pic").screenshot(path=str(OUT / "anh" / f"{slug(ten)}_{k + 1}.png"))
                chu_thich[f"{slug(ten)}_{k + 1}"] = {"ung_dung": ten, "chu_thich": td}
            mo_ta = w.evaluate("e => (e.innerText || '').split('\\n').filter(Boolean).slice(0, 6)")
            chu_thich[slug(ten)] = {"ung_dung": ten, "cua_so": wid, "chu_trong_cua_so": mo_ta}
            print(ten, wid, len(tieu_de), "ảnh")
        c.close()
        # 2) video thao tác mở lần lượt các ứng dụng
        tmp = OUT / "_quay"
        shutil.rmtree(tmp, ignore_errors=True)
        c = b.new_context(user_agent=UA, locale="en-US", viewport={"width": 1920, "height": 1080}, device_scale_factor=1,
                          record_video_dir=str(tmp), record_video_size={"width": 1920, "height": 1080})
        g = c.new_page()
        g.goto(URL, wait_until="domcontentloaded", timeout=60000)
        g.wait_for_timeout(9000)
        f = khung(g)
        icons = f.locator("a.ia.k")
        for i in range(icons.count()):
            icons.nth(i).click()
            g.wait_for_timeout(1500)
        g.wait_for_timeout(1000)
        c.close()
        vids = list(tmp.glob("*.webm"))
        if vids:
            shutil.move(str(vids[0]), str(OUT / "quay.webm"))
        shutil.rmtree(tmp, ignore_errors=True)
        b.close()
    (OUT / "anh" / "chu_thich.json").write_text(json.dumps(chu_thich, ensure_ascii=False, indent=1), encoding="utf-8")
    print("xong:", len(list((OUT / "anh").glob("*.png"))), "ảnh ứng dụng")


if __name__ == "__main__":
    main()
