import requests
import json
from config import Config
from models.conversation_manager import ConversationManager
from logger_config import logger


def clean_text(text):
    text = text.replace('[', '')
    text = text.replace(']', '')
    return text


class WazzupClient:
    def __init__(self):
        self.api_url = Config.WAZZUP_API_URL
        self.webhooks_api_url = Config.WAZZUP_WEBHOOKS_URL
        self.channel_id = Config.WAZZUP_CHANNEL_ID
        self._webhooks_uri = Config.WEBHOOKS_URI
        self._headers = {
            "Authorization": f"Bearer {Config.WAZZUP_API_KEY}",
            "Content-Type": "application/json"
        }
        self._conversation_manager = ConversationManager()

    def send_message(self, chat_id, message_text):
        message_text = clean_text(message_text)        
        payload = {
            "channelId": self.channel_id,
            "chatType": "whatsapp",
            "chatId": chat_id,
            "text": message_text
        }
        try:
            # Добавляем новое сообщение пользователя
            logger.info(f"------------ wz send_message {chat_id}: {message_text}")
            # self._conversation_manager.add_assistant_message(chat_id, message_text)
            response = requests.post(self.api_url, headers=self._headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error("Ошибка HTTP:", e)
        except requests.exceptions.RequestException as e:
            logger.error("Ошибка при отправке сообщения в Wazzup:", e)
        except Exception as e:
            logger.error("Ошибка", e)
            
    def update_webhooks(self):
        return
        # payload = {
        #     "webhooksUri": f'{self._webhooks_uri}/webhooks',
        #     "subscriptions": {
        #         "messagesAndStatuses": True,
        #         "contactsAndDealsCreation": False,
        #         "channelsUpdates": False,
        #         "templateStatus": False
        #     }
        # }
        # try:
        #     response = requests.patch(self.webhooks_api_url, json=payload, headers=self._headers)
        #     print('response', response.text)
        #     response.raise_for_status()
        #     return response.text
        # except requests.exceptions.RequestException as e:
        #     print(str(e))
        #     return {"error": str(e)}