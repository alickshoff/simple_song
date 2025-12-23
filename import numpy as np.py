import numpy as np
import scipy.io.wavfile as wavfile
import os

# Создаем простой тестовый файл
sample_rate = 44100
duration = 5
t = np.linspace(0, duration, int(sample_rate * duration), False)
audio = 0.5 * np.sin(2 * np.pi * 440 * t)  # Тон 440 Гц

# Нормализуем и конвертируем
audio = audio / np.max(np.abs(audio))
audio_int16 = np.int16(audio * 32767)

# Сохраняем
output_path = 'static/generated_audio/test_audio.wav'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
wavfile.write(output_path, sample_rate, audio_int16)
print(f'Создан тестовый файл: {output_path}')