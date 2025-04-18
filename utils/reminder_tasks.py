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
from utils.async_loop import loop

wazzup_client = WazzupClient()
dp_crm_client = DpCRMClient()
openai_client = OpenAIClient()
VLADIVOSTOK_TZ = pytz.timezone("Asia/Vladivostok")

# Словарь для хранения задач по ключу chat_id
tasks = {}
tasks_lead_id = {}


async def delayed_task(task_id):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        await asyncio.sleep(calc_wait_second())
        
        response_from_mini = await openai_client.get_gpt4o_mini_response(task_id, PromptType.MINI_PING)
        logger.info(f'--delayed_task-- response_from_mini PING!!!!: {response_from_mini}')
        wazzup_client.send_message(task_id, response_from_mini)
        
    except asyncio.CancelledError:
        logger.info(f"asyncio.CancelledError Задача с ID {task_id} отменена")
    finally:
        logger.info("------------ delayed_task finally------------")
        logger.info(f"task_id: {task_id} is poped")
        tasks.pop(task_id, None)
        
def calc_wait_second():
    now = datetime.now(VLADIVOSTOK_TZ).time()
    send_now = (Config.NOTIFY_START_TIME, 0) <= (now.hour, now.minute) <= (Config.NOTIFY_END_TIME, 0)
    logger.info(f"---- send_now: {send_now}")
    if not send_now:
        # Если время не в допустимом диапазоне
        tomorrow_10am = (datetime.now(VLADIVOSTOK_TZ) + timedelta(days=1)).replace(hour=10, minute=7, second=0, microsecond=0)
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
    
        
async def schedule_task(task_id, lead_id):
    """Планирует новую задачу, отменяя старую (если есть)"""
    await cancel_task(task_id)
    tasks_lead_id[task_id] = lead_id

    # Создаём новую задачу
    task = asyncio.run_coroutine_threadsafe(delayed_task(task_id), loop)
    logger.info(f"--schedule_task-- reminder {task_id} is started")
    tasks[task_id] = task    