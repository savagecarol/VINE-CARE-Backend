FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY Data-Collection/ .

EXPOSE 8000

CMD ["gunicorn", "datacollection.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]