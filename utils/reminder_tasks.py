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
from models.utils_db import get_conversation_history_by_chat_id
from models.db import async_session_maker
from utils.dp_api import get_lead_id_from_movements, get_valid_lead_phones
from models.conversation_manager import ConversationManager


wazzup_client = WazzupClient()
dp_crm_client = DpCRMClient()
openai_client = OpenAIClient()
conversation_manager = ConversationManager()

VLADIVOSTOK_TZ = pytz.timezone("Asia/Vladivostok")

# Словарь для хранения задач по ключу chat_id
tasks = {}
tasks_lead_id = {}


async def delayed_task(task_id):
    try:
        await asyncio.sleep(Config.USER_PING_DELAY)
        await asyncio.sleep(calc_wait_second())
        lead = dp_crm_client.get_or_create_lead_by_phone(task_id)   
        response_from_mini = await openai_client.get_gpt4o_mini_response(task_id, PromptType.MINI_PING, lead['source_id'])
        logger.info(f'--delayed_task-- response_from_mini PING!!!!: {response_from_mini}')
        await conversation_manager.add_assistant_message(task_id, response_from_mini)
        wazzup_client.send_message(task_id, response_from_mini)
        
    except asyncio.CancelledError:
        logger.info(f"asyncio.CancelledError Задача с ID {task_id} отменена")
    finally:
        logger.info("------------ delayed_task finally------------")
        logger.info(f"task_id: {task_id} is poped")
        tasks.pop(task_id, None)
        
async def remind_lead_from_victory():
    """пинг если клиент ничего не написал на первое сообщение скриптом"""
    logger.info("++++++++++++++++++++++++ start check_users_ping ++++++++++++++++++++++++")
    while True:
        await asyncio.sleep(calc_wait_second())
        logger.info("------------ check_users_ping ---------")
        movements = dp_crm_client.get_movements()
        lead_id_list = get_lead_id_from_movements(movements['movements'], Config.DPCRM_STATUS_ID_CHECK_REMINDER)
        leads = [dp_crm_client.get_lead_by_id(lead_id) for lead_id in lead_id_list]
        phones = get_valid_lead_phones(leads, (9198, 7269)) # check source id
        logger.info(f'phones (remind_lead_from_victory): {phones}')
        async with async_session_maker() as session:
            for phone in phones:
                history = await get_conversation_history_by_chat_id(session, phone)
                if not len(history):
                    wazzup_client.send_message(phone, Config.REMIND_LEAD_FROM_VICTORY_PHRASE)
                    await conversation_manager.add_assistant_message(phone, Config.REMIND_LEAD_FROM_VICTORY_PHRASE)
                    logger.info(f'!!!!!!!!!!!need to ping {phone}!!!!!!!!!!!')
        await asyncio.sleep(Config.REMIND_LEAD_FROM_VICTORY_DELAY)
        

# Запускаем мониторинг в event loop'е
asyncio.run_coroutine_threadsafe(remind_lead_from_victory(), loop)
        
def calc_wait_second():
    now_dt = datetime.now(VLADIVOSTOK_TZ)
    now_time = now_dt.time()
    send_now = (Config.NOTIFY_START_TIME, 0) <= (now_time.hour, now_time.minute) <= (Config.NOTIFY_END_TIME, 0)
    logger.info(f"---- send_now: {send_now}")
    if not send_now:
        today_target = now_dt.replace(hour=10, minute=7, second=0, microsecond=0)
        if now_dt < today_target:
            wait_until = today_target
        else:
            wait_until = today_target + timedelta(days=1)
        wait_seconds = (wait_until - now_dt).total_seconds()
            
        # Если время не в допустимом диапазоне
        # tomorrow_10am = (datetime.now(VLADIVOSTOK_TZ) + timedelta(days=1)).replace(hour=10, minute=7, second=0, microsecond=0)
        # wait_seconds = (tomorrow_10am - datetime.now(VLADIVOSTOK_TZ)).total_seconds()
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