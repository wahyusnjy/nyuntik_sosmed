#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
facebook/handler.py
Logic khusus Facebook: Like & Comment.

Elemen Facebook (dari dump UI aktual):
- Like (belum di-like) : "Like button. Double tap and hold to react to the comment."
- Like (sudah di-like) : "Liked button. Double tap and hold to react to the comment."  (atau "Remove Like")
- Comment input        : d(description="Write a comment…") / EditText
"""

import time
import random

import uiautomator2 as u2

from core.config import PLATFORM_CONFIG, COMMENT_TIMEOUT
from core.utils  import (
    human_click, human_sleep, find_element, find_by_desc, get_random_comment
)

_CFG = PLATFORM_CONFIG["facebook"]
MAX_SCROLL_ATTEMPTS = 20

# Description persis tombol Like Facebook (belum di-like)
_LIKE_DESC   = ["Like", "reaction"]

# Description saat sudah di-like (FB ubah dari "Like" → "Liked")
_LIKED_DESC  = "reaction"


# ─── Like ─────────────────────────────────────────────────────────────────────
def do_like(d: u2.Device) -> bool:
    """
    Scroll ke bawah sampai menemukan tombol Like Facebook.
    Cek dulu apakah sudah di-like via description 'Liked button...'.
    """
    print(f"    [FB-Like] Mencari tombol Like dengan scroll...")
    attempts = 0

    while True:
        attempts += 1

        # ── Sudah di-like? ──────────────────────────────────────────────────
        if d(descriptionContains=_LIKED_DESC).exists:
            print(f"    [FB-Like] Sudah di-like, skip.")
            return True
        for skip_desc in ["Remove Like", "Remove like", "Unlike","reactions"]:
            if d(descriptionContains=skip_desc).exists:
                print(f"    [FB-Like] Sudah di-like ({skip_desc}), skip.")
                return True

        # ── Tombol Like (belum di-like) ─────────────────────────────────────
        for like_desc in _LIKE_DESC: 
            like_el = d(descriptionContains=like_desc)
            if d(descriptionContains=like_desc).exists:
                human_click(d, like_el)
                print(f"    [FB-Like] ✓ Like berhasil (scroll ke-{attempts})")
                human_sleep()
                return True

        # Fallback: cari via descriptionContains (partial) atau resourceId
        like_el = find_element(d, _CFG["like_id"], timeout=1)
        if like_el is not None:
            try:
                info = like_el.info
                desc = info.get("contentDescription", "")
                # Sudah di-like kalau desc-nya mulai dengan "Liked"
                if desc.lower().startswith("liked"):
                    print(f"    [FB-Like] Sudah di-like (resourceId check), skip.")
                    return True
            except Exception:
                pass
            human_click(d, like_el)
            print(f"    [FB-Like] ✓ Like berhasil via resourceId (scroll ke-{attempts})")
            human_sleep()
            return True

        if attempts >= MAX_SCROLL_ATTEMPTS:
            print(f"    [FB-Like] Tombol Like tidak ditemukan setelah {attempts} scroll.")
            return False

        d.swipe(0.5, 0.75, 0.5, 0.35, duration=0.5)
        time.sleep(random.uniform(0.8, 1.5))


# ─── Comment ──────────────────────────────────────────────────────────────────
def do_comment(d: u2.Device) -> bool:
    """
    Scroll ke bawah sampai menemukan area Write a comment / Comment button.
    Klik → isi teks → Send.
    """
    print(f"    [FB-Comment] Mencari kolom Comment dengan scroll...")
    comment_text = get_random_comment()
    attempts     = 0

    while True:
        attempts += 1

        # ── Coba langsung klik placeholder input (sering muncul sebelum tombol) ──
        for input_desc in ["Write a comment…", "Write a comment...", "Write a public comment…"]:
            box = d(description=input_desc)
            if box.exists:
                _type_and_send(d, box, comment_text)
                return True

        # ── Cari via resourceId composer ───────────────────────────────────
        box = find_element(d, _CFG["comment_box_id"], timeout=1)
        if box is not None:
            _type_and_send(d, box, comment_text)
            return True

        # ── Cari tombol Comment → klik → cari box ──────────────────────────
        comment_btn = find_element(d, _CFG["comment_id"], timeout=1)
        if comment_btn is None:
            for btn_desc in ["Comment", "Comment button"]:
                btn = d(description=btn_desc)
                if btn.exists:
                    comment_btn = btn
                    break

        if comment_btn is not None:
            human_click(d, comment_btn)
            human_sleep(2, 3)

            # Setelah klik, tunggu input box muncul
            box = find_element(d, _CFG["comment_box_id"], timeout=COMMENT_TIMEOUT)
            if box is None:
                for input_desc in ["Write a comment…", "Write a comment..."]:
                    b = d(description=input_desc)
                    if b.exists:
                        box = b
                        break
            if box is None:
                box_et = d(className="android.widget.EditText")
                if box_et.exists:
                    box = box_et

            if box is not None:
                _type_and_send(d, box, comment_text)
                return True
            else:
                print(f"    [FB-Comment] Input box tidak muncul setelah klik Comment")
                d.press("back")

        if attempts >= MAX_SCROLL_ATTEMPTS:
            print(f"    [FB-Comment] Tombol Comment tidak ditemukan setelah {attempts} scroll.")
            return False

        d.swipe(0.5, 0.75, 0.5, 0.35, duration=0.5)
        time.sleep(random.uniform(0.8, 1.5))


def _type_and_send(d: u2.Device, box, comment_text: str) -> bool:
    """Helper: klik box, isi teks, klik Send."""
    box.click()
    human_sleep(0.8, 1.5)

    try:
        box.set_text(comment_text)
    except Exception:
        d.send_keys(comment_text, clear=True)

    human_sleep(1, 2)
    print(f"    [FB-Comment] Mengetik: '{comment_text}'")

    # Klik Send — FB sering pakai XPath atau description
    for send_desc in ["Send", "Post"]:
        btn = d(description=send_desc)
        if btn.exists:
            human_click(d, btn)
            human_sleep(2, 4)
            print(f"    [FB-Comment] ✓ Komentar terkirim (desc='{send_desc}')")
            return True

    # Fallback XPath
    send_xpath = d.xpath('//*[@resource-id="com.facebook.katana:id/send_button"]')
    if send_xpath.wait(timeout=5):
        send_xpath.click()
        human_sleep(2, 4)
        print(f"    [FB-Comment] ✓ Komentar terkirim (XPath)")
        return True

    # Fallback keyboard
    d.send_action("search")
    human_sleep(2, 3)
    print(f"    [FB-Comment] ✓ Komentar terkirim (keyboard)")
    return True
