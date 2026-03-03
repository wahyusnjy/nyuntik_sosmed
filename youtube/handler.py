#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
youtube/handler.py
Logic khusus YouTube: scroll until found, Like & Comment.
"""

import time
import random

import uiautomator2 as u2

from core.utils import human_click, human_sleep, get_random_comment

MAX_SCROLL_ATTEMPTS = 25


def do_like(d: u2.Device) -> bool:
    """
    Scroll ke bawah sampai menemukan tombol Like (description=='Like').
    Skip jika sudah di-like (description=='Unlike').
    """
    print(f"    [YT-Like] Mencari tombol 'Like' dengan scroll...")
    attempts = 0

    while True:
        attempts += 1

        like_el     = d(description="Like")
        already_like = d(description="Unlike")

        if already_like.exists:
            print(f"    [YT-Like] Sudah di-like, skip.")
            return True

        if like_el.exists:
            try:
                info = like_el.info
                if info.get("selected") or info.get("checked"):
                    print(f"    [YT-Like] Sudah di-like, skip.")
                    return True
            except Exception:
                pass
            human_click(d, like_el)
            print(f"    [YT-Like] ✓ Like berhasil (scroll ke-{attempts})")
            human_sleep()
            return True

        if attempts >= MAX_SCROLL_ATTEMPTS:
            print(f"    [YT-Like] Tombol 'Like' tidak ditemukan setelah {attempts} scroll.")
            return False

        # Scroll ke bawah dan coba lagi
        d.swipe(0.5, 0.7, 0.5, 0.3, duration=0.4)
        time.sleep(random.uniform(0.8, 1.5))


def do_comment(d: u2.Device) -> bool:
    """
    Scroll ke bawah sampai menemukan placeholder 'Add a comment...'.
    Klik → jeda 2 detik → isi teks → klik Send via XPath.
    """
    print(f"    [YT-Comment] Mencari kolom 'Add a comment...' dengan scroll...")
    comment_text = get_random_comment()
    attempts     = 0

    _SEND_XPATH = (
        '//*[@resource-id="com.google.android.youtube:id/interstitials_container"]'
        '/android.widget.FrameLayout[1]'
        '/android.view.ViewGroup[1]'
        '/android.view.ViewGroup[1]'
        '/android.widget.ImageView[1]'
    )

    while True:
        attempts += 1

        # Cari input box komentar
        box = d(text="Add a comment...")
        if not box.exists:
            box = d(description="Add a comment...")
        if not box.exists:
            box = d(resourceId="com.google.android.youtube:id/comment_composer_input")

        if box.exists:
            human_click(d, box)
            print(
                f"    [YT-Comment] Kolom ditemukan (scroll ke-{attempts}), "
                f"menunggu 2 detik..."
            )
            time.sleep(2)

            # Isi teks komentar
            try:
                box.set_text(comment_text)
                human_sleep(0.8, 1.5)
                print(f"    [YT-Comment] Teks dimasukkan: '{comment_text}'")
            except Exception:
                try:
                    d.send_keys(comment_text, clear=True)
                    human_sleep(0.8, 1.5)
                    print(f"    [YT-Comment] Teks dimasukkan (send_keys): '{comment_text}'")
                except Exception as e2:
                    print(f"    [YT-Comment] Gagal input teks: {e2}")
                    d.press("back")
                    return False

            # Klik Send via XPath
            send_el = d.xpath(_SEND_XPATH)
            if send_el.wait(timeout=5):
                send_el.click()
                human_sleep(2, 4)
                print(f"    [YT-Comment] ✓ Komentar terkirim (XPath)")
                return True

            # Fallback: description
            for desc in ["Send", "Post"]:
                btn = d(description=desc)
                if btn.exists:
                    human_click(d, btn)
                    human_sleep(2, 4)
                    print(f"    [YT-Comment] ✓ Komentar terkirim (desc='{desc}')")
                    return True

            # Fallback: keyboard
            d.send_action("search")
            human_sleep(2, 3)
            print(f"    [YT-Comment] ✓ Komentar terkirim (keyboard)")
            return True

        if attempts >= MAX_SCROLL_ATTEMPTS:
            print(
                f"    [YT-Comment] Kolom 'Add a comment...' tidak ditemukan "
                f"setelah {attempts} scroll."
            )
            return False

        # Scroll ke bawah dan coba lagi
        d.swipe(0.5, 0.7, 0.5, 0.3, duration=0.4)
        time.sleep(random.uniform(0.8, 1.5))
