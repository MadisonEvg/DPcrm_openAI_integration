import json
import re
import tiktoken
from datetime import datetime, timedelta

TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

def get_dt_movement_from_and_to(delta_hours=24):
    dt_to = datetime.now() - timedelta(hours=2) # ищем лидов которые уже минимум 2 часа не отвечают
    dt_from = dt_to - timedelta(hours=delta_hours) # с какого времени (даты) ещём лидов (за сутки, за неделю)
    return dt_from.strftime(TIME_FORMAT), datetime.now().strftime(TIME_FORMAT)


def count_tokens(messages, response, model="gpt-4"):
    encoding = tiktoken.encoding_for_model(model)
    num_tokens = 0
    for message in messages:
        num_tokens += len(encoding.encode(message["content"]))
    return num_tokens, len(encoding.encode(response))


# def count_tokens(messages, response):
#     prompt = " ".join([msg['content'] for msg in messages])
#     input_tokens = len(prompt.split())
#     output_tokens = len(response.split())
#     return input_tokens, output_tokens


def trim_conversation_history(history, max_tokens=3500):
    total_tokens = sum(len(msg['content'].split()) for msg in history)

    while total_tokens > max_tokens:
        if len(history) > 2:
            removed = history.pop(2)  # Удаляем третье сообщение (сохраняем первое системное и время)
            total_tokens -= len(removed['content'].split())
        else:
            break


def extract_phone_from_text(text):
    phone_regex = r"(\+?\d{1,4}[^\da-zA-Z]{0,3})?(\(?\d{1,4}\)?[^\da-zA-Z]{0,3})?(\d{1,4}[^\da-zA-Z\d]{0,3}\d{1,4}[^\da-zA-Z\d]{0,3}\d{1,4})"

    match = re.search(phone_regex, text)

    # Проверка на минимальное количество цифр
    if match:
        phone_digits = re.sub(r'\D', '', match.group())  # Убираем все нецифровые символы
        if len(phone_digits) >= 7:  # Проверяем, что цифр в номере хотя бы 7
            print(f"Найден номер телефона: {match.group()}")
            return True
        else:
            print("Ошибка: номер слишком короткий.")
            return False
    else:
        print("Номер телефона не найден.")
        return False

def load_json_data():
    with open('parsed_data_1.json', 'r', encoding='utf-8') as file:
        parsed_data_1 = json.load(file)
    return parsed_data_1