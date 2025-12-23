from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
import uuid
import shutil
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем папки
os.makedirs("static", exist_ok=True)
os.makedirs("static/generated_audio", exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Модель для параметров генерации
class GenerateParams(BaseModel):
    genre: str
    mood: str
    duration: int
    tempo: int
    instruments: str
    lyrics: str

# ВАЖНО: Замените на ваш реальный API ключ от Stability AI
# Получите ключ на https://platform.stability.ai/
STABILITY_API_KEY = "sk-51SVipk6u14mVK5C8bdTry8cIWi7hYBarJylGJHL2VL91czI"
STABLE_AUDIO_URL = "https://api.stability.ai/v2beta/audio/stable-audio-2/text-to-audio"

OUTPUT_DIR = "static/generated_audio"

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/generate")
async def generate_music(params: GenerateParams):
    try:
        # Проверяем API ключ
        if STABILITY_API_KEY == "sk-51SVipk6u14mVK5C8bdTry8cIWi7hYBarJylGJHL2VL91czI":
            raise HTTPException(
                status_code=400, 
                detail="API ключ не настроен. Получите ключ на platform.stability.ai"
            )
        
        # Строим промпт для Stable Audio
        prompt = f"A {params.mood} {params.genre} song with instruments: {params.instruments}, tempo {params.tempo} BPM, duration {params.duration} seconds"
        if params.lyrics:
            prompt += f", with lyrics: {params.lyrics}"

        # Запрос к Stability AI API
        response = requests.post(
            STABLE_AUDIO_URL,
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "audio/*"
            },
            data={
                "prompt": prompt,
                "duration": params.duration,
                "model": "stable-audio-2.5",
                "output_format": "wav"
            }
        )

        if response.status_code != 200:
            error = response.json() if response.content else {"detail": "Unknown error"}
            raise HTTPException(
                status_code=response.status_code, 
                detail=f"Stability AI Error {response.status_code}: {error}"
            )

        # Сохраняем аудио
        output_file = f"{uuid.uuid4()}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_file)
        with open(output_path, "wb") as f:
            f.write(response.content)

        # Возвращаем URL аудио
        audio_url = f"/static/generated_audio/{output_file}"
        return {"audio_url": audio_url}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Альтернативный эндпоинт для тестирования (без реального API)
@app.post("/generate-demo")
async def generate_music_demo(params: GenerateParams):
    """Демо-режим без реального API ключа"""
    try:
        # Генерируем демо-аудио URL (используем тестовый файл)
        # Создаем тестовый файл, если его нет
        test_file = "test_audio.wav"
        test_path = os.path.join(OUTPUT_DIR, test_file)
        
        if not os.path.exists(test_path):
            # Создаем заглушку
            import wave
            import struct
            import math
            
            # Создаем простой синусоидальный тон
            sample_rate = 44100
            duration = min(params.duration, 5)  # Ограничиваем для демо
            frequency = 440  # A4
            
            with wave.open(test_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                
                # Генерируем простой тон
                for i in range(int(sample_rate * duration)):
                    value = int(32767.0 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    data = struct.pack('<h', value)
                    wav_file.writeframes(data)
        
        audio_url = f"/static/generated_audio/{test_file}"
        return {
            "audio_url": audio_url,
            "message": "Демо-режим: Используется тестовый аудиофайл. Для реальной генерации настройте API ключ."
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Очистка старых файлов (раз в день можно запускать)
import atexit
import glob
import time

def cleanup_old_files():
    """Удаляем файлы старше 24 часов"""
    try:
        now = time.time()
        for file_path in glob.glob(os.path.join(OUTPUT_DIR, "*.wav")):
            if os.path.getmtime(file_path) < now - 24 * 3600:
                os.remove(file_path)
    except:
        pass  # Игнорируем ошибки очистки

atexit.register(cleanup_old_files)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)