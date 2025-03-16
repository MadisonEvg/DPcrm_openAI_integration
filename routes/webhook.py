from flask import Blueprint, request, jsonify
import logging
from utils.wazzup_client import WazzupClient
from utils.openai_client import OpenAIClient
from utils.statistics_manager import StatisticsManager
from utils.reminder_tasks import schedule_task


webhook_bp = Blueprint('webhooks', __name__)
wazzup_client = WazzupClient()
openai_client = OpenAIClient()
       

@webhook_bp.route('/webhooks', methods=['POST'])
async def webhook():
    
    # logging.info(f"Received webhook: {request.form}")
    # logging.info(f"Request Headers: {request.headers}")
    # wazzup_client.send_message('a', 'Hello!!!!')
    
    try:
        data = request.get_json(silent=True)
        # print(f"Получен вебхук: {data}")

        if data and data.get("test") == True:
            # print("Тестовый запрос от Wazzup обработан успешно")
            return jsonify({"status": "ok"}), 200  # Отправляем успешный ответ

        if not data or "messages" not in data:
            # print("Не сообщение или пустой запрос, игнорируем")
            return jsonify({"status": "ok"}), 200  # Отправляем успешный ответ

        for message in data["messages"]:
            if message.get("type") == "text" and message.get("status") == "inbound":
                client_message = message.get("text")
                chat_id = message.get("chatId")
                
                if not client_message or not chat_id:
                    # print("Нет текста или chatId, игнорируем")
                    continue

                logging.info(f"Received message: {client_message}")
                print('---------------------')
                print(f"Received message: {client_message}")
                print('---------------------')
                
                # Запрашиваем ответ от GPT-4, передавая результат поиска из векторной базы данных
                final_response, input_tokens_o, output_tokens_o = await openai_client.create_gpt4o_response(
                    client_message, chat_id
                )
                
                wazzup_client.send_message(chat_id, final_response)
                print('schedule_task runned!!!  1')
                schedule_task(chat_id)  # Планируем задачу в фоне
                print('schedule_task runned!!!  2')
        return jsonify({"status": "ok"}), 200  # Отправляем успешный ответ

    except Exception as e:
        print(f"Ошибка при обработке вебхука: {str(e)}")
        return '', 200
