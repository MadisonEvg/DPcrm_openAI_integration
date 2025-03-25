from flask import Flask
from routes.webhook import webhook_bp
from utils.wazzup_client import WazzupClient
from utils.statistics_manager import start_statistic_scheduler
import threading
import asyncio


app = Flask(__name__)
app.register_blueprint(webhook_bp)

wazzup_client = WazzupClient()

async def init_webhooks():
    print('-----------init_webhooks-------1')
    await asyncio.sleep(2)
    print('-----------init_webhooks-------2')
    wazzup_client.update_webhooks()

def run_asyncio_task():
    asyncio.run(init_webhooks()) 
    
threading.Thread(target=run_asyncio_task, daemon=True).start()

if __name__ == "__main__":
    start_statistic_scheduler()
    app.run(host='0.0.0.0', port=5000)