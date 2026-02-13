# Instalasi Bot Discord di Server Armbian

Panduan lengkap untuk menjalankan bot Discord Welcome di server Armbian agar berjalan 24/7.

---

## 1. Update Sistem

```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Install Python & FFmpeg

```bash
sudo apt install python3 python3-pip python3-venv ffmpeg -y
```

Verifikasi:
```bash
python3 --version
ffmpeg -version
```

## 3. Clone Repository

```bash
cd ~
git clone https://github.com/KresnaB/bot-selamat-datang.git
cd bot-selamat-datang
```

## 4. Buat Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

## 5. Install Dependencies

```bash
pip install -r requirements.txt
```

## 6. Konfigurasi Token

```bash
nano .env
```

Isi file `.env`:
```
DISCORD_TOKEN=token_bot_kamu_disini
VOICE_CHANNEL_ID=id_voice_channel_(opsional)
```

Simpan: `Ctrl+O` → `Enter` → `Ctrl+X`

## 7. Test Bot

```bash
python3 bot.py
```

Jika muncul `✅ Bot sudah online!`, bot berjalan dengan benar. Tekan `Ctrl+C` untuk stop.

---

## 8. Jalankan 24/7 dengan systemd

Buat service file:
```bash
sudo nano /etc/systemd/system/discord-bot.service
```

Isi dengan (ganti `NAMA_USER` dengan username Armbian kamu, cek dengan perintah `whoami`):
```ini
[Unit]
Description=Discord Welcome Bot
After=network.target
[Service]
Type=simple
User=root
WorkingDirectory=/root/bot-selamat-datang
ExecStart=/root/bot-selamat-datang/venv/bin/python3 bot.py
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin
[Install]
WantedBy=multi-user.target
```

Simpan: `Ctrl+O` → `Enter` → `Ctrl+X`

Aktifkan service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

## 9. Cek Status Bot

```bash
sudo systemctl status discord-bot
```

## Perintah Berguna

| Perintah | Fungsi |
|----------|--------|
| `sudo systemctl start discord-bot` | Jalankan bot |
| `sudo systemctl stop discord-bot` | Hentikan bot |
| `sudo systemctl restart discord-bot` | Restart bot |
| `sudo systemctl status discord-bot` | Cek status |
| `journalctl -u discord-bot -f` | Lihat log real-time |
| `journalctl -u discord-bot --since "1 hour ago"` | Log 1 jam terakhir |


## Update Bot

Jika ada perubahan kode di GitHub:
```bash
cd ~/bot-selamat-datang
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart discord-bot
```

---

# Migrasi ke Docker (Recommended)

Jika ingin beralih menggunakan Docker agar lebih stabil dan mudah dikelola:

## 1. Stop Service Lama (Jika ada)

```bash
sudo systemctl stop discord-bot
sudo systemctl disable discord-bot
```

## 2. Install Docker & Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Tambahkan user ke grup docker (agar tidak perlu sudo terus)
sudo usermod -aG docker $USER
newgrp docker
```

## 3. Jalankan dengan Docker

Pastikan sudah berada di folder bot dan sudah `git pull` terbaru:

```bash
cd ~/bot-selamat-datang
git pull
docker-compose up -d --build
```

## 4. Cek Status Container

```bash
docker-compose logs -f
```

Untuk mematikan: `docker-compose down`
Update bot di masa depan cukup: `git pull && docker-compose up -d --build`
