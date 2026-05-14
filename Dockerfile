FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema (se necessário)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código
COPY . .

# Criar diretórios necessários (persistidos via volumes)
RUN mkdir -p .credentials .claude orcamentos

# Garantir que scripts são executáveis
RUN chmod +x auto_pipeline.py google_drive_sync_with_token.py test_drive_connection.py test_oauth_google_drive.py monitor_drive_uploads.py

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Executar o pipeline automático
CMD ["python3", "auto_pipeline.py"]
