#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
instagram/handler.py
Logic khusus Instagram: get_username, Like & Comment.

Flow per-akun:
  1. Buka app Instagram ke halaman utama
  2. get_username() → ambil nama akun dari tab profil
  3. open_url() → intent ke postingan target
  4. do_like() → klik Like
  5. do_comment() → klik Comment → ketik → Post
"""

import uiautomator2 as u2

from core.config import PLATFORM_CONFIG, COMMENT_TIMEOUT
from core.utils  import (
    human_click, human_sleep, find_element, find_by_desc, get_random_comment
)

_CFG    = PLATFORM_CONFIG["instagram"]
_PKG    = _CFG["package"]


# ─── Pre-action sebelum buka URL target ──────────────────────────────────────
def pre_open_url(d: u2.Device) -> str:
    """
    Dipanggil SEBELUM open_url ke post target.
    Buka Instagram ke halaman utama → tab Profil → ambil username.
    Return: username string.
    """
    print(f"    [IG] Membuka Instagram ke halaman utama...")
    try:
        d.app_start(_PKG)          # Buka tanpa URL → Main Feed
        human_sleep(3, 5)
    except Exception as e:
        print(f"    [IG] Gagal buka app: {e}")
        return "Unknown"

    # Tap tab profil
    profile_tab = find_element(d, _CFG["profile_tab_id"], timeout=8)
    if profile_tab:
        human_click(d, profile_tab)
        human_sleep(2, 3)
        print(f"    [IG] ✓ Tab profil dibuka")
    else:
        print(f"    [IG] ⚠ Tab profil tidak ditemukan")
        return "Unknown"

    # Ambil username dari action bar
    username_el = find_element(d, _CFG["switch_acc_id"], timeout=5)
    if username_el:
        try:
            name = username_el.get_text() or "Unknown"
            print(f"    [IG] Akun aktif: {name}")
            return name
        except Exception:
            pass

    return "Unknown"


# ─── Like ─────────────────────────────────────────────────────────────────────
def do_like(d: u2.Device) -> bool:
    """Klik tombol Like Instagram. Dismiss popup jika ada."""
    # Dismiss popup/dialog (negative button)
    neg = d(resourceId="com.instagram.android:id/negative_button")
    if neg.exists:
        print(f"    [IG-Like] Dismiss popup...")
        neg.click()
        human_sleep(1, 2)

    like = find_element(d, _CFG["like_id"])
    if like is None:
        like = find_by_desc(d, "Like")

    if like is None:
        print(f"    [IG-Like] Tombol tidak ditemukan")
        return False

    try:
        info = like.info
        if info.get("selected") or info.get("checked"):
            print(f"    [IG-Like] Sudah di-like, skip.")
            return True
    except Exception:
        pass

    human_click(d, like)
    print(f"    [IG-Like] ✓ Like berhasil")
    human_sleep()
    return True


# ─── Comment ──────────────────────────────────────────────────────────────────
def do_comment(d: u2.Device) -> bool:
    """Klik ikon comment → ketik teks → klik Post."""

    # 1. Klik tombol buka kolom komentar
    comment_btn = find_element(d, _CFG["comment_id"])
    if comment_btn is None:
        comment_btn = find_by_desc(d, "Comment")
    if comment_btn is None:
        print(f"    [IG-Comment] Tombol comment tidak ditemukan")
        return False

    human_click(d, comment_btn)
    human_sleep(1.5, 3)

    # 2. Klik input box komentar
    comment_box = find_element(d, _CFG["comment_box_id"], timeout=COMMENT_TIMEOUT)
    if comment_box is None:
        # Fallback: tap area bawah layar
        w, h = d.window_size()
        d.click(w // 2, int(h * 0.85))
        human_sleep(1, 2)
        comment_box = find_element(d, _CFG["comment_box_id"], timeout=5)

    if comment_box is None:
        print(f"    [IG-Comment] Input box tidak ditemukan")
        d.press("back")
        return False

    comment_text = get_random_comment()
    comment_box.click()
    human_sleep(0.8, 1.5)

    # 3. Isi teks
    try:
        comment_box.set_text(comment_text)
    except Exception:
        d.send_keys(comment_text, clear=True)

    human_sleep(1, 2)
    print(f"    [IG-Comment] Mengetik: '{comment_text}'")

    # 4. Klik Post/Send
    post_btn = find_element(d, _CFG["post_btn_id"], timeout=5)
    if post_btn is None:
        post_btn = find_by_desc(d, "Post")
    if post_btn is None:
        post_btn = find_by_desc(d, "Send")

    if post_btn:
        post_btn.click()
        human_sleep(2, 4)
        print(f"    [IG-Comment] ✓ Komentar terkirim")
        return True

    # Fallback keyboard
    d.send_action("search")
    human_sleep(2, 3)
    print(f"    [IG-Comment] ✓ Komentar terkirim (keyboard)")
    return True
