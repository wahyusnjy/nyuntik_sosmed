#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
threads/handler.py
Logic khusus Threads: Like & Comment.
"""

import uiautomator2 as u2

from core.config import PLATFORM_CONFIG, COMMENT_TIMEOUT
from core.utils  import human_click, human_sleep, find_element, find_by_desc, get_random_comment

_CFG = PLATFORM_CONFIG["threads"]


def do_like(d: u2.Device) -> bool:
    """Klik tombol Like Threads."""
    like = find_element(d, _CFG["like_id"])
    if like is None:
        like = find_by_desc(d, "Like")

    if like is None:
        print(f"    [TH-Like] Tombol tidak ditemukan")
        return False

    try:
        info = like.info
        if info.get("selected") or info.get("checked"):
            print(f"    [TH-Like] Sudah di-like, skip.")
            return True
    except Exception:
        pass

    human_click(d, like)
    print(f"    [TH-Like] ✓ Like berhasil")
    human_sleep()
    return True


def do_comment(d: u2.Device) -> bool:
    """Klik tombol Reply → ketik teks → Send."""
    # 1. Klik tombol reply / comment
    comment_btn = find_element(d, _CFG["comment_id"])
    if comment_btn is None:
        comment_btn = find_by_desc(d, "Reply")
    if comment_btn is None:
        comment_btn = find_by_desc(d, "Comment")
    if comment_btn is None:
        print(f"    [TH-Comment] Tombol reply tidak ditemukan")
        return False

    human_click(d, comment_btn)
    human_sleep(1.5, 3)

    # 2. Input box
    comment_box = find_element(d, _CFG["comment_box_id"], timeout=COMMENT_TIMEOUT)
    if comment_box is None:
        screen_size = d.window_size()
        d.click(screen_size[0] // 2, int(screen_size[1] * 0.85))
        human_sleep(1, 2)
        comment_box = find_element(d, _CFG["comment_box_id"], timeout=5)

    if comment_box is None:
        print(f"    [TH-Comment] Input box tidak ditemukan")
        d.press("back")
        return False

    comment_text = get_random_comment()
    comment_box.click()
    human_sleep(0.5, 1)

    try:
        comment_box.set_text(comment_text)
    except Exception:
        d.send_keys(comment_text, clear=True)

    human_sleep(1, 2)
    print(f"    [TH-Comment] Mengetik: '{comment_text}'")

    # 3. Klik Send
    post_btn = find_element(d, _CFG["post_btn_id"], timeout=5)
    if post_btn is None:
        post_btn = find_by_desc(d, "Post")
    if post_btn is None:
        post_btn = find_by_desc(d, "Send")

    if post_btn:
        human_click(d, post_btn)
        human_sleep(2, 4)
        print(f"    [TH-Comment] ✓ Komentar terkirim")
        return True

    d.send_action("search")
    human_sleep(2, 3)
    print(f"    [TH-Comment] ✓ Komentar terkirim (keyboard)")
    return True
