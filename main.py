#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Entry point utama.
Routing platform → handler masing-masing folder.
Jalankan:
  python main.py youtube "https://www.youtube.com/watch?v=xxx"
  python main.py instagram "https://www.instagram.com/p/xxx/"
  python main.py threads "https://www.threads.net/@user/post/xxx"
  python main.py snackvideo "https://www.kwai.com/short-video/xxx"
"""

import sys
import re
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import uiautomator2 as u2
    import adbutils
except ImportError:
    print("[ERROR] Jalankan: pip install uiautomator2 adbutils")
    sys.exit(1)

from core.config   import PLATFORM_CONFIG
from core.utils    import (
    clear_recent_apps, open_url, get_current_username,
    do_switch_account, human_sleep
)
from core.reporter import print_report

# ─── Import handler per platform ──────────────────────────────────────────────
import youtube.handler    as yt_handler
import instagram.handler  as ig_handler
import threads.handler    as th_handler
import snack_video.handler as sv_handler
import facebook.handler   as fb_handler

HANDLERS = {
    "youtube"   : yt_handler,
    "instagram" : ig_handler,
    "threads"   : th_handler,
    "snackvideo": sv_handler,
    "facebook"  : fb_handler,
}

# ─── Thread-safe result store ─────────────────────────────────────────────────
results_lock = threading.Lock()


# ─── Detect Devices ───────────────────────────────────────────────────────────
def detect_devices() -> list[str]:
    try:
        return [d.serial for d in adbutils.adb.device_list()
                if d.get_state() == "device"]
    except Exception as e:
        print(f"[ERROR] Gagal deteksi device: {e}")
        return []


def validate_url(url: str, platform: str) -> bool:
    pattern = PLATFORM_CONFIG[platform]["url_pattern"]
    return bool(re.search(pattern, url, re.IGNORECASE))


# ─── Per-Device Task ──────────────────────────────────────────────────────────
def process_device(serial: str, platform: str, url: str) -> list[dict]:
    """Jalankan automation di 1 device, looping multi-akun."""
    print(f"\n{'='*55}")
    print(f"  [DEVICE] {serial}  |  {platform.upper()}")
    print(f"{'='*55}")

    handler      = HANDLERS[platform]
    cfg          = PLATFORM_CONFIG[platform]
    device_results = []

    try:
        d = u2.connect(serial)
        d.implicitly_wait(15)
    except Exception as e:
        print(f"  [ERROR] Gagal connect ke {serial}: {e}")
        return [{"device": serial, "account": "N/A", "platform": platform,
                 "status": "FAILED", "error": str(e), "duration": 0.0}]

    account_iteration = 0
    max_accounts      = 10

    while account_iteration < max_accounts:
        account_iteration += 1
        print(f"\n  >>> Iterasi Akun ke-{account_iteration}")

        start_time      = time.time()
        status          = "FAILED"
        error_msg       = ""
        current_account = "Unknown"

        try:
            # 0. Bersihkan & force-stop
            clear_recent_apps(d, cfg["package"])
            human_sleep(1, 2)

            # 1a. PRE-hook: buka app → profil → ambil username SEBELUM ke post
            #     Dipakai oleh Instagram (open app → navigate profile → get username)
            #     Handler yang mendukung: wajib punya fungsi pre_open_url(d) -> str
            if hasattr(handler, "pre_open_url"):
                print(f"  [PRE] Mengambil username akun aktif...")
                current_account = handler.pre_open_url(d)
                print(f"  [INFO] Akun aktif: {current_account}")
                human_sleep(1, 2)

            # 1b. Buka URL target via Intent
            print(f"  [1/4] Membuka URL di {platform}...")
            if not open_url(d, platform, url):
                raise RuntimeError("Gagal membuka URL")
            human_sleep(2, 4)

            # 2. Like
            print(f"  [2/4] Proses Like...")
            like_ok = handler.do_like(d)
            human_sleep()

            # 3. Comment
            print(f"  [3/4] Proses Comment...")
            comment_ok = handler.do_comment(d)

            # 4. POST-hook (opsional): SnackVideo close → buka ulang → ke profil
            if hasattr(handler, "after_action"):
                print(f"  [POST] Menjalankan post-action...")
                handler.after_action(d)

            # 5. Ambil username (jika belum diambil di PRE-hook)
            if current_account == "Unknown":
                if hasattr(handler, "get_username"):
                    current_account = handler.get_username(d)
                else:
                    current_account = get_current_username(d, platform)
                print(f"  [INFO] Akun aktif: {current_account}")

            end_time = time.time()
            status   = "SUCCESS" if (like_ok or comment_ok) else "PARTIAL"
            if status == "PARTIAL":
                error_msg = "Like/Comment gagal"

        except Exception as e:
            end_time  = time.time()
            status    = "FAILED"
            error_msg = str(e)
            print(f"  [ERROR] {e}")

        duration = round(end_time - start_time, 2)
        result   = {
            "device"  : serial,
            "account" : current_account,
            "platform": platform,
            "url"     : url,
            "status"  : status,
            "error"   : error_msg,
            "duration": duration,
        }
        device_results.append(result)
        print(f"  [DONE] Akun '{current_account}' | {status} | {duration}s")

        # 5. Switch akun
        print(f"  [4/4] Switch akun...")
        human_sleep()
        if not do_switch_account(d, platform):
            print(f"  [INFO] Tidak ada akun lagi di {serial}.")
            break
        human_sleep(3, 6)

    return device_results


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Mobile Social Media Automation Agent")
    print("  Powered by UIAutomator2")
    print("=" * 55)

    platforms   = list(PLATFORM_CONFIG.keys())
    url_example = {
        "instagram" : "https://www.instagram.com/p/XXXXX/",
        "threads"   : "https://www.threads.net/@user/post/XXXXX",
        "youtube"   : "https://www.youtube.com/watch?v=XXXXX",
        "snackvideo": "https://www.kwai.com/short-video/XXXXX",
        "facebook"  : "https://www.facebook.com/permalink.php?story_fbid=XXXXX",
    }

    # ── Parse sys.argv ─────────────────────────────────────────────────────────
    # Format: python main.py <platform> <url> [device_id]
    target_device = None

    if len(sys.argv) >= 3:
        platform      = sys.argv[1].strip().lower()
        url           = sys.argv[2].strip()
        target_device = sys.argv[3].strip() if len(sys.argv) >= 4 else None
    else:
        print(f"\n  Platform : {' | '.join(platforms)}")
        print(f"  Format   : <platform> <url> [device_id]")
        print(f"  Contoh   : instagram https://www.instagram.com/p/XXX/")
        print(f"             instagram https://www.instagram.com/p/XXX/ emulator-5554")
        print(f"  {'─'*51}")
        while True:
            raw   = input("  >> ").strip()
            parts = raw.split(maxsplit=2)
            if len(parts) >= 2:
                platform = parts[0].lower()
                url      = parts[1]
                target_device = parts[2] if len(parts) == 3 else None
                break
            print("  [!] Format salah. Contoh: instagram https://...")

    # ── Validasi platform ──────────────────────────────────────────────────────
    if platform not in HANDLERS:
        print(f"\n  [ERROR] Platform '{platform}' tidak dikenal.")
        print(f"  Valid  : {' | '.join(platforms)}")
        sys.exit(1)

    # ── Validasi URL ───────────────────────────────────────────────────────────
    while not validate_url(url, platform):
        print(f"  [!] URL tidak cocok dengan {platform.upper()}.")
        print(f"  Contoh : {url_example[platform]}")
        url = input("  URL    : ").strip()

    # ── Deteksi devices ────────────────────────────────────────────────────────
    print("\n  Mendeteksi perangkat ADB...")
    all_devices = detect_devices()
    if not all_devices:
        print("  [ERROR] Tidak ada perangkat terdeteksi.")
        sys.exit(1)

    print(f"  Perangkat tersedia: {', '.join(all_devices)}")

    # ── Filter device jika device_id diberikan ─────────────────────────────────
    if target_device:
        if target_device not in all_devices:
            print(f"\n  [ERROR] Device '{target_device}' tidak ditemukan.")
            print(f"  Tersedia: {', '.join(all_devices)}")
            sys.exit(1)
        devices = [target_device]
        print(f"  Target device: {target_device}")
    else:
        devices = all_devices
        print(f"  Target device: semua ({len(devices)} perangkat)")

    # ── Konfirmasi ─────────────────────────────────────────────────────────────
    print(f"\n  {'─'*51}")
    print(f"  Platform  : {platform.upper()}")
    print(f"  URL       : {url}")
    print(f"  Perangkat : {', '.join(devices)}")
    print(f"  {'─'*51}")
    if input("\n  Jalankan? (y/n): ").strip().lower() != "y":
        print("  Dibatalkan.")
        sys.exit(0)

    # ── Eksekusi paralel ───────────────────────────────────────────────────────
    print(f"\n  Memulai eksekusi pada {len(devices)} perangkat...\n")
    start_all         = time.time()
    collected_results = []

    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        futures = {
            executor.submit(process_device, sn, platform, url): sn
            for sn in devices
        }
        for future in as_completed(futures):
            sn = futures[future]
            try:
                with results_lock:
                    collected_results.extend(future.result())
            except Exception as e:
                print(f"[ERROR] Thread {sn}: {e}")
                with results_lock:
                    collected_results.append({
                        "device": sn, "account": "N/A", "platform": platform,
                        "url": url, "status": "FAILED",
                        "error": str(e), "duration": 0.0,
                    })

    print(f"\n  Selesai dalam {round(time.time() - start_all, 2)}s")
    print_report(collected_results)


if __name__ == "__main__":
    main()


