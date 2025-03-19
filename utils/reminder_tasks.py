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
last_reminder_tasks = {}
loop = asyncio.new_event_loop()  # Глобальный event loop
thread = threading.Thread(target=lambda: asyncio.run(loop.run_forever()), daemon=True)
thread.start()  # Запускаем event loop в отдельном потоке

async def delayed_task(task_id, tasks_dict=tasks):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        await asyncio.sleep(calc_wait_second())
        if tasks_dict==tasks:
            wazzup_client.send_message(task_id, "Вы про меня не забыли?")
            schedule_last_reminder(task_id)
            print('----------------------------------')
            print(f"Задача выполнена с ID: {task_id}")
        elif tasks_dict==last_reminder_tasks:
            print('----------------------------------')
            print(f"Последнее напоминание прошло у пользователя {tasks_lead_id[task_id]} меняем статус")
            dp_crm_client.change_user_status(tasks_lead_id[task_id], dp_crm_client.status_archive)
        
    except asyncio.CancelledError:
        print(f"Задача с ID {task_id} отменена")
    finally:
        tasks_dict.pop(task_id, None)
        
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
        tasks[task_id].cancel()  # Отменяем старую задачу
    if task_id in last_reminder_tasks:  
        last_reminder_tasks[task_id].cancel()  # Отменяем старую задачу
    print(f"Старая задача с ID {task_id} отменена")
        
def schedule_task(task_id, lead_id):
    """Планирует новую задачу, отменяя старую (если есть)"""
    cancel_task(task_id)
    tasks_lead_id[task_id] = lead_id

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id), loop)
    tasks[task_id] = task
    print(f"Новая задача запущена с ID {task_id}")

def schedule_last_reminder(task_id):
    """Планирует новую задачу, отменяя старую (если есть)"""
    cancel_task(task_id)

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id, last_reminder_tasks), loop)
    last_reminder_tasks[task_id] = task
    print(f"Новая задача запущена с ID {task_id}")
    