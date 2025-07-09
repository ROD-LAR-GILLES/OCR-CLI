# ──────────────────────────────
# OCR-CLI   (Python 3.11 slim)
# ──────────────────────────────
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# libs para Tesseract, pdf2image y pdfplumber
RUN apt-get update && apt-get install -y \
    tesseract-ocr tesseract-ocr-spa poppler-utils ghostscript gcc \
    libglib2.0-0 libgl1-mesa-glx libsm6 libxext6 libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "interfaces/cli/main.py"]