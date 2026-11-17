FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-base', revision='ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66', local_dir='/opt/whisper/base', allow_patterns=['model.bin','config.json','vocabulary.txt','tokenizer.json'])"
COPY . .
RUN python -m unittest discover -v
ENV PORT=8080 DATA_DIR=/data PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "server.py"]
