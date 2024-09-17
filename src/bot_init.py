from bot_logic import handle_message
from dotenv import load_dotenv
import os
from storage import ChatMode, user_storage
from telegram import *
from telegram.ext import *
from storage import ChatMode, user_storage
from pydub import AudioSegment


async def new_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_storage.create_user(update.message.from_user.id, update.message.from_user.username)
    user_storage.add_message(update.message.from_user.id, update.message.from_user.username, "Новый чат", "Новый чат")
    await update.message.reply_text(f'Даров, {update.effective_user.first_name}. Я типа бот. Спрашивай что-нибудь.')

async def start_voice_chat(update: Update, context: CallbackContext) -> None:
    # query = update.callback_query
    user_storage.set_chat_mode(update.effective_sender.id, update.effective_sender.username, ChatMode.VOICE)
    # await query.answer()
    await update.message.reply_text('🗣️ Голосовой чат включен')

async def start_text_chat(update: Update, context: CallbackContext) -> None:
    # query = update.callback_query
    user_storage.set_chat_mode(update.effective_sender.id, update.effective_sender.username, ChatMode.TEXT)
    # await query.answer()
    await update.message.reply_text('💬 Текстовый чат включен')


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("assistant", "Задать вопрос ассистенту"),
        BotCommand("new_chat", "Начать новый чат"),
        BotCommand("change_voice_sample", "Изменить образец голоса"),
        BotCommand("start_voice_chat", "Включить голосовой чат"),
        BotCommand("start_text_chat", "Включить текстовый чат"),
    ])
    print("Бот запущен")


async def change_voice_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Пожалуйста, отправьте новый голосовой образец длительностью не менее 30 секунд.')
    context.user_data['awaiting_voice_sample'] = True


async def handle_voice_sample(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('awaiting_voice_sample'):
        voice = update.message.voice
        if voice.duration < 30:
            await update.message.reply_text('Голосовой образец должен быть длительностью не менее 30 секунд. Пожалуйста, отправьте более длинное сообщение.')
            return

        file = await context.bot.get_file(voice.file_id)
        
        file_name = f'samples\{update.message.from_user.id}_voice_sample'
        await file.download_to_drive(f'{file_name}.ogg')

        # Конвертация .ogg в .wav
        AudioSegment.from_ogg(f'{file_name}.ogg').export(f'{file_name}.wav', format='wav')

        os.remove(f'{file_name}.ogg')
        context.user_data['awaiting_voice_sample'] = False
        await update.message.reply_text('Голосовой образец успешно обновлен!')


if __name__ == '__main__':
    # Загрузка переменных из файла .env
    load_dotenv(dotenv_path='environment.env')
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

    app.add_handler(CommandHandler("new_chat", new_chat))
    app.add_handler(CommandHandler("assistant", handle_message))
    app.add_handler(CommandHandler("change_voice_sample", change_voice_sample))
    app.add_handler(CommandHandler("start_voice_chat", start_voice_chat))
    app.add_handler(CommandHandler("start_text_chat", start_text_chat))
    app.add_handler(MessageHandler(filters.VOICE & filters.ChatType.PRIVATE, handle_voice_sample))
    app.run_polling()

    
