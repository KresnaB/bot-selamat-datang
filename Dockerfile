# Gunakan image Python yang ringan
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies sistem yang diperlukan (termasuk FFmpeg dan gcc untuk build modules)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    build-essential \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file terlebih dahulu untuk caching layer
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Force reinstall voice libraries to ensure DAVE protocol support (NaCl extensions)
RUN pip install --no-cache-dir --force-reinstall discord.py[voice] PyNaCl

# Copy sisa kode aplikasi
COPY . .

# Command untuk menjalankan bot
CMD ["python", "bot.py"]
