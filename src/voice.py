import os
from pathlib import Path
import tempfile
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from TTS.api import TTS
from ollama import generate_chat_response, query_ollama
import torch

# Генерируем аудио ответ
async def generate_voice_response(prompt, temp, context, update):
    chat_out = await query_ollama(prompt)
    chat_out = chat_out.replace("*", "").replace("**", "")
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio:
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        print(f"device to generate voice response: {device}")
        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        tts.to(device)
        
        user_id = update.message.from_user.id
        user_sample = f'samples\{user_id}_voice_sample.wav'
        speaker_wav = user_sample if os.path.exists(user_sample) else "samples\sample_voice.wav"
        
        tts.tts_to_file(text=chat_out,
                        file_path=temp_audio.name,
                        speaker_wav=speaker_wav,
                        language="ru")
        await update.message.reply_voice(temp_audio.name)
    try:
        os.unlink(temp_audio.name)
    except Exception as e:
        print(e)
    return chat_out


# Преобразуем аудио в текст
def transcribe_audio(audio):
    try:
        # Преобразуем аудио в текст
        text = sr.Recognizer().recognize_google(audio, language="ru-RU")
        return text
    except sr.UnknownValueError:
        return "Извините, не удалось распознать речь"
    except sr.RequestError as e:
        return f"Ошибка сервиса распознавания речи: {e}"


# Получаем текст из голосового сообщения
async def get_text_from_message(update, context):
    transcribed_text = ""
    with tempfile.TemporaryDirectory() as tmp_dir:
        voice_path = Path(tmp_dir) / "voice.wav"
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        await voice_file.download_to_drive(voice_path)
        AudioSegment.from_file(voice_path).export(voice_path, format="wav")
        with sr.AudioFile(str(voice_path)) as source:
            transcribed_text = transcribe_audio(sr.Recognizer().record(source))
    return transcribed_text