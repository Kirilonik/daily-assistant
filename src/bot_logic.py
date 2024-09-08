from telegram import *
from telegram.ext import *
from dotenv import load_dotenv
import os
from ollama import generate_chat_response
from storage import ChatMode, user_storage
from voice import get_text_from_message, generate_voice_response


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_mode = user_storage.get_chat_mode(update.message.chat_id)
    chat_history = user_storage.get_chat_history(update.message.chat_id)
    last_message = chat_history[-1] if chat_history else ""
    temp = await update.message.reply_text("Думоем...")

    if (update.message.text != None):
        chat_in = update.message.text
    else:
        chat_in = await get_text_from_message(update, context)

    prompt_template = os.getenv('PROMPT_TEMPLATE')
    prompt = prompt_template.format(chat_in=chat_in, last_message=last_message)
    if chat_mode == ChatMode.TEXT:
        await update.message.chat.send_action(action="TYPING")
        chat_out = await generate_chat_response(prompt, temp, context=context)
    elif chat_mode == ChatMode.VOICE:
        await update.message.chat.send_action(action="RECORD_VOICE")
        chat_out = await generate_voice_response(prompt, temp, context=context, update=update)
        await update.message.delete()


    user_storage.add_message(chat_id, chat_in, chat_out)