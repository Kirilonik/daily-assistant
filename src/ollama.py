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
        'model': 'wizard-vicuna-uncensored:13b',
        'prompt': prompt,
        'stream': False,
        'temperature': 0,
        'max_tokens': 182,
    })
    response.raise_for_status()
    
    result = ""
    json_response = response.json()
    if 'response' in json_response:
        result = json_response['response']
    else:
        print(f"Неожиданный формат ответа: {json_response}")
    print(result)
    return result