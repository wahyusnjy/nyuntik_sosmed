#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snack_video/handler.py
Logic khusus SnackVideo (Kwai/Bulldog): Like, Comment, back dari stream,
navigasi ke profil, dan ambil User ID.
"""

import uiautomator2 as u2

from core.config import PLATFORM_CONFIG, COMMENT_TIMEOUT
from core.utils  import (
    human_click, human_sleep, find_element, find_by_desc, get_random_comment
)

_CFG = PLATFORM_CONFIG["snackvideo"]


# ─── Like ─────────────────────────────────────────────────────────────────────
def do_like(d: u2.Device) -> bool:
    """Klik tombol Like SnackVideo."""
    like = find_element(d, _CFG["like_id"])
    if like is None:
        like = find_by_desc(d, "Like")

    if like is None:
        print(f"    [SV-Like] Tombol tidak ditemukan")
        return False

    try:
        info = like.info
        if info.get("selected") or info.get("checked"):
            print(f"    [SV-Like] Sudah di-like, skip.")
            return True
    except Exception:
        pass

    human_click(d, like)
    print(f"    [SV-Like] ✓ Like berhasil")
    human_sleep()
    return True


# ─── Comment ──────────────────────────────────────────────────────────────────
def do_comment(d: u2.Device) -> bool:
    """Klik ikon comment → ketik teks → Send."""
    comment_btn = find_element(d, _CFG["comment_id"])
    if comment_btn is None:
        comment_btn = find_by_desc(d, "Comment")
    if comment_btn is None:
        print(f"    [SV-Comment] Tombol comment tidak ditemukan")
        return False

    print(f"    [SV-Comment] Tombol comment ditemukan")
    human_click(d, comment_btn)
    human_sleep(1.5, 3)

    comment_box = find_element(d, _CFG["comment_box_id"], timeout=COMMENT_TIMEOUT)
    comment_editor = find_element(d, _CFG["comment_editor_id"], timeout=COMMENT_TIMEOUT)
    comment_text = get_random_comment()
    if comment_box is None:
        print(f"    [SV-Comment] comment box tidak ditemukan")
        screen_size = d.window_size()
        d.click(screen_size[0] // 2, int(screen_size[1] * 0.85))
        human_sleep(1, 2)
        comment_box = find_element(d, _CFG["comment_box_id"], timeout=5)

    if comment_box.exists:
        print(f"    [SV-Comment] comment box ditemukan")
        comment_box.click()
        human_sleep(0.5, 1)

    print(f"    [SV-Comment] Processing with comment {comment_text}")
    try:

        if comment_editor is None:
            print(f"    [SV-Comment] Input box tidak ditemukan")
            print(f"    [SV-Comment] Trying alternative") # Aktifkan keyboard khusus u2
            d.send_keys(comment_text)
            human_sleep(0.5, 1)
        else:
            comment_editor.set_text(comment_text)
    except Exception:
        d.send_keys(comment_text, clear=True)

    human_sleep(1, 2)
    print(f"    [SV-Comment] Mengetik: '{comment_text}'")

    post_btn = find_element(d, _CFG["post_btn_id"], timeout=5)
    if post_btn is None:
        post_btn = find_by_desc(d, "Send")
    if post_btn is None:
        post_btn = find_by_desc(d, "Post")

    if post_btn:
        human_click(d, post_btn)
        human_sleep(2, 4)
        print(f"    [SV-Comment] ✓ Komentar terkirim")
        d.press("back")
        return True

    d.send_action("search")
    human_sleep(2, 3)
    print(f"    [SV-Comment] ✓ Komentar terkirim (keyboard)")
    return True


# ─── Post-Action: Close → Buka Ulang → Profil ────────────────────────────────
def after_action(d: u2.Device) -> None:
    """
    Dipanggil setelah Like & Comment selesai.
    1. Force-stop SnackVideo agar kembali bersih
    2. Buka ulang app ke halaman utama (tanpa URL)
    3. Tap footer profile tab (id_home_bottom_tab_me)
    """
    package = _CFG["package"]

    # 1. Close app
    print(f"    [SV] Menutup app...")
    try:
        d.app_stop(package)
        print(f"    [SV] ✓ App di-close")
    except Exception as e:
        print(f"    [SV] ⚠ Gagal close app: {e}")

    human_sleep(1.5, 2)

    # 2. Buka ulang app ke halaman utama (launch tanpa intent URL)
    print(f"    [SV] Membuka ulang app...")
    try:
        d.app_start(package)
        print(f"    [SV] ✓ App dibuka ulang")
    except Exception as e:
        print(f"    [SV] ⚠ Gagal buka app: {e}")

    human_sleep(3, 5)  # Tunggu app load

    # 3. Tap tab profil di footer
    print(f"    [SV] Navigasi ke tab Profil...")
    profile_footer = find_element(d, _CFG["profile_footer_id"], timeout=8)
    if profile_footer:
        human_click(d, profile_footer)
        print(f"    [SV] ✓ Tab profil diklik")
    else:
        print(f"    [SV] ⚠ Tab profil tidak ditemukan")

    human_sleep(2, 3)


# ─── Get Username (override dari core/utils) ──────────────────────────────────
def get_username(d: u2.Device) -> str:
    """
    Ambil User ID dari halaman profil SnackVideo.
    Dipanggil setelah after_action() mengarahkan ke profile page.
    Menggunakan tv_user_id.
    """
    user_id_el = find_element(d, _CFG["user_id_id"], timeout=8)
    if user_id_el:
        try:
            uid = user_id_el.get_text() or ""
            if uid:
                print(f"    [SV] User ID: {uid}")
                return uid
        except Exception:
            pass

    print(f"    [SV] ⚠ User ID tidak ditemukan, pakai 'Unknown'")
    return "Unknown"
