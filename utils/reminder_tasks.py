import threading
import pytz
import asyncio
from config import Config
from datetime import datetime, timedelta
from utils.wazzup_client import WazzupClient

wazzup_client = WazzupClient()
VLADIVOSTOK_TZ = pytz.timezone("Asia/Vladivostok")

# Словарь для хранения задач по ключу chat_id
tasks = {}
loop = asyncio.new_event_loop()  # Глобальный event loop
thread = threading.Thread(target=lambda: asyncio.run(loop.run_forever()), daemon=True)
thread.start()  # Запускаем event loop в отдельном потоке

async def delayed_task(task_id):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        
        now = datetime.now(VLADIVOSTOK_TZ).time()
        send_now = (10, 0) <= (now.hour, now.minute) <= (20, 0)

        if not send_now:
            # Если время не в допустимом диапазоне
            tomorrow_10am = (datetime.now(VLADIVOSTOK_TZ) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
            wait_seconds = (tomorrow_10am - datetime.now(VLADIVOSTOK_TZ)).total_seconds()
            print(f"Время вне диапазона, откладываем до 10:00 (ждать {wait_seconds // 60} минут)")
            await asyncio.sleep(wait_seconds)
            
        wazzup_client.send_message(task_id, "Вы про меня не забыли?")
        print(f"Задача выполнена с ID: {task_id}")
    except asyncio.CancelledError:
        print(f"Задача с ID {task_id} отменена")
    finally:
        tasks.pop(task_id, None)
    
def schedule_task(task_id):
    """Планирует новую задачу, отменяя старую (если есть)"""
    if task_id in tasks:  
        tasks[task_id].cancel()  # Отменяем старую задачу
        print(f"Старая задача с ID {task_id} отменена")

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id), loop)
    tasks[task_id] = task
    print(f"Новая задача запущена с ID {task_id}")