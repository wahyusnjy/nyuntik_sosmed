#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/config.py
Konfigurasi global: load config.json dan PLATFORM_CONFIG.
"""

import json
import os
import sys

# ─── Path config.json selalu dari root project ───────────────────────────────
_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH  = os.path.join(_ROOT, "config.json")


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print(f"[ERROR] config.json tidak ditemukan di: {CONFIG_PATH}")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CONFIG   = load_config()
SETTINGS = CONFIG.get("settings", {})
COMMENTS = CONFIG.get("comments", ["Keren!"])

SLEEP_MIN       = SETTINGS.get("sleep_min", 2)
SLEEP_MAX       = SETTINGS.get("sleep_max", 5)
TIMEOUT         = SETTINGS.get("timeout", 15)
COMMENT_TIMEOUT = SETTINGS.get("comment_timeout", 20)
MAX_RETRIES     = SETTINGS.get("max_retries", 3)
OFFSET_RANGE    = SETTINGS.get("click_offset_range", 5)

# ─── Platform Config ──────────────────────────────────────────────────────────
PLATFORM_CONFIG = {
    "instagram": {
        "package":        "com.instagram.android",
        "like_id":        "com.instagram.android:id/row_feed_button_like",
        "comment_id":     "com.instagram.android:id/row_feed_button_comment",
        "comment_box_id": "com.instagram.android:id/layout_comment_thread_edittext",
        "post_btn_id":    "com.instagram.android:id/layout_comment_thread_post_button_click_area",
        "profile_tab_id": "com.instagram.android:id/tab_avatar",
        "switch_acc_id":  "com.instagram.android:id/action_bar_title",
        "url_pattern":    r"instagram\.com",
    },
    "threads": {
        "package":        "com.instagram.barcelona",
        "like_id":        "com.instagram.barcelona:id/like_button",
        "comment_id":     "com.instagram.barcelona:id/reply_button",
        "comment_box_id": "com.instagram.barcelona:id/reply_compose_text",
        "post_btn_id":    "com.instagram.barcelona:id/send_button",
        "profile_tab_id": "com.instagram.barcelona:id/tab_profile",
        "switch_acc_id":  "com.instagram.barcelona:id/username",
        "url_pattern":    r"threads\.net",
    },
    "youtube": {
        "package":        "com.google.android.youtube",
        "like_id":        "com.google.android.youtube:id/like_button",
        "comment_id":     "com.google.android.youtube:id/add_comment_button",
        "comment_box_id": "com.google.android.youtube:id/comment_composer_input",
        "post_btn_id":    "com.google.android.youtube:id/submit_text_button",
        "profile_tab_id": "com.google.android.youtube:id/thumbnail_layout",
        "switch_acc_id":  "com.google.android.youtube",
        "switch_acc_desc": "Switch account",
        "url_pattern":    r"(youtube\.com|youtu\.be)",
    },
    "snackvideo": {
        "package":        "com.kwai.bulldog",
        "like_id":        "com.kwai.bulldog.basis:id/like_icon",
        "comment_id":     "com.kwai.bulldog.basis:id/comment_icon",
        "comment_box_id": "com.kwai.bulldog.basis:id/normal_editor_layout",
        "comment_editor_id": "com.kwai.bulldog.basis:id/editor",
        "post_btn_id":    "com.kwai.bulldog.basis:id/finish_button",
        "profile_tab_id": "com.kwai.bulldog.basis:id/profile_tab",
        "switch_acc_id":  "com.kwai.bulldog.basis:id/username_text",
        "back_btn_id":    "com.kwai.bulldog.basis:id/inside_stream_back_btn",
        "profile_footer_id": "com.kwai.bulldog.basis:id/id_home_bottom_tab_me",
        "user_id_id":     "com.kwai.bulldog.basis:id/tv_user_id",
        "url_pattern":    r"kwai\.com|snackvideo",
    },
    "facebook": {
        "package":        "com.facebook.katana",
        "like_id":        "com.facebook.katana:id/reaction_button",
        "comment_id":     "com.facebook.katana:id/comment_button",
        "comment_box_id": "com.facebook.katana:id/composer_text_input",
        "post_btn_id":    "com.facebook.katana:id/send_button",
        "profile_tab_id": "com.facebook.katana:id/tab_icon",
        "switch_acc_id":  "com.facebook.katana:id/account_switcher_chevron",
        "url_pattern":    r"facebook\.com|fb\.com|fb\.watch",
    },
}
