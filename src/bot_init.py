from bot_logic import handle_message
from dotenv import load_dotenv
import os
from storage import ChatMode, user_storage
from telegram import *
from telegram.ext import *


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_storage.create_user(update.message.chat_id)
    await update.message.reply_text(f'Даров, {update.effective_user.first_name}. Я типа бот. Спрашивай что-нибудь.',
                                    reply_markup=main_menu_keyboard())

async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_storage.create_user(update.message.chat_id)
    user_storage.add_message(update.message.chat_id, "Новый чат", "Новый чат")
    await update.message.reply_text(f'Даров, {update.effective_user.first_name}. Я типа бот. Спрашивай что-нибудь.',
                                    reply_markup=main_menu_keyboard())

async def start_voice_chat(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_storage.set_chat_mode(query.message.chat_id, ChatMode.VOICE)
    await query.answer()
    await query.message.reply_text('🗣️ Голосовой чат включен')

async def start_text_chat(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_storage.set_chat_mode(query.message.chat_id, ChatMode.TEXT)
    await query.answer()
    await query.message.reply_text('💬 Текстовый чат включен')


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("/new_chat", "Начать новый чат"),
    ])
    print("Бот запущен")


def main_menu_keyboard():
    keyboard = [[InlineKeyboardButton('💬 Текстовый чат', callback_data='text')],
                [InlineKeyboardButton('🗣️ Голосовой чат', callback_data='voice')]]
    return InlineKeyboardMarkup(keyboard)


if __name__ == '__main__':
    # Загрузка переменных из файла .env
    load_dotenv()
    # Теперь вы можете обращаться к переменным через os.getenv()
    bot_token = os.getenv('BOT_TOKEN')

    # Создаем бота телеграмма
    app = (
        ApplicationBuilder()
        .token(bot_token)
        .concurrent_updates(4)
        .post_init(post_init)
        .read_timeout(60)
        .write_timeout(60)
        .build()
    )

    # Регистрируем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new_chat", new_chat))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_message))
    # app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # app.add_handler(MessageHandler(filters.VIDEO, handle_video))
    app.add_handler(CallbackQueryHandler(start_voice_chat, pattern='voice'))
    app.add_handler(CallbackQueryHandler(start_text_chat, pattern='text'))

    app.run_polling()
