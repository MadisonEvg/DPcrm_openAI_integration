FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Vladivostok

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD ["python", "app.py"]
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--certfile=cert.pem", "--keyfile=privkey.pem", "app:app"]
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--certfile=cert.pem", "--keyfile=privkey.pem", "-b", "0.0.0.0:5000", "app:app"]