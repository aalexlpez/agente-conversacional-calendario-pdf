# Dockerfile para agente conversacional FastAPI
FROM python:3.11-slim

# Evita prompts interactivos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Instala dependencias del sistema necesarias para pdfminer y Google API
RUN apt-get update && apt-get install -y \
    build-essential \
    libpoppler-cpp-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expone el puerto por defecto de FastAPI/Uvicorn
EXPOSE 8000

# Comando de arranque para Railway
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
