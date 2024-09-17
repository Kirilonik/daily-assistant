from telegram import *
from telegram.ext import *
from dotenv import load_dotenv
import os
from ollama import generate_chat_response
from storage import ChatMode, user_storage
from voice import get_text_from_message, generate_voice_response


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверяем, что сообщение не было переслано
    if update.message.forward_origin is not None:
        return
    user_id = update.message.from_user.id
    username = update.message.from_user.username or update.message.from_user.first_name

    # Обновляем или создаем пользователя с именем пользователя
    user = user_storage.get_user(user_id)
    if user:
        if user['username'] != username:
            user_storage.update_username(user_id, username)
    else:
        user_storage.create_user(user_id, username)
    
    # Проверяем, не обрабатывается ли уже запрос от этого пользователя
    if user_storage.get_processing_state(user_id):
        await update.message.reply_text("Пожалуйста, подождите. Ваш предыдущий запрос обрабатывается.")
        return

    # Устанавливаем флаг, что запрос обрабатывается
    user_storage.set_processing_state(user_id, True)

    try:
        chat_mode = user_storage.get_chat_mode(user_id, username)
        chat_history = user_storage.get_chat_history(user_id)
        # last_message = chat_history[-1] if chat_history else ""
        temp = await update.message.reply_text("Думоем...")

        if (update.message.text != None):
            chat_in = update.message.text.replace('/assistant', '').strip()
        else:
            if update.message.reply_to_message and update.message.reply_to_message.voice:
                chat_in = await get_text_from_message(update.message.reply_to_message, context)
            else:
                await update.message.reply_text("Пожалуйста, укажите запрос после команды /assistant или отправьте голосовое сообщение и ответье на него с командой /assistant.")

        
        prompt = "Твой ответ должен быть на русском языке. \n" + chat_in
        print(f'user_id: {user_id}')
        print(f'prompt: {prompt}')
        print(f'chat_mode: {chat_mode}')
        # print(f'last_message: {last_message}')


        if chat_mode == ChatMode.TEXT:
            await update.message.chat.send_action(action="TYPING")
            chat_out = await generate_chat_response(prompt, temp, context=context)
            await update.message.reply_text(chat_out)
        elif chat_mode == ChatMode.VOICE:
            await update.message.chat.send_action(action="RECORD_VOICE")
            chat_out = await generate_voice_response(prompt, temp, context=context, update=update)
            await update.message.reply_text("🗣️\n" + chat_out)
        
        print("--------------------------------")
        await context.bot.delete_message(chat_id=temp.chat_id, message_id=temp.message_id)
        user_storage.add_message(user_id, username, chat_in, chat_out)
        return chat_out
    finally:
        # Сбрасываем флаг после завершения обработки запроса
        user_storage.set_processing_state(user_id, False)