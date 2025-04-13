from flask import Flask
from logger_config import logger
from routes.webhook import webhook_bp
from utils.wazzup_client import WazzupClient
from utils.statistics_manager import start_statistic_scheduler
import threading
import asyncio
import os


IN_DOCKER = os.environ.get("IN_DOCKER", False)


app = Flask(__name__)
app.register_blueprint(webhook_bp)

wazzup_client = WazzupClient()

async def init_webhooks():
    await asyncio.sleep(2)
    wazzup_client.update_webhooks()

def run_asyncio_task():
    asyncio.run(init_webhooks()) 
    
threading.Thread(target=run_asyncio_task, daemon=True).start()


if __name__ == "__main__":
    start_statistic_scheduler()
    logger.info("==========================")
    logger.info("Flask application started!")
    if IN_DOCKER:
        pass
        app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'privkey.pem'))
    else:
        app.run(host='0.0.0.0', port=5000)
    