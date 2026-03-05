#!/bin/bash

SERVICE_NAME="nyuntik_cihuy"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME.service"

echo "🚀 Memulai setup service: $SERVICE_NAME"

# 1. Pastikan script dijalankan sebagai root/sudo
if [ "$EUID" -ne 0 ]; then 
  echo "❌ Tolong jalankan script ini dengan sudo ya: sudo ./setup_service.sh"
  exit
fi

# 2. Cek apakah file service sudah ada di lokasi tujuan
if [ ! -f "$SERVICE_PATH" ]; then
    echo "📂 Menyalin file service ke $SERVICE_PATH..."
    # Asumsi file service ada di folder saat ini, kalau tidak ada kita buatkan otomatis
    cp ./$SERVICE_NAME.service $SERVICE_PATH 2>/dev/null || {
        echo "⚠️ File $SERVICE_NAME.service tidak ditemukan di folder ini."
        echo "📝 Membuat file service baru..."
        cat <<EOF > $SERVICE_PATH
[Unit]
Description=Server Python Nyuntik Sosmed
After=network.target

[Service]
User=me
Group=me
WorkingDirectory=/home/me/nyuntik_sosmed
ExecStart=/home/me/nyuntik_sosmed/.venv/bin/python /home/me/nyuntik_sosmed/server.py
Restart=always
RestartSec=5
Environment=PATH=/home/me/nyuntik_sosmed/.venv/bin:/usr/local/bin:/usr/bin
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    }
fi

# 3. Reload systemd untuk mengenali perubahan
echo "🔄 Reloading systemd daemon..."
systemctl daemon-reload

# 4. Enable service agar jalan otomatis saat boot
echo "⚙️ Enabling service..."
systemctl enable $SERVICE_NAME

# 5. Restart service
echo "⚡ Restarting service..."
systemctl restart $SERVICE_NAME

# 6. Cek status akhir
echo "---------------------------------------"
systemctl status $SERVICE_NAME --no-pager
echo "---------------------------------------"
echo "✅ Setup Selesai! Cek log pake: journalctl -u $SERVICE_NAME -f"