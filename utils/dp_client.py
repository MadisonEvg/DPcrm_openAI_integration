import requests
from config import Config

class AmoCRMClient:
    def __init__(self):
        self.url = Config.AMOCRM_URL
        self.access_token = Config.AMOCRM_ACCESS_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_deal_by_id(self, lead_id):

        url = f"{self.url}/api/v4/leads/{lead_id}"
        response = requests.get(url, headers=self.headers)

        if response.status_code == 200:
            lead_data = response.json()
            status_id = lead_data.get("status_id")
            return status_id
        else:
            return f"Ошибка при получении данных: {response.text}"


    def change_deal_status(self, deal_id, new_status_id):
        url = f"{self.url}/api/v4/leads/{deal_id}"
        payload = {
            "status_id": new_status_id
        }

        response = requests.patch(url, json=payload, headers=self.headers)

        if response.status_code == 200:
            print(f"Статус сделки с ID {deal_id} успешно обновлен на {new_status_id}.")
            return response.json()
        else:
            print(f"Ошибка при изменении статуса сделки: {response.text}")
            return None

    def get_contact_phone(self, contact_id):

        url = f"{self.url}/api/v4/contacts/{contact_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            try:
                contact_data = response.json()
                for field in contact_data.get("custom_fields_values", []):
                    if field.get("field_code") == "PHONE":
                        phone = field.get("values", [])[0].get("value", "").lstrip('+')
                        return phone if phone else "Телефон не найден"
            except ValueError:
                print("Ошибка: ответ не в формате JSON. Текст ответа:", response.text)
                return None
        else:
            print("Ошибка при получении данных:", response.text)
            return None