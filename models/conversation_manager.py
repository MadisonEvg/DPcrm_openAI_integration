import pytz
from utils.helpers import trim_conversation_history
from config import Config
from docx import Document
from enum import Enum
from utils.dp_client import DpCRMClient, MessageDirection
from datetime import datetime
from models.models import Role
from models.utils_db import add_conversation, get_conversation_history_by_chat_id
from models.db import async_session_maker
from logger_config import logger


dp_crm_client = DpCRMClient()

class PromptType(Enum):
    MINI_DIALOG = "mini_dialog"
    MINI_PING = "mini_ping"
    
weekdays = {
    0: 'Понедельник',
    1: 'Вторник',
    2: 'Среда',
    3: 'Четверг',
    4: 'Пятница',
    5: 'Суббота',
    6: 'Воскресенье',
}    
    
def get_vladivostok_time():
    vladivostok_tz = pytz.timezone('Asia/Vladivostok')
    vladivostok_time = datetime.now(vladivostok_tz)
    weekday = weekdays[vladivostok_time.weekday()]
    return f"{weekday}, {vladivostok_time.strftime('%Y-%m-%d %H:%M:%S')}"
    
    
class ConversationManager:
    
    _instance = None  
    
    # key это source_id из инфы lead'а
    # https://domoplaner.ru/mypanel/settings/leads/ на вкладке Источники
    DEFAULT_PROMPT_PATH = "promts/promt.docx"  # Дефолтный путь
    MINI_PROMPT_PATH = "promts/promt_mini.docx"  # Путь для решения успешности диалога
    MINI_PROMPT_PING_PATH = "promts/promt_ping.docx"  # Путь для решения успешности диалога
    PROMPT_PATHS = {
        7269: "promts/promt_victory.docx",
        9077: DEFAULT_PROMPT_PATH,
        9198: "promts/promt_victory.docx",
    }

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.mini_promt_dialog = self._read_prompt_from_word(self.MINI_PROMPT_PATH)
        self.mini_promt_ping = self._read_prompt_from_word(self.MINI_PROMPT_PING_PATH)

    def _get_promt(self, source_id):
        prompt_path = self.PROMPT_PATHS.get(source_id, self.DEFAULT_PROMPT_PATH)
        logger.info(f"Выбран вот такой промт: ", prompt_path)
        return self._read_prompt_from_word(prompt_path)

    def _read_prompt_from_word(self, file_path: str) -> str:
        try:
            document = Document(file_path)
            return "\n".join([para.text for para in document.paragraphs])
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return "Произошла ошибка при загрузке промпта."

    async def get_history(self, chat_id, source_id=DEFAULT_PROMPT_PATH, max_tokens=None):
        promt = self._get_promt(source_id)
        full_history = [{"role": Role.SYSTEM.value, "content": promt}]
        vladivostok_time = get_vladivostok_time()
        full_history.append({"role": Role.SYSTEM.value, "content": f"Текущее время во Владивостоке: {vladivostok_time}"})
        async with async_session_maker() as session:
            full_history += await get_conversation_history_by_chat_id(session, chat_id)
        if max_tokens is not None:
            trim_conversation_history(full_history, max_tokens)
        return full_history
            
    async def add_user_message(self, chat_id, content):
        await self.add_message(chat_id, Role.USER, content)
        dp_crm_client.send_message(content, chat_id, MessageDirection.INCOMING)
        
    async def add_assistant_message(self, chat_id, content):
        await self.add_message(chat_id, Role.ASSISTANT, content)
        dp_crm_client.send_message(content, chat_id, MessageDirection.OUTGOING)

    async def add_message(self, chat_id, role, content):
        async with async_session_maker() as session:
            await add_conversation(session, chat_id, role, content)
    
    async def get_history_for_mini(self, chat_id, prompt_type: PromptType, source_id, max_tokens=None):
        prompt_map = {
            PromptType.MINI_DIALOG: self.mini_promt_dialog,
            PromptType.MINI_PING: self.mini_promt_ping
        }
        prompt = prompt_map.get(prompt_type)
        history = await self.get_history(chat_id, max_tokens=max_tokens, source_id=source_id)
        return [{"role": Role.SYSTEM.value, "content": prompt}] + history[1:]
