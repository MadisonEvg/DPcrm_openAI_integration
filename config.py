import os

IN_DOCKER = os.environ.get("IN_DOCKER", False)

# Если НЕ в Docker — загружаем переменные из `.env`
if not IN_DOCKER:
    from dotenv import load_dotenv
    dotenv_path = os.path.join(os.getcwd(), ".env", ".env")
    load_dotenv(dotenv_path)

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    WAZZUP_API_KEY = os.getenv("WAZZUP_API_KEY")
    WAZZUP_API_URL = os.getenv("WAZZUP_API_URL")
    WAZZUP_CHANNEL_ID = os.getenv("WAZZUP_CHANNEL_ID")
    
    WAZZUP_WEBHOOKS_URL = os.getenv("WAZZUP_WEBHOOKS_URL")
    WEBHOOKS_URI = os.getenv("WEBHOOKS_URI")
    
    PROXY_URL = os.getenv('PROXY_URL')
    DPCRM_ACCESS_TOKEN = os.getenv("DPCRM_ACCESS_TOKEN")
    PDCRM_URL = "https://acc524e049130cf3.amocrm.ru"
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.5))
    MODEL_GPT4O = "gpt-4o"
    MODEL_GPT4OMINI = "gpt-4o-mini"
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 10000))
    PORT = int(os.getenv("PORT", 8080))
    ASSISTANT_DELAY = int(os.getenv("ASSISTANT_DELAY", 1))
    USER_RESPONSE_DELAY = int(os.getenv("USER_RESPONSE_DELAY", 1))
    USER_PING_DELAY = int(os.getenv("USER_PING_DELAY", 7200))
    
    DPCRM_ACCESS_TOKEN=os.getenv("DPCRM_ACCESS_TOKEN")
    DPCRM_API_URL=os.getenv("DPCRM_API_URL")
    
    DPCRM_FIRST_STATUS=int(os.getenv("DPCRM_FIRST_STATUS"))
    DPCRM_SUCCESS_STATUS=int(os.getenv("DPCRM_SUCCESS_STATUS"))
    DPCRM_VALID_CLIENT_STATUSES=[int(status) for status in os.getenv("DPCRM_VALID_CLIENT_STATUSES").split(',')]
    DPCRM_LINK_RECEIVED=int(os.getenv("DPCRM_LINK_RECEIVED"))
    DPCRM_ARCHIVE_STATUS=int(os.getenv("DPCRM_ARCHIVE_STATUS"))
    DPCRM_PING_ALLOWED=int(os.getenv("DPCRM_PING_ALLOWED"))
    

    TOKEN_COST_IN_GPT4O = 2.50 / 10**6
    TOKEN_COST_OUT_GPT4O = 10.00 / 10**6
    TOKEN_COST_IN_GPT4_MINI = 0.150 / 10**6
    TOKEN_COST_OUT_GPT4_MINI = 0.600 / 10**6
    
    NOTIFY_START_TIME = int(os.getenv("NOTIFY_START_TIME", 10))
    NOTIFY_END_TIME = int(os.getenv("NOTIFY_END_TIME", 20))