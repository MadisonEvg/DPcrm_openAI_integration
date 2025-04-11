FROM python:3.11

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Vladivostok

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]