FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY notification/ .

EXPOSE 8001

CMD ["gunicorn", "notification.wsgi:application", "--bind", "0.0.0.0:8001", "--workers", "3"]