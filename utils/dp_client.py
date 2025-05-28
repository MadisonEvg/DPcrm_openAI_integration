import requests
from config import Config
from logger_config import logger
from enum import IntEnum
from datetime import datetime
from utils.helpers import get_dt_movement_from_and_to

class MessageDirection(IntEnum):
    INCOMING = 1
    OUTGOING = 2

class DpCRMClient:
    
    def __init__(self):
        self.url = Config.DPCRM_API_URL
        self.access_token = Config.DPCRM_ACCESS_TOKEN
        self.user_access_token = Config.DPCRM_USER_TOKEN_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.inner_headers = {
            "x-user-token": f"{self.user_access_token}",
            "Content-Type": "application/json"
        }
        logger.info(f"------ id статусов:")
        # с таким статусом создаём клиента в ДП
        self.status_first = Config.DPCRM_FIRST_STATUS
        logger.info(f"status_first={self.status_first}")
        # если диалог успешен, переводим в этом статус
        self.status_success = Config.DPCRM_SUCCESS_STATUS
        logger.info(f"status_success={self.status_success}")
        # дополнительный статус, если ссылка получена когда-нибудь
        self.status_link_received = Config.DPCRM_LINK_RECEIVED
        logger.info(f"status_link_received={self.status_link_received}")
        # дополнительный статус, если клиент не отвечает после пинга или клиент отказался (но ссылку так и не получил)
        self.status_archive = Config.DPCRM_ARCHIVE_STATUS
        logger.info(f"status_archive={self.status_archive}")
        # в этих статусах бот отвечает
        self.valid_client_statuses = Config.DPCRM_VALID_CLIENT_STATUSES
        # Статусы в которых можно пинговать
        self.ping_allowed_statuses = [Config.DPCRM_PING_ALLOWED]
        logger.info(f"ping_allowed_statuses={self.ping_allowed_statuses}")
        print('---------')

    
    def change_lead_to_success_status(self, user_id):
        self.change_user_status(user_id, self.status_success)
    
    
    def change_lead_to_link_received_status(self, user_id):
        self.change_user_status(user_id, self.status_link_received)
    
    
    def change_lead_to_archive_status(self, user_id, user_status_id):
        # Проверяем, если у клиента статус link_received_status, то никуда не перемещаем
        if user_status_id != self.status_link_received:
            self.change_user_status(user_id, self.status_archive)
        
   
    def get_list_of_statuses(self, all_statuses, spec_statuses):
        valid_client_statuses = [status.strip() for status in spec_statuses.split(",")]
        return [status['id'] for status in all_statuses if status['title'] in valid_client_statuses]
        
        
    def is_client_status_valid(self, status):
        return status in self.valid_client_statuses
    
    
    def is_client_allowed_to_remind(self, status):
        logger.info(f"--dp_client--is_client_is_client_allowed_to_remind--?? {status}")
        return status in self.ping_allowed_statuses
        
        
    def get_users_status_by_title(self, title, statuses):
        return next((status['id'] for status in statuses if status['title'] == title), None)
    
    def get_users_statuses(self):
        url = f"{self.url}/leads/statuses"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Ошибка при получении данных: {response.text}"
        
    def get_or_create_lead_by_phone(self, phone):
        response = self.get_lead_by_phone(phone)
        if response['status'] == 'error' and response['text'] == 'Клиента с таким номером телефона не найдено':
            user = self.add_user(phone)
            raise Exception("нет лида с таким номером телефона")
            # self.change_user_status(user['lead_id'], self.status_first)
            # response = self.get_lead_by_phone(phone)
        return response['lead']
        
    
    def get_lead_by_phone(self, phone):
        url = f"{self.url}/leads/get-by-phone?phone={phone}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Ошибка при получении данных: {response.text}"
    
    def add_user(self, phone):
        """Add user in CRM

        Args:
            phone (str): user phone number

        Returns:
            dict: {'lead_id': 2064666, 'is_new_lead': 1, 'warnings': [], 'status': 'ok'}
        """
        return ""
        # url = f"{self.url}/leads"
        # payload = {
        #     "phone": phone,
        #     "name": f"Контакт {phone}",
        #     "source": "wazzup",
        #     # "status_id": self.status_first
        # }
        # response = requests.post(url, json=payload, headers=self.headers)
        # if response.status_code == 200:
        #     return response.json()
        # else:
        #     logger.error(f"Ошибка при добавлении пользователя: {response.text}")
        #     raise Exception(f"Ошибка при добавлении пользователя: {response.text}")
        
    def send_message(self, text, client_number, direction: MessageDirection):
        """Creating an array of messages to the client
        """
        return
        # url = f"{self.url}/chats/messages"
        # author_name = " " if direction == MessageDirection.INCOMING else "бот"
        # payload = [{
        #     "text": text,
        #     "client_number": client_number,
        #     "messenger_type": 1,
        #     "content_type": 1,
        #     "direction": direction,
        #     "author_name": author_name,
        #     "dt_message": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        # }]
        # response = requests.post(url, json=payload, headers=self.headers)
        # if response.status_code == 200:
        #     return response.json()
        # else:
        #     return f"Ошибка при получении данных: {response.text}"
        
    def change_user_status(self, user_id, status_id):
        logger.info(f"Изменить статус клиента {user_id} на {status_id}")
        url = f"{self.url}/leads/{user_id}/status"
        payload = {
            "status_id": status_id
        }

        response = requests.patch(url, json=payload, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            logger.info(f"Статус пользователя изменён на {result}.")
            return response.json()
        else:
            logger.warning(f"Ошибка при изменении статуса клиента: {response.text}")
            return None
        
    def get_lead_by_id(self, id):
        url = f"{self.url}/leads/get-by-id?id={id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Ошибка при получении данных: {response.text}"
        
        
    # inner api
    def get_movements(self):
        SERVER_URL = 'https://domoplaner.ru/supereble-api/leads/movements'
        dt_movement_from, dt_movement_to = get_dt_movement_from_and_to(Config.REMIND_LEAD_FROM_VICTORY_PERIOD)
        url = f"{SERVER_URL}/get-raw?dt_movement_from={dt_movement_from}&dt_movement_to={dt_movement_to}"
        response = requests.get(url, headers=self.inner_headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Ошибка при получении данных: {response.text}"
    
    
