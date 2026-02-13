# Discord Welcome Bot

Bot Discord Python yang akan bergabung ke voice channel dan memutar suara sambutan ("Welcome to the stream") secara otomatis ketika ada pengguna lain yang masuk ke channel yang sama.

## Fitur
- **Stay 24/7**: Bot tetap berada di voice channel meskipun tidak ada orang.
- **Auto Welcome**: Memutar `welcome.mp3` saat mendeteksi user baru masuk.
- **Commands**: Tersedia perintah untuk join, leave, dan setting channel.
- **Auto Reconnect**: Mendukung rekoneksi otomatis jika koneksi internet terputus.

## Prasyarat
1. **Python 3.8+**
2. **FFmpeg** (diperlukan untuk memutar audio)
3. **Bot Token** dari [Discord Developer Portal](https://discord.com/developers/applications)

## Instalasi

1. Clone repository ini (atau download ZIP):
   ```bash
   git clone https://github.com/USERNAME/REPO_NAME.git
   cd bot-selamat-datang
   ```

2. Install dependensi:
   ```bash
   pip install -r requirements.txt
   ```

3. Konfigurasi `.env`:
   Buat file `.env` di folder utama dan isi:
   ```env
   DISCORD_TOKEN=your_token_here
   VOICE_CHANNEL_ID=optional_channel_id
   ```


## Cara Menjalankan (Docker)

1. Pastikan Docker dan Docker Compose sudah terinstall.
2. Buat file `.env` (lihat bagian Instalasi).
3. Jalankan perintah:
   ```bash
   docker-compose up -d --build
   ```
4. Untuk melihat log:
   ```bash
   docker-compose logs -f
   ```
5. Untuk mematikan bot:
   ```bash
   docker-compose down
   ```

## Cara Menjalankan (Manual)
```bash
python bot.py
```

## Perintah Bot (Prefix: `!`)
- `!join`: Menyuruh bot masuk ke voice channel kamu saat ini.
- `!leave`: Menyuruh bot keluar dari voice channel.
- `!reconnect`: Memaksa bot untuk disconnect dan connect ulang (berguna jika bot error/suara hilang).
- `!setchannel <id>`: Mengatur channel default agar bot otomatis join saat dinyalakan.
- `!status`: Melihat status koneksi bot.
- `!help_welcome`: Menampilkan bantuan.

## Lisensi
MIT
