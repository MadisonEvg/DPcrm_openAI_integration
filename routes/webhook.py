from flask import Blueprint, request, jsonify
import logging
from utils.wazzup_client import WazzupClient
from utils.openai_client import OpenAIClient
from utils.statistics_manager import StatisticsManager
from utils.reminder_tasks import schedule_task


webhook_bp = Blueprint('webhooks', __name__)
wazzup_client = WazzupClient()
openai_client = OpenAIClient()
stats_manager = StatisticsManager()
       

@webhook_bp.route('/webhooks', methods=['POST'])
async def webhook():
    
    try:
        data = request.get_json(silent=True)
        print(f"Получен вебхук: {data}")

        if data and data.get("test") == True:
            print("Тестовый запрос от Wazzup обработан успешно")
            return jsonify({"status": "ok"}), 200

        if not data or "messages" not in data:
            return jsonify({"status": "ok"}), 200

        for message in data["messages"]:
            if message.get("type") == "text" and message.get("status") == "inbound":
                client_message = message.get("text")
                chat_id = message.get("chatId")
                
                if not client_message or not chat_id:
                    # print("Нет текста или chatId, игнорируем")
                    continue
                print(f"Received message: {client_message}")
                
                final_response, input_tokens, output_tokens = await openai_client.create_gpt4o_response(
                    client_message, chat_id
                )
                
                wazzup_client.send_message(chat_id, final_response)
                schedule_task(chat_id)  # Планируем задачу в фоне
                stats_manager.update_statistics(
                    input_tokens_o=input_tokens,
                    output_tokens_o=output_tokens,
                    is_successful=False,
                    phone_number=chat_id
                )
            
        return jsonify({"status": "ok"}), 200  # Отправляем успешный ответ

    except Exception as e:
        print(f"Ошибка при обработке вебхука: {str(e)}")
        return '', 200
