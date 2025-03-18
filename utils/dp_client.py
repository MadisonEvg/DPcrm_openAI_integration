import requests
from config import Config

class DpCRMClient:
    def __init__(self):
        self.url = Config.DPCRM_API_URL
        self.access_token = Config.DPCRM_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.status_first = self.get_users_status_by_title(Config.DPCRM_FIRST_STATUS)
        self.status_success = self.get_users_status_by_title(Config.DPCRM_SUCCESS_STATUS)
        self.status_archive = self.get_users_status_by_title(Config.DPCRM_ARCHIVE_STATUS)
        
    def get_users_status_by_title(self, title):
        statuses = self.get_users_statuses()['statuses']
        status_id = next((status['id'] for status in statuses if status['title'] == title), None)
        return status_id
    
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
            self.change_user_status(user['lead_id'], self.status_first)
            response = self.get_lead_by_phone(phone)
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
        url = f"{self.url}/leads"
        payload = {
            "phone": phone,
            "name": f"Контакт {phone}",
            # "status_id": self.status_first
        }
        response = requests.post(url, json=payload, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Ошибка при получении данных: {response.text}"
        
    def change_user_status(self, user_id, status_id):
        url = f"{self.url}/leads/{user_id}/status"
        payload = {
            "status_id": status_id
        }

        response = requests.patch(url, json=payload, headers=self.headers)

        if response.status_code == 200:
            result = response.json()
            print(f"Статус пользователя изменён на {result}.")
            return response.json()
        else:
            print(f"Ошибка при изменении статуса клиента: {response.text}")
            return None
    
    def change_lead_to_success_status(self, user_id):
        self.change_user_status(user_id, self.status_success)