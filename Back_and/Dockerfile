# 1. Escolher a imagem base do Python
FROM python:3.10-slim

# 2. Definir o diretório de trabalho
WORKDIR /app

# 3. NOVO: Atualizar e instalar ffmpeg, que é uma dependência do Whisper
RUN apt-get update && apt-get install -y ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 4. Copiar e instalar as dependências Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copiar o resto do código
COPY . .

# 6. Expor a porta
EXPOSE 8080

# 7. Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "120", "app:app"]