from utils.helpers import trim_conversation_history
from config import Config
from docx import Document
from enum import Enum


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationManager:
    
    _instance = None  
    
    # key это source_id из инфы lead'а
    # https://domoplaner.ru/mypanel/settings/leads/ на вкладке Источники
    PROMPT_PATHS = {
        1: "promts/promt_victory.docx",
        9077: "promts/promt.docx",
    }
    DEFAULT_PROMPT_PATH = "promts/promt_victory.docx"  # Дефолтный путь

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance.conversation_histories = {} 
        return cls._instance

    def _get_promt(self, source_id):
        prompt_path = self.PROMPT_PATHS.get(source_id, self.DEFAULT_PROMPT_PATH)
        return self._read_prompt_from_word(prompt_path)

    def _read_prompt_from_word(self, file_path: str) -> str:
        try:
            document = Document(file_path)
            return "\n".join([para.text for para in document.paragraphs])
        except Exception as e:
            print(f"Ошибка при чтении файла {file_path}: {e}")
            return "Произошла ошибка при загрузке промпта."

    def initialize_conversation(self, chat_id, source_id):
        # Делаем инициализацию в точке входа, обработке webhook'а
        if chat_id not in self.conversation_histories:
            promt = self._get_promt(source_id)
            self.conversation_histories[chat_id]=[{"role": Role.SYSTEM.value, "content": promt}]
            
    def add_user_message(self, chat_id, content):
        self.add_message(chat_id, Role.USER, content)
        
    def add_assistant_message(self, chat_id, content):
        self.add_message(chat_id, Role.ASSISTANT, content)

    def add_message(self, chat_id, role, content):
        self.conversation_histories[chat_id].append({"role": role.value, "content": content})

    def get_history(self, chat_id):
        return self.conversation_histories.get(chat_id, [])

    def trim_history(self, chat_id, max_tokens=3500):
        history = self.conversation_histories.get(chat_id, [])
        trim_conversation_history(history, max_tokens)
        self.conversation_histories[chat_id] = history