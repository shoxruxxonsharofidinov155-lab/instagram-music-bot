import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import FSInputFile
from yt_dlp import YoutubeDL

# O'zingizning bot tokeringizni kiriting
TOKEN = "8632342746:AAHYorlOiRZUR59M9r7_IQgkR4XnMYG0ry0"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Vaqtinchalik fayllarni xavfsiz o'chirish uchun funksiya
def cleanup(*file_paths):
    for path in file_paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Faylni o'chirishda xatolik: {e}")

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Salom! Menga **YouTube** yoki **Instagram** havolasini yuboring.\n\nYouTube uchun video va MP3 fayllarini, Instagram uchun esa videoni yuklab beraman.")

@dp.message(F.text)
async def handle_social_links(message: types.Message):
    url = message.text.strip()
    
    is_youtube = "youtube.com" in url or "youtu.be" in url
    is_instagram = "instagram.com" in url
    
    if not (is_youtube or is_instagram):
        await message.answer("⚠️ Iltimos, faqat YouTube yoki Instagram havolasini yuboring.")
        return

    status_msg = await message.answer("⏳ Havola tekshirilmoqda va fayllar tayyorlanmoqda, iltimos kuting...")

    video_path = None
    audio_path = None

    try:
        if is_youtube:
            # 1. YouTube videoni yuklash (Telegram 50MB cheklovini hisobga olgan holda)
            ydl_video_opts = {
                'format': 'best[filesize<=50M]/best',
                'outtmpl': 'downloads/%(id)s_video.%(ext)s',
                'merge_output_format': 'mp4',
                'quiet': True
            }
            with YoutubeDL(ydl_video_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)
                if not video_path.endswith('.mp4'):
                    video_path = os.path.splitext(video_path)[0] + '.mp4'

            # 2. YouTube audioni MP3 formatida yuklash
            ydl_audio_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(id)s_audio.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True
            }
            with YoutubeDL(ydl_audio_opts) as ydl:
                info_audio = ydl.extract_info(url, download=True)
                audio_path = os.path.splitext(ydl.prepare_filename(info_audio))[0] + '.mp3'

            await status_msg.delete()

            # Yuklangan YouTube fayllarini foydalanuvchiga yuborish
            if video_path and os.path.exists(video_path):
                await message.answer_video(FSInputFile(video_path), caption="🎬 YouTube Video")
            if audio_path and os.path.exists(audio_path):
                await message.answer_audio(FSInputFile(audio_path), caption="🎵 YouTube MP3")

        elif is_instagram:
            # 3. Instagram videoni yuklash
            ydl_insta_opts = {
                'format': 'best',
                'outtmpl': 'downloads/%(id)s_insta.%(ext)s',
                'quiet': True
            }
            with YoutubeDL(ydl_insta_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                video_path = ydl.prepare_filename(info)

            await status_msg.delete()

            # Yuklangan Instagram faylini foydalanuvchiga yuborish
            if video_path and os.path.exists(video_path):
                await message.answer_video(FSInputFile(video_path), caption="📱 Instagram Video")

    except Exception as e:
        # Xatolik yuz bersa xabarni tahrirlash (masalan, yopiq profil yoki 50MB dan katta fayl)
        await status_msg.edit_text(f"❌ Yuklab olishda xatolik yuz berdi.\nSabab: Profil yopiq bo'lishi yoki video hajmi Telegram ruxsat bergan chegaradan (50 MB) katta bo'lishi mumkin.")
        print(f"Xatolik tafsiloti: {e}")

    finally:
        # Kod ishini tugatgach, serverda joy band qilmasligi uchun fayllarni tozalash
        cleanup(video_path, audio_path)

async def main():
    # Vaqtinchalik yuklash papkasini yaratish
    os.makedirs('downloads', exist_ok=True)
    
    # Botni ishga tushirish
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())