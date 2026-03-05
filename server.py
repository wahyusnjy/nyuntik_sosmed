#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py — Flask web server untuk dashboard automation.
Jalankan: python server.py
Buka browser: http://localhost:5000
"""

import os
import sys
import re
import json
import queue
import threading
import time
from datetime import datetime

from flask import Flask, jsonify, request, Response, send_from_directory

# Pastikan root project ada di path
_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _ROOT)

try:
    import adbutils
except ImportError:
    print("[ERROR] Jalankan: pip install adbutils")
    sys.exit(1)

from core.config   import PLATFORM_CONFIG
from core.reporter import print_report

app = Flask(__name__, static_folder=os.path.join(_ROOT, "web"))

# ─── Job Manager ──────────────────────────────────────────────────────────────
# Setiap job punya queue untuk stream log ke frontend via SSE
_jobs: dict[str, dict] = {}  # job_id → {"queue": Queue, "status": str, "results": []}
_jobs_lock = threading.Lock()


def _new_job_id() -> str:
    import uuid
    return str(uuid.uuid4())[:8]


# ─── ADB Devices ──────────────────────────────────────────────────────────────
@app.route("/api/devices")
def get_devices():
    """Kembalikan list device yang terhubung via ADB."""
    try:
        devices = []
        for dev in adbutils.adb.device_list():
            try:
                state = dev.get_state()
                if state == "device":
                    # Coba ambil info device (model)
                    try:
                        model = dev.shell("getprop ro.product.model").strip()
                    except Exception:
                        model = "Unknown Model"
                    devices.append({
                        "serial": dev.serial,
                        "model" : model,
                        "state" : state,
                    })
            except Exception:
                pass
        return jsonify({"devices": devices, "count": len(devices)})
    except Exception as e:
        return jsonify({"error": str(e), "devices": []}), 500


# ─── URL Validation ───────────────────────────────────────────────────────────
@app.route("/api/validate-url", methods=["POST"])
def validate_url():
    data     = request.json or {}
    platform = data.get("platform", "").lower()
    url      = data.get("url", "")

    if platform not in PLATFORM_CONFIG:
        return jsonify({"valid": False, "message": f"Platform '{platform}' tidak dikenal"})

    pattern = PLATFORM_CONFIG[platform]["url_pattern"]
    valid   = bool(re.search(pattern, url, re.IGNORECASE))
    return jsonify({"valid": valid, "message": "OK" if valid else "URL tidak cocok dengan platform"})


# ─── Run Automation ───────────────────────────────────────────────────────────
@app.route("/api/run", methods=["POST"])
def run_automation():
    """Start automation job, return job_id untuk SSE stream."""
    data     = request.json or {}
    platform = data.get("platform", "").lower()
    url      = data.get("url", "").strip()
    serials  = data.get("devices", [])

    if not platform or platform not in PLATFORM_CONFIG:
        return jsonify({"error": f"Platform tidak valid: {platform}"}), 400
    if not url:
        return jsonify({"error": "URL tidak boleh kosong"}), 400
    if not serials:
        return jsonify({"error": "Pilih minimal 1 device"}), 400

    job_id = _new_job_id()
    q      = queue.Queue()

    with _jobs_lock:
        _jobs[job_id] = {
            "queue"    : q,
            "status"   : "running",
            "results"  : [],
            "platform" : platform,
            "url"      : url,
            "devices"  : serials,
            "started_at": datetime.now().isoformat(),
        }

    # Jalankan di thread terpisah
    t = threading.Thread(
        target=_run_job,
        args=(job_id, platform, url, serials, q),
        daemon=True,
    )
    t.start()

    return jsonify({"job_id": job_id})


def _run_job(job_id: str, platform: str, url: str, serials: list, q: queue.Queue):
    """Worker thread: jalankan automation dan push log ke queue."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import uiautomator2 as u2

    # Import handler & utils
    import importlib
    handler_map = {
        "youtube"   : "youtube.handler",
        "instagram" : "instagram.handler",
        "threads"   : "threads.handler",
        "snackvideo": "snack_video.handler",
        "facebook"  : "facebook.handler",
    }

    from core.utils    import clear_recent_apps, open_url, get_current_username, do_switch_account, human_sleep
    from core.config   import PLATFORM_CONFIG
    from core.reporter import print_report

    handler_mod = importlib.import_module(handler_map[platform])
    cfg         = PLATFORM_CONFIG[platform]

    def log(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line      = f"[{timestamp}] {msg}"
        q.put({"type": "log", "data": line})

    def process_one(serial: str) -> list[dict]:
        """Jalankan satu device."""
        log(f"{'='*50}")
        log(f"[DEVICE] {serial} | {platform.upper()}")
        log(f"{'='*50}")
        device_results = []

        try:
            d = u2.connect(serial)
            d.implicitly_wait(15)
        except Exception as e:
            log(f"[ERROR] Gagal connect ke {serial}: {e}")
            return [{"device": serial, "account": "N/A", "platform": platform,
                     "url": url, "status": "FAILED", "error": str(e), "duration": 0.0}]

        account_iteration = 0
        while account_iteration < 10:
            account_iteration += 1
            log(f">>> Iterasi Akun ke-{account_iteration} [{serial}]")

            start_time      = time.time()
            status          = "FAILED"
            error_msg       = ""
            current_account = "Unknown"

            try:
                log(f"[CLEAR] Force-stop & home [{serial}]")
                clear_recent_apps(d, cfg["package"])
                human_sleep(1, 2)

                log(f"[1/3] Membuka URL [{serial}]")
                if not open_url(d, platform, url):
                    raise RuntimeError("Gagal membuka URL")
                human_sleep(2, 4)

                log(f"[2/3] Proses Like [{serial}]")
                like_ok = handler_mod.do_like(d)

                human_sleep(2, 4)

                log(f"[3/3] Proses Comment [{serial}]")
                comment_ok = handler_mod.do_comment(d)

                if hasattr(handler_mod, "after_action"):
                    log(f"[POST] After-action [{serial}]")
                    handler_mod.after_action(d)

                if hasattr(handler_mod, "get_username"):
                    current_account = handler_mod.get_username(d)
                else:
                    current_account = get_current_username(d, platform)

                log(f"[INFO] Akun: {current_account} [{serial}]")

                end_time = time.time()
                status   = "SUCCESS" if (like_ok or comment_ok) else "PARTIAL"
                if status == "PARTIAL":
                    error_msg = "Like/Comment gagal"

            except Exception as e:
                end_time  = time.time()
                status    = "FAILED"
                error_msg = str(e)
                log(f"[ERROR] {e} [{serial}]")

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
            # Push result ke queue untuk update tabel di frontend
            q.put({"type": "result", "data": result})
            log(f"[DONE] {current_account} | {status} | {duration}s [{serial}]")

            log(f"[SWITCH] Mencoba switch akun [{serial}]")
            human_sleep(2, 3)
            if not do_switch_account(d, platform):
                log(f"[INFO] Tidak ada akun lagi di {serial}")
                break
            human_sleep(3, 5)

        return device_results

    # Parallel execution
    all_results = []
    try:
        with ThreadPoolExecutor(max_workers=len(serials)) as executor:
            futures = {executor.submit(process_one, sn): sn for sn in serials}
            for future in as_completed(futures):
                sn = futures[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    log(f"[ERROR] Thread {sn}: {e}")
                    all_results.append({
                        "device": sn, "account": "N/A", "platform": platform,
                        "url": url, "status": "FAILED", "error": str(e), "duration": 0.0,
                    })
    except Exception as e:
        log(f"[FATAL] {e}")

    # Simpan ke CSV
    from core.reporter import _save_to_csv
    csv_path = _save_to_csv(all_results, datetime.now())
    log(f"[CSV] Laporan disimpan → {csv_path}")
    log(f"[DONE] Semua perangkat selesai!")

    with _jobs_lock:
        _jobs[job_id]["status"]  = "done"
        _jobs[job_id]["results"] = all_results

    q.put({"type": "done", "data": "finished"})


# ─── SSE Log Stream ───────────────────────────────────────────────────────────
@app.route("/api/stream/<job_id>")
def stream_logs(job_id: str):
    """Server-Sent Events: stream log dari job ke browser."""
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job tidak ditemukan"}), 404

    q = job["queue"]

    def generate():
        while True:
            try:
                msg = q.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg.get("type") == "done":
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─── Job Status ───────────────────────────────────────────────────────────────
@app.route("/api/job/<job_id>")
def job_status(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job tidak ditemukan"}), 404
    return jsonify({
        "status"  : job["status"],
        "results" : job["results"],
        "platform": job["platform"],
        "devices" : job["devices"],
    })


# ─── Serve Frontend ───────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(os.path.join(_ROOT, "web"), "index.html")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  Social Media Automation Dashboard")
    print("  http://localhost:9999")
    print("=" * 50)
    app.run(host="0.0.0.0", port=9999, debug=False, threaded=True)
