import os

IN_DOCKER = os.environ.get("IN_DOCKER", False)

# Если НЕ в Docker — загружаем переменные из `.env`
if not IN_DOCKER:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.getcwd(), ".env", ".env")
    load_dotenv(dotenv_path)

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")
    WAZZUP_API_URL = os.getenv("WAZZUP_API_URL")
    WAZZUP_CHANNEL_ID = os.getenv("WAZZUP_CHANNEL_ID")
    
    WAZZUP_WEBHOOKS_URL = os.getenv("WAZZUP_WEBHOOKS_URL")
    WEBHOOKS_URI = os.getenv("WEBHOOKS_URI")
    
    PROMPT_FILE_PATH = os.getenv('PROMPT_FILE_PATH')
    PROXY_URL = os.getenv('PROXY_URL')
    DPCRM_ACCESS_TOKEN = os.getenv("DPCRM_ACCESS_TOKEN")
    PDCRM_URL = "https://acc524e049130cf3.amocrm.ru"
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.5))
    MODEL_GPT4O = "gpt-4o"
    MODEL_GPT4OMINI = "gpt-4o-mini"
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 10000))
    ASSISTANT_DELAY = int(os.getenv("ASSISTANT_DELAY", 1))
    PORT = int(os.getenv("PORT", 8080))
    USER_PING_DELAY = int(os.getenv("USER_PING_DELAY", 7200))
    TOKEN_COST_IN_GPT4O = 2.50 / 10**6
    TOKEN_COST_OUT_GPT4O = 10.00 / 10**6
    TOKEN_COST_IN_GPT4_MINI = 0.150 / 10**6
    TOKEN_COST_OUT_GPT4_MINI = 0.600 / 10**6