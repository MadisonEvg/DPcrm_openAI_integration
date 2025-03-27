from flask import Blueprint, request, jsonify
import logging
from utils.wazzup_client import WazzupClient
from utils.openai_client import OpenAIClient
from utils.statistics_manager import StatisticsManager
from utils.reminder_tasks import schedule_task, cancel_task
from utils.dp_client import DpCRMClient
from models.conversation_manager import ConversationManager


webhook_bp = Blueprint('webhooks', __name__)
wazzup_client = WazzupClient()
openai_client = OpenAIClient()
stats_manager = StatisticsManager()
dp_crm_client = DpCRMClient()
conversation_manager = ConversationManager()
       

@webhook_bp.route('/webhooks', methods=['POST'])
async def webhook():
    print('------------------------------------------------')
    try:
        data = request.get_json(silent=True)
        # print(f"Получен вебхук: {data}")
        
        if data and data.get("test") == True:
            print("Тестовый запрос от Wazzup обработан успешно")
            return jsonify({"status": "ok"}), 200

        if not data or "messages" not in data:
            return jsonify({"status": "ok"}), 200

        for message in data["messages"]:
            if message.get("type") == "text" and message.get("status") == "inbound":
                client_message = message.get("text")
                chat_id = message.get("chatId")
                lead = dp_crm_client.get_or_create_lead_by_phone(chat_id)
                conversation_manager.initialize_conversation(chat_id, lead['source_id'])

                if not dp_crm_client.is_client_status_valid(lead['status']):
                    wazzup_client.send_message(chat_id, f"Вы в игноре! статус_id({lead['status']})")
                    # lead status reset!
                    # dp_crm_client.change_user_status(lead['id'], dp_crm_client.status_first)
                    return jsonify({"status": "ok"}), 200
                
                if not client_message or not chat_id:
                    print("Нет текста или chatId, игнорируем")
                    continue

                
                final_response, input_tokens, output_tokens = await openai_client.create_gpt4o_response(
                    client_message, chat_id
                )
                
                if final_response.strip().endswith("статус ожидает звонка"):
                    final_response = final_response.rstrip().removesuffix("статус ожидает звонка").rstrip()
                    dp_crm_client.change_lead_to_success_status(lead['id'])
                    cancel_task(chat_id)
                elif final_response.strip().endswith("неуспешный диалог"):
                    final_response = final_response.rstrip().removesuffix("неуспешный диалог").rstrip()
                    dp_crm_client.change_lead_to_success_status(lead['id'])
                    dp_crm_client.change_user_status(lead['id'], dp_crm_client.status_archive)
                    cancel_task(chat_id)
                else:
                    print('!!!!!!!!!!!!!!!!!!!')
                    schedule_task(chat_id, lead['id'])  # Планируем задачу в фоне
                
                wazzup_client.send_message(chat_id, final_response)
                
                stats_manager.update_statistics(
                    input_tokens_o=input_tokens,
                    output_tokens_o=output_tokens,
                    is_successful=False,
                    phone_number=chat_id
                )
            
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        print(f"Ошибка при обработке вебхука: {str(e)}")
        return '', 200
