import json
import requests

async def generate_chat_response(prompt, temp_msg, context):
    result = ""
    try:
        result = await query_ollama(prompt)
        await context.bot.editMessageText(text=result, chat_id=temp_msg.chat_id, message_id=temp_msg.message_id)
        if not result:
            print("Пустой ответ модели")
            await context.bot.editMessageText(text='😔 Я не знаю что ответить. Попробуй что-то другое',
                                              chat_id=temp_msg.chat_id, message_id=temp_msg.message_id)
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        await context.bot.editMessageText(text='😔 Что-то пошло не так. Попробуй что-то другое',
                                          chat_id=temp_msg.chat_id, message_id=temp_msg.message_id)
    return result

async def query_ollama(prompt):
    response = requests.post('http://localhost:11434/api/generate', json={
        # 'model': 'qwen2:0.5b',
        'model': 'gemma2:2b',
        # 'model': 'llama3.1:latest',
        'prompt': prompt,
        'stream': True,
    })
    response.raise_for_status()
    # Обрабатываем ответ построчно
    result = ""
    for line in response.iter_lines():
        if line:
            try:
                json_line = json.loads(line)
                if 'response' in json_line:
                    result += json_line['response']
            except json.JSONDecodeError:
                print(f"Не удалось разобрать строку JSON: {line}")
    return result