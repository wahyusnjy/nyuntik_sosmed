# Mobile Social Media Automation Agent (UI Automator2)

## 🎯 Project Goal
Membangun skrip otomatisasi Android (`main.py`) menggunakan library `uiautomator2` untuk melakukan interaksi otomatis (Like, Comment, Repost) pada aplikasi: **Instagram, Threads, YouTube, dan SnackVideo**.

## 🛠️ Environment Setup
- **Language:** Python 3.x
- **Library:** `uiautomator2`, `adbutils`
- **Device:** Android Emulator (LDPlayer/BlueStacks) atau HP Fisik dengan USB Debugging ON.
- **Connection:** Terhubung via ADB (Android Debug Bridge).

## 🚀 Workflow Logic (The Instructions)
Agen harus mengikuti alur kerja berikut:

1.  **Direct Intent Execution:**
    * Ambil URL dari `sys.argv`.
    * Gunakan perintah ADB shell intent untuk langsung membuka aplikasi terkait tanpa melewati browser.
    * Contoh: `d.app_start("com.instagram.android", action="android.intent.action.VIEW", data=url)`

2.  **Element Interaction (Resource-ID based):**
    * Cari komponen **Like** (Biasanya ID: `like_button` atau deskripsi: `Like`).
    * Cari komponen **Comment**, klik, ketik teks, dan klik **Post/Send**.
    * Cari tombol **Share/Repost** jika diminta.

3.  **Account Switching:**
    * Setelah interaksi selesai, navigasi ke tab **Profile**.
    * Klik pada nama akun (top bar) untuk memicu menu 'Switch Account'.
    * Pilih akun berikutnya secara berurutan.
    * *Catatan:* Jika akun habis, stop skrip.

4.  **Error Handling & Reporting:**
    * Gunakan `d.exists(resourceId="...")` untuk validasi elemen.
    * Buat variabel counter `success_count` dan `failed_count`.
    * Output akhir di terminal harus berupa tabel sederhana:
      ```text
      [RESULT SUMMARY]
      - App: Instagram | Link: [URL] | Acc: User_1 | Status: SUCCESS
      - App: YouTube   | Link: [URL] | Acc: User_1 | Status: FAILED (Timeout)
      --------------------------------------------------------------
      Total Success: X | Total Failed: Y
      ```

## 🧩 Element Reference (Hint for Agent)
Agen perlu mencari ID berikut (atau yang serupa di update terbaru):
- **Instagram:** `com.instagram.android:id/row_feed_button_like`
- **YouTube:** `com.google.android.youtube:id/like_button`
- **SnackVideo:** `com.kwai.snackvideo:id/like_button`
- **Threads:** `com.instagram.barcelona:id/like_button`

## ⚠️ Anti-Detection Rules
- Berikan jeda `time.sleep(random.randint(2, 5))` di antara setiap klik.
- Gunakan `d.click(x, y)` dengan sedikit offset koordinat agar klik tidak selalu di titik yang sama persis (lebih mirip manusia).
- Jangan scroll terlalu cepat; gunakan `d.swipe(fx, fy, tx, ty, duration=0.5)`.

## 📂 Project Structure
```text
.
├── .venv
├── instagram
├── threads
├── youtube
├── snackvideo
├── main.py              # Logic utama uiautomator2
├── config.json          # List komentar & daftar nama akun
└── README.md            # File instruksi ini

## 🚀 Critical Workflow Logic

### 1. Initialization Phase
- Skrip harus mendeteksi seluruh Serial Number (SN) perangkat yang statusnya `device`.
- Pengguna memilih 1 platform target melalui input terminal.
- Skrip memvalidasi URL sesuai dengan platform yang dipilih.

### 2. Parallel Execution (Threading)
- Buat fungsi `process_device(serial_number, platform, url)`.
- Gunakan `ThreadPoolExecutor` untuk menjalankan fungsi tersebut di setiap HP secara bersamaan.
- **Setiap HP harus:**
    - Identifikasi akun yang sedang aktif (Scrape username dari halaman profil).
    - Kirim Intent URL langsung ke aplikasi.
    - Mulai timer (`start_time`).
    - Cari tombol Like & klik.
    - Cari tombol Comment, ketik teks random, & post.
    - Catat `end_time` segera setelah komentar terkirim.

### 3. Account Switching Logic
- Jika skrip mendeteksi ada lebih dari satu akun di perangkat (via menu switch account), lakukan iterasi:
  * Selesaikan tugas di Akun A -> Switch ke Akun B -> Ulangi tugas di URL yang sama.

### 4. Advanced Reporting (Per Device)
Setiap HP harus melaporkan hasilnya ke dalam tabel ringkasan akhir yang mencakup:
| Device ID | Account Name | Platform | Status | Duration (sec) |
|-----------|--------------|----------|--------|----------------|
| SN12345   | @user_pro    | Instagram| SUCCESS| 12.5s          |
| SN67890   | @test_bot    | Instagram| FAILED | 0.0s           |

## 🧩 Logic Snippet for Agent
Agen harus menggunakan pendekatan ini untuk koneksi perangkat:
```python
import uiautomator2 as u2
from concurrent.futures import ThreadPoolExecutor

def task(serial, url):
    d = u2.connect(serial)
    # Logic intent, like, comment, timer...
    
devices = [d.serial for d in adbutils.adb.device_list()]
with ThreadPoolExecutor(max_workers=len(devices)) as executor:
    executor.map(lambda sn: task(sn, target_url), devices)