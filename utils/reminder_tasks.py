import threading
import pytz
import asyncio
from config import Config
from datetime import datetime, timedelta
from utils.wazzup_client import WazzupClient
from utils.dp_client import DpCRMClient

wazzup_client = WazzupClient()
dp_crm_client = DpCRMClient()
VLADIVOSTOK_TZ = pytz.timezone("Asia/Vladivostok")

# Словарь для хранения задач по ключу chat_id
tasks = {}
tasks_lead_id = {}
loop = asyncio.new_event_loop()  # Глобальный event loop
thread = threading.Thread(target=lambda: asyncio.run(loop.run_forever()), daemon=True)
thread.start()  # Запускаем event loop в отдельном потоке

async def delayed_task(task_id, last_reminder=False):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        await asyncio.sleep(calc_wait_second())
        
        if last_reminder:
            print(f"Последнее напоминание прошло у пользователя {tasks_lead_id[task_id]} меняем статус")
            dp_crm_client.change_user_status(tasks_lead_id[task_id], dp_crm_client.status_archive)
        else:
            wazzup_client.send_message(task_id, "Вы про меня не забыли?")
        
    except asyncio.CancelledError:
        last_reminder = True
        print(f"asyncio.CancelledError Задача с ID {task_id} отменена")
    finally:
        print(f"delayed_task finally")
        tasks.pop(task_id, None)
        if not last_reminder:
            task = asyncio.run_coroutine_threadsafe(delayed_task(task_id, True), loop)
            tasks[task_id] = task
        
def calc_wait_second():
    now = datetime.now(VLADIVOSTOK_TZ).time()
    send_now = (10, 0) <= (now.hour, now.minute) <= (20, 0)

    if not send_now:
        # Если время не в допустимом диапазоне
        tomorrow_10am = (datetime.now(VLADIVOSTOK_TZ) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow_10am - datetime.now(VLADIVOSTOK_TZ)).total_seconds()
        print(f"Время вне диапазона, откладываем до 10:00 (ждать {wait_seconds // 60} минут)")
        return wait_seconds
    else:
        return 0
    
def cancel_task(task_id):
    """Удаляет напоминание, в случае если диалог успешен или клиент ответил отрицательно
    или если появилась новая задача с таким task_id"""
    if task_id in tasks:  
        print(f"Task {task_id} status: {tasks[task_id]}")
        tasks[task_id].cancel()  # Отменяем старую задачу
        print(f"Task {task_id} status: {tasks[task_id]}")
    
        
def schedule_task(task_id, lead_id, last_reminder=False):
    """Планирует новую задачу, отменяя старую (если есть)"""
    cancel_task(task_id)
    tasks_lead_id[task_id] = lead_id

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id, last_reminder), loop)
    tasks[task_id] = task
    print(f"Новая задача запущена с ID {task_id}")
    