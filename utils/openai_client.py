import json
import logging
import asyncio
import httpx
from datetime import datetime
from config import Config
from utils.helpers import count_tokens
from models.conversation_manager import ConversationManager
from openai import AsyncOpenAI


class OpenAIClient:
    
    def __init__(self):
        transport = httpx.AsyncHTTPTransport(proxy=Config.PROXY_URL)
        http_async_client = httpx.AsyncClient(transport=transport)
        self._client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY, http_client=http_async_client)
        self._conversation_manager = ConversationManager()

    async def _ask_openai(self, messages, model):
        try:
            response = await self._client.chat.completions.create(
                temperature=Config.TEMPERATURE,
                model=model,
                messages=messages
            )
        except Exception as e:
            print(f"Ошибка при обращении к OpenAI: {e}")
            return "Произошла ошибка при обработке запроса.", 0, 0
        response_text = response.choices[0].message.content.strip()
        input_tokens, output_tokens = count_tokens(messages, response_text)
        print(f"Ответ от {model}: {response_text}")
        print(f"Входных токенов: {input_tokens}, Выходных токенов: {output_tokens}")
        return response_text, input_tokens, output_tokens
    
    async def create_gpt4o_response(self, question, chat_id):
        # Добавляем новое сообщение пользователя
        self._conversation_manager.add_user_message(chat_id, question)
        
        # Ограничиваем историю, чтобы не превышать лимит токенов
        self._conversation_manager.trim_history(chat_id, max_tokens=Config.MAX_TOKENS)
        
        # Отправляем всю историю вместе с новым сообщением для GPT
        task_response = asyncio.create_task(self._ask_openai(
            self._conversation_manager.get_history(chat_id),
            model=Config.MODEL_GPT4O
        ))
        task_delay = asyncio.create_task(asyncio.sleep(Config.ASSISTANT_DELAY))
        gpt4_response, input_tokens, output_tokens = await task_response
        await task_delay
        
        return gpt4_response, input_tokens, output_tokens
