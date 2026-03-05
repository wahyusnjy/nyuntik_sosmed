#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/utils.py
Fungsi-fungsi utility yang dipakai semua platform.
"""

import time
import random

import uiautomator2 as u2

from core.config import (
    SLEEP_MIN, SLEEP_MAX, TIMEOUT, COMMENTS, OFFSET_RANGE, PLATFORM_CONFIG
)


def human_sleep(min_s: float = None, max_s: float = None):
    """Tidur durasi acak menyerupai manusia."""
    t = random.uniform(min_s or SLEEP_MIN, max_s or SLEEP_MAX)
    time.sleep(t)


def human_click(d: u2.Device, element, offset: int = None):
    """Klik elemen dengan sedikit offset koordinat agar mirip manusia."""
    off = offset or OFFSET_RANGE
    bounds = element.info.get("bounds", {})
    cx = (bounds.get("left", 0) + bounds.get("right", 0)) // 2
    cy = (bounds.get("top",  0) + bounds.get("bottom", 0)) // 2
    cx += random.randint(-off, off)
    cy += random.randint(-off, off)
    d.click(cx, cy)


def find_element(d: u2.Device, resource_id: str, timeout: int = None):
    """Cari elemen by resourceId, return element atau None."""
    t = timeout or TIMEOUT
    try:
        el = d(resourceId=resource_id)
        if el.wait(timeout=t):
            return el
    except Exception:
        pass
    return None

def find_by_xpath(d: u2.Device, xpath: str, timeout: int = None):
    """Cari elemen by xpath, return element atau None."""
    t = timeout or TIMEOUT
    try:
        el = d.xpath(xpath)
        if el.wait(timeout=t):
            return el
    except Exception:
        pass
    return None


def find_by_desc(d: u2.Device, desc: str, timeout: int = None):
    """Cari elemen by content-description."""
    t = timeout or TIMEOUT
    try:
        el = d(description=desc)
        if el.wait(timeout=t):
            return el
    except Exception:
        pass
    return None

def find_by_desc_contains(d: u2.Device, desc: str, timeout: int = None):
    """Cari elemen by content-description."""
    t = timeout or TIMEOUT
    try:
        el = d(descriptionContains=desc)
        if el.wait(timeout=t):
            return el
    except Exception:
        pass
    return None


def get_random_comment() -> str:
    return random.choice(COMMENTS)


def get_current_username(d: u2.Device, platform: str) -> str:
    """Ambil username akun aktif dari layar profil (generic)."""
    cfg = PLATFORM_CONFIG[platform]
    print(f"     Closing apps {platform}...")
    clear_recent_apps(d, cfg["package"])
    human_sleep(1, 2)

    print(f"     Membuka Ulang {platform}...")
    d.app_start(cfg["package"])
    human_sleep(2, 4)
    try:
        profile_tab = find_element(d, cfg["profile_tab_id"], timeout=5)
        alternative_profile_tab = find_by_desc_contains(d, cfg["profile_tab_id"], timeout=5)
        if profile_tab:
            print(f"     Find tab profile  on primary tab...")
            human_click(d, profile_tab)
            human_sleep(1.5, 3)
        elif alternative_profile_tab :
            print(f"     Find tab profile on alternative 1 ...")
            human_click(d, alternative_profile_tab)
            human_sleep(1.5, 3)

        username_el = find_element(d, cfg.get("switch_acc_id"), timeout=5)
        username_el_xpath = find_by_xpath(d, cfg.get("switch_acc_id"), timeout=5)
        if username_el:
            print(f"     Find username on primary 1 tab...")
            return username_el.get_text()
        elif username_el_xpath: 
            print(f"     Find username on alternative 1 tab...")
            return username_el_xpath.get_text() or username_el_xpath.get("contentDescription") or "Unknown"
    except Exception:
        pass
    return "Unknown"


def open_url(d: u2.Device, platform: str, url: str) -> bool:
    """Buka URL langsung via ADB Intent ke aplikasi target."""
    cfg     = PLATFORM_CONFIG[platform]
    package = cfg["package"]
    try:
        d.app_start(
            package,
            activity="android.intent.action.VIEW",
            action="android.intent.action.VIEW",
            data=url,
            stop=False,
        )
        human_sleep(3, 5)
        return True
    except Exception:
        try:
            d.shell(f"am start -a android.intent.action.VIEW -d '{url}' {package}")
            human_sleep(3, 5)
            return True
        except Exception as e:
            print(f"    [open_url] Gagal: {e}")
            return False


def do_switch_account(d: u2.Device, platform: str) -> bool:
    """Navigasi ke profil dan switch ke akun berikutnya."""
    cfg = PLATFORM_CONFIG[platform]
    try:
        profile_tab = find_element(d, cfg["profile_tab_id"], timeout=5)
        if profile_tab:
            human_click(d, profile_tab)
            human_sleep(2, 3)
        else:
            d.press("back")
            human_sleep(1)

        switch_btn = find_element(d, cfg["switch_acc_id"], timeout=5)
        if switch_btn is None:
            switch_btn = find_by_xpath(d,cfg["switch_acc_xpath"], timeout=5)

        if switch_btn:
            human_click(d, switch_btn)
            human_sleep(2, 3)

            acc_list = d(scrollable=True)
            if acc_list.exists:
                acc_list.scroll.to(
                    resourceId="com.instagram.android:id/row_user_header_username"
                )

            # IG
            all_accounts = d(
                resourceId="com.instagram.android:id/row_user_header_username"
            )
            # Facebook
            other_account = find_by_desc_contains(d,"Other accounts",timeout=5)
            if all_accounts.count >= 2:
                human_click(d, all_accounts[1])
                human_sleep(3, 5)
                print(f"    [Switch] ✓ Akun berhasil diganti")
                return True
            elif other_account.exists:
                # facebook - klik "Other accounts"
                other_account.click()
                human_sleep(1, 2)

                recycler = d(className="androidx.recyclerview.widget.RecyclerView")
                view_groups = recycler.child(className="android.view.ViewGroup")
                total = view_groups.count
                print(f"    [Switch-FB] Total akun ditemukan: {total}")

                # Kumpulkan semua nama akun dari contentDescription cucu
                account_names = []
                for i in range(total):
                    cucu = view_groups[i].child(className="android.view.ViewGroup")
                    desc = cucu.info.get("contentDescription", "") or ""
                    account_names.append(desc)
                    print(f"    [Switch-FB] Akun index {i}: {desc}")

                # Index 0 = akun yang sedang aktif
                current_account = account_names[0] if account_names else "Unknown"
                print(f"    [Switch-FB] Akun terkini: {current_account}")

                # Klik akun berikutnya (index 1) untuk switch
                if total >= 2:
                    view_groups[1].click()
                    human_sleep(3, 5)
                    print(f"    [Switch-FB] ✓ Berhasil switch ke: {account_names[1]}")
                    return True
                else:
                    print(f"    [Switch-FB] Tidak ada akun lain untuk diganti")
                    d.press("back")
                    return False
            
            else:
                print(f"    [Switch] Tidak ada akun lain untuk diganti")
                d.press("back")
                return False
        else:
            print(f"    [Switch] Tombol switch tidak ditemukan")
            return False

    except Exception as e:
        print(f"    [Switch] Error: {e}")
        return False


def clear_recent_apps(d: u2.Device, package: str):
    """Kembali ke home lalu force-stop app agar mulai bersih."""
    print(f"  [CLEAR] Membersihkan recent apps...")
    try:
        d.press("home")
        time.sleep(0.8)
    except Exception as e:
        print(f"  [CLEAR] Warning home: {e}")

    try:
        d.app_stop(package)
        print(f"  [CLEAR] ✓ App '{package}' di-force stop")
        time.sleep(1)
    except Exception as e:
        print(f"  [CLEAR] Warning force-stop: {e}")
