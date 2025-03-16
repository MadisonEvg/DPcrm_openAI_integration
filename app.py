from flask import Flask
from routes.webhook import webhook_bp
from utils.wazzup_client import WazzupClient
import time
import threading


app = Flask(__name__)
app.register_blueprint(webhook_bp)

wazzup_client = WazzupClient()

@app.route('/')
def hello_world():
  return 'Hello, World!'

def init_webhooks():
    time.sleep(2)
    wazzup_client.update_webhooks()

# Запускаем отправку запроса в отдельном потоке
threading.Thread(target=init_webhooks, daemon=True).start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)