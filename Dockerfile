FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
ENV FLASK_APP=project/app.py
ENV FLASK_ENV=production
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "--bind", "0.0.0.0:8000", "project.app:create_app()"]