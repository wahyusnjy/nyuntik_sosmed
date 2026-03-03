#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/reporter.py
Cetak tabel laporan hasil eksekusi di terminal
dan simpan ke CSV di folder logs/.
"""

import os
import csv
from datetime import datetime

# ─── Lokasi folder logs ────────────────────────────────────────────────────────
_ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGS_DIR = os.path.join(_ROOT, "logs")

_CSV_HEADER = [
    "Date", "Time", "Device ID", "Account Name",
    "Platform", "URL", "Status", "Duration (sec)", "Error"
]


def _ensure_logs_dir():
    os.makedirs(_LOGS_DIR, exist_ok=True)


def _get_csv_path() -> str:
    """CSV dinamis per-hari: logs/report_YYYY-MM-DD.csv"""
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(_LOGS_DIR, f"report_{date_str}.csv")


def _save_to_csv(results: list[dict], timestamp: datetime):
    """Append hasil ke file CSV harian."""
    _ensure_logs_dir()
    csv_path    = _get_csv_path()
    file_exists = os.path.isfile(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_HEADER)

        # Tulis header hanya jika file baru
        if not file_exists:
            writer.writeheader()

        for r in results:
            writer.writerow({
                "Date"           : timestamp.strftime("%Y-%m-%d"),
                "Time"           : timestamp.strftime("%H:%M:%S"),
                "Device ID"      : r.get("device",   ""),
                "Account Name"   : r.get("account",  ""),
                "Platform"       : r.get("platform", ""),
                "URL"            : r.get("url",      ""),
                "Status"         : r.get("status",   ""),
                "Duration (sec)" : r.get("duration", 0.0),
                "Error"          : r.get("error",    ""),
            })

    return csv_path


def print_report(results: list[dict]):
    """Cetak tabel ringkasan ke terminal dan simpan ke CSV."""
    now = datetime.now()

    # ── Terminal table ─────────────────────────────────────────────────────────
    print("\n" + "=" * 75)
    print("  [RESULT SUMMARY]")
    print("=" * 75)
    print(
        f"  {'Date':<12} {'Time':<10} {'Device ID':<18} {'Account':<18} "
        f"{'Platform':<12} {'Status':<9} {'Dur':>6}"
    )
    print("-" * 75)

    success_total = 0
    failed_total  = 0

    for r in results:
        icon = "✓" if r["status"] == "SUCCESS" else ("~" if r["status"] == "PARTIAL" else "✗")
        print(
            f"  {now.strftime('%Y-%m-%d'):<12} {now.strftime('%H:%M:%S'):<10} "
            f"{r['device']:<18} {r['account']:<18} "
            f"{r['platform']:<12} {icon} {r['status']:<7} {r['duration']:>5.1f}s"
        )
        if r["status"] == "SUCCESS":
            success_total += 1
        else:
            failed_total += 1

    print("-" * 75)
    print(f"  Total SUCCESS : {success_total} | Total FAILED: {failed_total}")
    print(f"  Timestamp     : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 75)

    # Detail error di terminal
    errors = [r for r in results if r.get("error")]
    if errors:
        print("\n  [ERROR DETAILS]")
        for r in errors:
            print(f"  - {r['device']} / {r['account']}: {r['error']}")

    # ── Simpan ke CSV ──────────────────────────────────────────────────────────
    csv_path = _save_to_csv(results, now)
    print(f"\n  📄 Laporan CSV disimpan → {csv_path}")
