import threading
import pytz
import asyncio
from config import Config
from datetime import datetime, timedelta
from utils.wazzup_client import WazzupClient
from utils.dp_client import DpCRMClient
from logger_config import logger
from utils.openai_client import OpenAIClient
from models.conversation_manager import PromptType

wazzup_client = WazzupClient()
dp_crm_client = DpCRMClient()
openai_client = OpenAIClient()
VLADIVOSTOK_TZ = pytz.timezone("Asia/Vladivostok")

# Словарь для хранения задач по ключу chat_id
tasks = {}
tasks_lead_id = {}
loop = asyncio.new_event_loop()  # Глобальный event loop
thread = threading.Thread(target=lambda: asyncio.run(loop.run_forever()), daemon=True)
thread.start()  # Запускаем event loop в отдельном потоке


async def monitor_tasks():
    while True:
        logger.info("------------ monitor_tasks ------------")
        active_tasks = list(tasks.keys())
        logger.info(f"tasks: {active_tasks}")
        active_tasks = [
            t.get_name() for t in asyncio.all_tasks(loop) 
            if not t.done() and t.get_coro().__name__ != "monitor_tasks"
        ]
        logger.info(f"active tasks: {active_tasks }")  # Исправленный вывод
        
        logger.info("------------ monitor_tasks end---------")
        await asyncio.sleep(60)

# Запускаем мониторинг в event loop'е
future = asyncio.run_coroutine_threadsafe(monitor_tasks(), loop)

async def delayed_task(task_id, last_reminder=False):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        await asyncio.sleep(calc_wait_second())
        
        if last_reminder:
            logger.info(f"Последнее напоминание прошло у пользователя {tasks_lead_id[task_id]} меняем статус")
            dp_crm_client.change_user_status(tasks_lead_id[task_id], dp_crm_client.status_archive)
        else:
            response_from_mini = await openai_client.get_gpt4o_mini_response(task_id, PromptType.MINI_PING)
            logger.info(f'--delayed_task-- response_from_mini PING!!!!: {response_from_mini}')
            wazzup_client.send_message(task_id, response_from_mini)
        
    except asyncio.CancelledError:
        last_reminder = True
        logger.info(f"asyncio.CancelledError Задача с ID {task_id} отменена")
    finally:
        logger.info("------------ delayed_task finally------------")
        logger.info(f"task_id: {task_id} is poped")
        tasks.pop(task_id, None)
        
        if not last_reminder:
            logger.info(f"--webhook-- запускаем напоминалку из delayed_task")
            await schedule_task(task_id, tasks_lead_id[task_id], True)
        
def calc_wait_second():
    now = datetime.now(VLADIVOSTOK_TZ).time()
    send_now = (Config.NOTIFY_START_TIME, 0) <= (now.hour, now.minute) <= (Config.NOTIFY_END_TIME, 0)
    logger.info(f"---- send_now: {send_now}")
    # TODO delete next line befor commit
    return 0
    if not send_now:
        # Если время не в допустимом диапазоне
        tomorrow_10am = (datetime.now(VLADIVOSTOK_TZ) + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        wait_seconds = (tomorrow_10am - datetime.now(VLADIVOSTOK_TZ)).total_seconds()
        logger.info(f"Время вне диапазона, откладываем до 10:00 (ждать {wait_seconds // 60} минут)")
        return wait_seconds
    else:
        return 0
    
async def cancel_task(task_id):
    """Удаляет напоминание, в случае если диалог успешен или клиент ответил отрицательно
    или если появилась новая задача с таким task_id"""
    if task_id in tasks:
        tasks[task_id].cancel()
        await asyncio.sleep(0.2)
        logger.info("-- cancel_task -- cancel {task_id}")
    
        
async def schedule_task(task_id, lead_id, last_reminder=False):
    """Планирует новую задачу, отменяя старую (если есть)"""
    await cancel_task(task_id)
    tasks_lead_id[task_id] = lead_id

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id, last_reminder), loop)
    if last_reminder:
        logger.info(f"--schedule_task-- LAST reminder {task_id} is started")
    else:
        logger.info(f"--schedule_task-- reminder {task_id} is started")
    tasks[task_id] = task    