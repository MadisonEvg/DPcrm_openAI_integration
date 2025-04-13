from flask import Blueprint, request, jsonify
import logging
import threading
from utils.wazzup_client import WazzupClient
from utils.openai_client import OpenAIClient, AUDIO_PHOTO_RESPOSE
from utils.statistics_manager import StatisticsManager
from utils.reminder_tasks import schedule_task, cancel_task
from utils.dp_client import DpCRMClient
from models.conversation_manager import ConversationManager, PromptType
from logger_config import logger
import asyncio
from utils.async_loop import loop
from config import Config


webhook_bp = Blueprint('webhooks', __name__)
wazzup_client = WazzupClient()
openai_client = OpenAIClient()
stats_manager = StatisticsManager()
dp_crm_client = DpCRMClient()
conversation_manager = ConversationManager()

# Хранилище сообщений в памяти
user_messages = {}
user_timers = {}

       
async def send_response(chat_id):
    """Отправляет накопленные сообщения пользователю"""
    messages = user_messages.pop(chat_id, [])
    if messages:
        combined_message = "\n".join(messages)
        logger.info(f"---------- Sending response to {chat_id}: {combined_message}")

        lead = dp_crm_client.get_or_create_lead_by_phone(chat_id)    
        conversation_manager.initialize_conversation(chat_id, lead['source_id'])

        final_response, input_tokens, output_tokens = await openai_client.create_gpt4o_response(
            combined_message, chat_id
        )
        
        response_from_mini = await openai_client.get_gpt4o_mini_response(chat_id, PromptType.MINI_DIALOG)
        logger.info(f'--webhook-- response_from_mini: {response_from_mini}')
        await cancel_task(chat_id)
        if response_from_mini.lower() == "статус ожидает звонка":
            logger.info(f"--webhook-- изменили на статус ожидает звонка")
            dp_crm_client.change_lead_to_success_status(lead['id'])
            # asyncio.run_coroutine_threadsafe(delayed_change_to_success_status(lead['id']), loop)
        elif response_from_mini.lower() == "статус презентация отправлена":
            logger.info(f"--webhook-- изменили на статус презентация отправлена")
            dp_crm_client.change_lead_to_link_received_status(lead['id'])
        elif response_from_mini.lower() == "неуспешный диалог":
            logger.info(f"--webhook-- изменили на статус неуспешный диалог")
            dp_crm_client.change_lead_to_archive_status(lead['id'], lead['status'])
        elif dp_crm_client.is_client_allowed_to_remind(lead['status']):
            logger.info(f"--webhook-- запускаем напоминалку")
            logger.info(f"--webhook-- schedule_task {chat_id}, {lead['id']}")
            await schedule_task(chat_id, lead['id'])  # Планируем задачу в фоне
        else:
            logger.info(f"--webhook-- напоминалка запрещена!!")
            logger.warning(f"запрещено отсылать напоминание из-за статуса: {lead['status']}")
        final_response = final_response.replace('[ссылка]', '')
        wazzup_client.send_message(chat_id, final_response)
        
        stats_manager.update_statistics(
            input_tokens_o=input_tokens,
            output_tokens_o=output_tokens,
            is_successful=False,
            phone_number=chat_id
        )
        
# async def delayed_change_to_success_status(user_id):
#     """Ждет минуту, затем меняем статус клиента"""
#     await asyncio.sleep(60)
#     logger.info(f"--webhook-- изменили на статус ожидает звонка")
#     dp_crm_client.change_lead_to_success_status(user_id)
        
async def delayed_send(user_id):
    """Ждет 10 секунд, затем отправляет накопленные сообщения"""
    await asyncio.sleep(10)
    await send_response(user_id)

@webhook_bp.route('/webhooks', methods=['POST'])
async def webhook():
    logger.info('--webhooks--')
    try:
        data = request.get_json(silent=True)
        logger.info(f"Получен вебхук: {data}")
        if data and data.get("test") == True:
            logger.info("Тестовый запрос от Wazzup обработан успешно")
            return jsonify({"status": "ok"}), 200
        
        if data and data.get("webhook_test"):
            logger.info(f"Проверка webhook'a!!!!!!!!!!!! {data.get('message')}")
            return jsonify({"status": "ok"}), 200
        
        if not data or 'messages' not in data:
            logger.info(f"--webhooks-- data: {data} or 'messages not in data' {'messages' not in data}")
            return jsonify({"status": "ok"}), 200

        for message in data["messages"]:
            if message.get("channelId") != Config.WAZZUP_CHANNEL_ID:
                return jsonify({"status": "ok"}), 200
        
            if (message.get("chatType") == 'whatsgroup'):
                return jsonify({"status": "ok"}), 200
            
            if (message.get("type") == 'audio' or message.get("type") == 'image') and message.get("status") == "inbound":
                chat_id = message.get("chatId")
                lead = dp_crm_client.get_or_create_lead_by_phone(chat_id)
                # skip not victory
                if lead['source_id'] not in (7269, 9198):
                    logger.info(f"--webhooks-- skipping not victory lead")
                    return jsonify({"status": "ok"}), 200
                
                if not dp_crm_client.is_client_status_valid(lead['status']):
                    logger.info(f"--webhooks-- lead {chat_id} is ignoring {lead['status']}")
                    return jsonify({"status": "ok"}), 200
                
                wazzup_client.send_message(chat_id, AUDIO_PHOTO_RESPOSE)
                return jsonify({"status": "ok"}), 200
            
            if message.get("type") == "text" and message.get("status") == "inbound":
                client_message = message.get("text")
                chat_id = message.get("chatId")
                
                lead = dp_crm_client.get_or_create_lead_by_phone(chat_id)
                # skip not victory
                if lead['source_id'] not in (7269, 9198):
                    logger.info(f"--webhooks-- skipping not victory lead")
                    return jsonify({"status": "ok"}), 200 
                
                if not client_message or not chat_id:
                    logger.info(f"--webhooks-- Нет текста или chatId, игнорируем")
                    continue
                
                if not dp_crm_client.is_client_status_valid(lead['status']):
                    logger.info(f"--webhooks-- lead {chat_id} is ignoring {lead['status']}")
                #     # wazzup_client.send_message(chat_id, f"Вы в игноре! статус_id({lead['status']})")
                #     # lead status reset!
                #     # dp_crm_client.change_user_status(lead['id'], dp_crm_client.status_first)
                    return jsonify({"status": "ok"}), 200
                
                # Добавляем сообщение в буфер
                if chat_id not in user_messages:
                    user_messages[chat_id] = []
                user_messages[chat_id].append(client_message)

                # Если уже был запущен таймер, сбрасываем его
                if chat_id in user_timers:
                    user_timers[chat_id].cancel()

                # Устанавливаем новый таймер
                user_timers[chat_id] = asyncio.run_coroutine_threadsafe(delayed_send(chat_id), loop)
                
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука: {e}", exc_info=True)
        return '', 200
