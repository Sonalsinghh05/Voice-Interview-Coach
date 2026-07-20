FROM python:3.11-slim

WORKDIR /app

# ffmpeg is required by faster-whisper for audio decoding
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install CPU-only torch FIRST — the default PyPI torch wheel pulls in several GB
# of NVIDIA CUDA libraries that we don't need (no GPU is used here).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Note: ./data is mounted as a volume via docker-compose.yml at runtime

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
