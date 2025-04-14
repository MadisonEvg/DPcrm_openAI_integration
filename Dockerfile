FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Vladivostok

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001", "--workers", "1", "--ssl-keyfile", "/certs/privkey.pem", "--ssl-certfile", "/certs/cert.pem"]
