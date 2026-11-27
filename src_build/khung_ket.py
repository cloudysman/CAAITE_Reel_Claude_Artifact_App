"""Khung kết CAAITE (logo vẽ dần, chữ CAAITE, liên hệ, nút Bình luận), lấy từ reel GLM-5.4 (src_build/tao_canh.py, cảnh 07).

Dùng chung tiền tố id f07-; cảnh dùng khung này đặt lại tiền tố bằng doi_tien_to().
"""

KET_LOGO = """
    <img id="f07-bloom" src="assets/derived/star-bloom-900.png" alt="" />
    <div id="f07-logo">
      <svg class="f07-part" id="f07-swoosh-line" viewBox="55563 59502 507237 364451"><path pathLength="1" d="M271272 121023 C271272 121023 123952 128531 69469 216594 C65532 222957 63627 229193 63500 235428 L63500 236574 C65151 330872 480822 406464 549275 418299 C495300 408882 224790 357342 117221 256808 C59563 202850 271272 121023 271272 121023 Z M549275 418299 C555371 419317 558800 419953 558800 419953 C558800 419953 555498 419444 549275 418299 Z"/></svg>
      <svg class="f07-part" id="f07-swoosh" viewBox="55563 59502 507237 364451"><path d="M271272 121023 C271272 121023 123952 128531 69469 216594 C65532 222957 63627 229193 63500 235428 L63500 236574 C65151 330872 480822 406464 549275 418299 C495300 408882 224790 357342 117221 256808 C59563 202850 271272 121023 271272 121023 Z M549275 418299 C555371 419317 558800 419953 558800 419953 C558800 419953 555498 419444 549275 418299 Z"/></svg>
      <svg class="f07-part" id="f07-leg-left" viewBox="55563 59502 507237 364451"><path d="M266446 164545 L177546 293967 C186690 299312 196215 304530 206121 309365 L284099 195087 Z M162052 321837 C162052 321837 156337 335072 161544 351361 L168529 367523 L191770 333417 C181483 329600 171577 325654 162179 321709 Z"/></svg>
      <svg class="f07-part" id="f07-leg-inner" viewBox="55563 59502 507237 364451"><path d="M346202 339526 L247777 194705 L266319 164800 L400431 364341 L397129 364341 C375920 364214 356489 354669 346202 339653 Z"/></svg>
      <svg class="f07-part" id="f07-leg-right" viewBox="55563 59502 507237 364451"><path d="M288544 163527 L409702 338380 C420370 353651 440182 363196 461772 363196 L465582 363196 L341884 184525 C332994 171672 316230 163654 298196 163654 Z"/></svg>
      <svg class="f07-part" id="f07-crossbar" viewBox="55563 59502 507237 364451"><path d="M289814 285695 L302133 285823 L320929 313310 L229489 313056 C242824 294222 265938 283659 289814 285568 Z"/></svg>
      <svg class="f07-part" id="f07-star" viewBox="55563 59502 507237 364451"><path d="M286385 63629 C286385 63629 290830 84627 297942 91626 C304673 98371 324485 101934 324485 101934 C324485 101934 304927 106515 298196 113387 C291338 120387 286766 140621 286766 140621 C286766 140621 283083 119750 276098 112751 C269113 105752 248666 102189 248666 102189 C248666 102189 269113 98498 275971 91499 C282829 84500 286385 63502 286385 63502 Z"/></svg>
    </div>
    <div id="f07-streak"></div>
"""

KET_CSS = """
    #root #f07-bloom { position: absolute; left: 451px; top: 1122px; width: 900px; height: 900px; opacity: 0; }
    #root #f07-logo { position: absolute; left: 400px; top: 1480px; width: 1100px; height: 790px; }
    #root .f07-part { position: absolute; left: 0; top: 0; width: 1100px; height: 790px; overflow: visible; }
    #root .f07-part path { fill: #ffffff; }
    #root #f07-swoosh-line path { fill: none; stroke: #ffffff; stroke-width: 1400; stroke-linejoin: round; stroke-dasharray: 1; stroke-dashoffset: 1; }
    #root #f07-swoosh path { fill-opacity: 0; }
    #root #f07-star { transform-origin: 45.54% 11.68%; }
    #root #f07-streak { position: absolute; left: 790px; top: 1570px; width: 240px; height: 4px; border-radius: 4px; background: linear-gradient(90deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.95) 50%, rgba(255, 255, 255, 0) 100%); opacity: 0; }
    #root #f07-cmt { position: absolute; left: 351px; top: 800px; height: 104px; box-sizing: border-box; padding: 0 40px 0 30px; gap: 18px; font-size: 48px; font-weight: 600; line-height: 60px; color: #2f55d4; background: #ffffff; border: 2px solid #ffffff; box-shadow: 0 16px 36px rgba(18, 20, 58, 0.22); transform-origin: 50% 50%; }
    #root #f07-bubble { width: 60px; height: 57px; display: block; color: #2f55d4; flex: none; }
    #root .f07-dot { fill: #ffffff; }
    #root .f07-mask { position: absolute; left: 72px; overflow: hidden; white-space: nowrap; }
    #root .f07-mask > span { display: inline-block; }
    #root #f07-m-kicker { top: 556px; height: 46px; }
    #root #f07-kicker { position: static; font-size: 36px; line-height: 46px; color: #ffffff; }
    #root #f07-m-name { top: 608px; height: 150px; }
    #root #f07-name { font-size: 128px; font-weight: 600; letter-spacing: 0.02em; line-height: 150px; color: #ffffff; }
    #root #f07-m-center { top: 768px; height: 56px; }
    #root #f07-center { font-size: 42px; font-weight: 300; line-height: 56px; color: #ffffff; }
    #root #f07-m-dept { top: 832px; height: 38px; }
    #root #f07-dept { font-size: 30px; font-weight: 500; letter-spacing: 0.1em; text-transform: uppercase; color: var(--fg-soft); line-height: 38px; }
    #root .f07-contact { position: absolute; left: 72px; height: 66px; box-sizing: border-box; display: inline-flex; align-items: center; gap: 16px; padding: 0 30px; white-space: nowrap; }
    #root .f07-contact.k-glass { border-radius: 999px; }
    #root #f07-c-web { top: 906px; }
    #root #f07-c-mail { top: 984px; }
    #root #f07-c-fb { top: 1062px; }
    #root .f07-c-label { font-size: 30px; font-weight: 500; letter-spacing: 0.12em; text-transform: uppercase; color: var(--fg-soft); }
    #root .f07-c-value { font-size: 32px; font-weight: 500; color: #ffffff; }"""

KET_THAN = """
    <div class="k-chip" id="f07-cmt" data-layout-allow-overlap><svg id="f07-bubble" viewBox="0 0 38 36"><path fill="currentColor" d="M7 2 H31 C34.9 2 38 5.1 38 9 V21 C38 24.9 34.9 28 31 28 H17 L9 35 V28 H7 C3.1 28 0 24.9 0 21 V9 C0 5.1 3.1 2 7 2 Z"/><circle class="f07-dot" cx="11" cy="15" r="2.6"/><circle class="f07-dot" cx="19" cy="15" r="2.6"/><circle class="f07-dot" cx="27" cy="15" r="2.6"/></svg><span>Bình luận</span></div>
    <div class="f07-mask" id="f07-m-kicker"><span class="k-kicker" id="f07-kicker">Theo dõi</span></div>
    <div class="f07-mask" id="f07-m-name"><span id="f07-name">CAAITE</span></div>
    <div class="f07-mask" id="f07-m-center"><span id="f07-center">Trung tâm Đào tạo AI Chuyên sâu</span></div>
    <div class="f07-mask" id="f07-m-dept"><span id="f07-dept">Khoa Trí tuệ nhân tạo · PTIT</span></div>
    <div class="k-glass f07-contact" id="f07-c-web"><span class="f07-c-label">Website</span><span class="f07-c-value">ptitai.org</span></div>
    <div class="k-glass f07-contact" id="f07-c-mail"><span class="f07-c-label">Email</span><span class="f07-c-value">aicenter@ptit.edu.vn</span></div>
    <div class="k-glass f07-contact" id="f07-c-fb"><span class="f07-c-label">Fanpage</span><span class="f07-c-value">facebook.com/CAAITE</span></div>"""

KET_JS_GOC = """
      var tQ = 0.15;
      var t1 = Math.max(wt(S1, 5, 11), tQ + 0.4), t2 = Math.max(wt(S1, 9, 11), t1 + 0.3);
      var tCmt = Math.max(wt(S2, 0, 7), t2 + 0.5);
      var tK = Math.max(S2.t1, tCmt + 0.45);
      tl.fromTo("#f07-logo", { y: 0 }, { y: -12, duration: D, ease: "none" }, 0);
      tl.fromTo("#f07-q", { autoAlpha: 0, y: 24 }, { autoAlpha: 1, y: 0, duration: 0.4, ease: "power3.out" }, tQ);
      tl.fromTo("#f07-o1", { autoAlpha: 0, x: -40 }, { autoAlpha: 1, x: 0, duration: 0.36, ease: "back.out(1.3)" }, t1);
      tl.fromTo("#f07-o2", { autoAlpha: 0, x: -40 }, { autoAlpha: 1, x: 0, duration: 0.36, ease: "back.out(1.3)" }, t2);
      tl.fromTo("#f07-cmt", { autoAlpha: 0, scale: 0.6 }, { autoAlpha: 1, scale: 1, duration: 0.45, ease: "back.out(1.8)" }, tCmt);
      tl.fromTo("#f07-bubble", { rotation: -18, transformOrigin: "30% 90%" }, { rotation: 0, transformOrigin: "30% 90%", duration: 0.6, ease: "elastic.out(1, 0.45)" }, tCmt + 0.15);
      tl.fromTo("#f07-q, #f07-o1, #f07-o2, #f07-cmt", { y: 0, autoAlpha: 1 }, { y: -40, autoAlpha: 0, duration: 0.22, ease: "power2.in", stagger: 0.02, immediateRender: false }, tK);
      tl.fromTo("#f07-kicker, #f07-name, #f07-center, #f07-dept", { yPercent: 110, autoAlpha: 0 }, { yPercent: 0, autoAlpha: 1, duration: 0.6, ease: "power3.out", stagger: 0.12 }, tK + 0.3);
      tl.fromTo("#f07-swoosh-line path", { strokeDashoffset: 1, opacity: 1 }, { strokeDashoffset: 0, opacity: 1, duration: 0.7, ease: "power2.out" }, tK);
      tl.fromTo("#f07-swoosh path", { fillOpacity: 0 }, { fillOpacity: 1, duration: 0.4, ease: "power1.out" }, tK + 0.6);
      tl.to("#f07-swoosh-line path", { opacity: 0, duration: 0.3, ease: "power1.out", immediateRender: false }, tK + 0.9);
      tl.fromTo("#f07-leg-left, #f07-leg-inner, #f07-leg-right", { y: 80, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: "power3.out", stagger: 0.1 }, tK + 0.25);
      tl.fromTo("#f07-crossbar", { x: -60, opacity: 0 }, { x: 0, opacity: 1, duration: 0.35, ease: "back.out(2)" }, tK + 0.75);
      var tS = tK + 1.1;
      tl.fromTo("#f07-bloom", { opacity: 0, scale: 0.3 }, { opacity: 0.9, scale: 1.2, duration: 0.3, ease: "power2.out" }, tS);
      tl.to("#f07-bloom", { opacity: 0.3, scale: 1, duration: 0.45, ease: "power2.inOut", immediateRender: false }, tS + 0.3);
      tl.fromTo("#f07-star", { opacity: 1, scale: 0, rotation: 45 }, { opacity: 1, scale: 1.2, rotation: 0, duration: 0.35, ease: "power3.out" }, tS);
      tl.to("#f07-star", { scale: 1, duration: 0.25, ease: "power2.inOut", immediateRender: false }, tS + 0.35);
      tl.fromTo("#f07-c-web, #f07-c-mail, #f07-c-fb", { autoAlpha: 0, scale: 0.7, transformOrigin: "0% 50%" }, { autoAlpha: 1, scale: 1, transformOrigin: "0% 50%", duration: 0.5, ease: "back.out(1.4)", stagger: 0.1 }, tK + 0.5);
"""


def doi_tien_to(s: str, moi: str) -> str:
    return s.replace("f07-", moi + "-")
