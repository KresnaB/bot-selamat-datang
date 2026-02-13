# Gunakan image Python yang ringan
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies sistem yang diperlukan (termasuk FFmpeg dan gcc untuk build modules)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file terlebih dahulu untuk caching layer
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode aplikasi
COPY . .

# Command untuk menjalankan bot
CMD ["python", "bot.py"]
