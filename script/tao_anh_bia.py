"""Chép khuôn ảnh bìa của reel Unsloth, thay nội dung hai phương án cho reel Claude Ultra, đổi tên tệp xuất trong render_thumbnail.py."""
import re
import shutil
from pathlib import Path

R = Path(__file__).resolve().parents[1]
A = R.parent / "CAAITE_Reel_Unsloth_DeepSeek_V41"
s = (A / "thumbnail/thumb.html").read_text(encoding="utf-8")
s = s.replace('<div class="kicker" data-key="kicker">DeepSeek V4.1 Flash</div>', '<div class="kicker" data-key="kicker">Claude · Anthropic</div>')
s = s.replace("<title>Ảnh bìa Unsloth DeepSeek</title>", "<title>Ảnh bìa Claude Ultra</title>")
s = re.sub(r"<!--\n  Ảnh bìa dọc.*?-->", """<!--
  Ảnh bìa dọc 1080x1920 cho reel Claude Ultra, cùng loạt với ảnh bìa các reel trước. Không dùng logo Claude hay Anthropic; chữ tự dựng,
  khớp bài @claudeai 30/10/2026 và claude.com/pricing. Mọi chữ chính nằm trong dải x 60-1020, y 420-1280.
  Phương án: v1 "Bỏ giới hạn 5 giờ" (bản chính), v2 "Max 20x giờ là Ultra" (bản phụ).
  Render: python src_build/render_thumbnail.py v1 v2 --final v1 --alt v2
-->""", s, flags=re.S)
v = """<!-- V1 (bản chính): khớp câu mở đầu của video -->
  <div class="variant" id="v1">
    <div class="title" data-key="title" data-fit="944" style="top: 500px;"><span class="t-a">Bỏ giới hạn</span></div>
    <div class="title" data-key="title-b" data-fit-from="title" style="top: 672px;"><span class="t-b">5 giờ<span class="star">%%STAR%%</span></span></div>
    <div class="pcard" data-key="pcard" style="top: 892px;">
      <div class="p-row" data-key="p-row" data-fit="852" data-fit-from="p-row-2"><span class="p-who">Áp dụng:</span><span class="p-say"><b>Ultra đã xác minh</b></span></div>
      <div class="p-sep"></div>
      <div class="p-row" data-key="p-row-2" data-fit="852"><span class="p-who">Giới hạn tuần:</span><span class="p-say">vẫn còn</span></div>
      <div class="p-note" data-key="p-note" data-fit="852">Bảng giá ghi gấp 10 lần Pro mỗi tuần</div>
    </div>
  </div>

  <!-- V2 (bản phụ): đổi tên gói -->
  <div class="variant" id="v2">
    <div class="title" data-key="title" data-fit="944" style="top: 500px;"><span class="t-a">Max 20x</span></div>
    <div class="title" data-key="title-b" data-fit-from="title" style="top: 672px;"><span class="t-b">giờ là Ultra<span class="star">%%STAR%%</span></span></div>
    <div class="pcard" data-key="pcard" style="top: 892px;">
      <div class="p-row" data-key="p-row" data-fit="852" data-fit-from="p-row-2"><span class="p-who">Giá:</span><span class="p-say">200 USD/tháng</span></div>
      <div class="p-sep"></div>
      <div class="p-row" data-key="p-row-2" data-fit="852"><span class="p-who">Theo tuần:</span><span class="p-say">gấp 10 lần Pro</span></div>
      <div class="p-note" data-key="p-note" data-fit="852">Tài khoản đã xác minh không còn giới hạn 5 giờ</div>
    </div>
  </div>
</div>
"""
s, n = re.subn(r"<!-- V1 \(bản chính\).*?</div>\n  </div>\n</div>\n", lambda _: v, s, flags=re.S)
assert n == 1
(R / "thumbnail").mkdir(exist_ok=True)
(R / "thumbnail/thumb.html").write_text(s, encoding="utf-8", newline="\n")
p = R / "src_build/render_thumbnail.py"
t = p.read_text(encoding="utf-8")
t = re.sub(r'^YT_TITLE = .*$', 'YT_TITLE = "Claude bỏ giới hạn 5 giờ cho gói Ultra, nhưng không phải ai cũng được"', t, flags=re.M)
t = re.sub(r'^FINAL_NAME = .*$', 'FINAL_NAME = "CAAITE-Claude-Ultra-anh-bia.jpg"', t, flags=re.M)
p.write_text(t, encoding="utf-8", newline="\n")
for f in ("src_build/upload_kit", ):
    d = R / f
    if not d.exists():
        shutil.copytree(A / f, d)
shutil.copy(A / "DANG_BAI/1-TikTok.txt", R / "DANG_BAI/1-TikTok.txt")
print("đã tạo khuôn ảnh bìa")
