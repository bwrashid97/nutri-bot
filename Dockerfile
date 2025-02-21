# Use uma imagem base do Python (3.10-slim, por exemplo)
FROM python:3.10-slim

# Define o diretório de trabalho no container
WORKDIR /app

# Instale dependências do sistema (ex.: gcc) se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copie o arquivo de dependências para o container
COPY requirements.txt .

# Atualize o pip e instale as dependências do projeto
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copie todo o código do projeto para o container
COPY . .

# Variáveis de ambiente (ajuste conforme necessário)
ENV FLASK_APP=project/app.py
ENV FLASK_ENV=production

# Exponha a porta que a aplicação usará (por exemplo, 8000)
EXPOSE 8000

# Comando para iniciar a aplicação com Gunicorn
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8000", "project.app:create_app()"]