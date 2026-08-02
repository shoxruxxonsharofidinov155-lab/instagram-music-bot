import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
import yt_dlp

BOT_TOKEN = "8632342746:AAHYorlOiRZUR59M9r7_IQgkR4XnMYG0ry0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Salom! Menga YouTube yoki Instagram havolasini yuboring, men uni sizga yuklab beraman.")

@dp.message(F.text & (F.text.startswith("http://") | F.text.startswith("https://")))
async def link_handler(message: types.Message):
    url = message.text.strip()
    await message.answer("⏳ Iltimos kuting, video yuklab olinmoqda...")
    
    output_filename = "downloaded_video.mp4"
    
    ydl_opts = {
        'format': 'best[filesize<50M]/best',
        'outtmpl': output_filename,
        'noplaylist': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_filename):
            file_size = os.path.getsize(output_filename)
            if file_size > 50 * 1024 * 1024:
                await message.answer("❌ Video hajmi 50 MB dan katta, shuning uchun Telegramga yuklab bo'lmaydi.")
            else:
                video_file = types.FSInputFile(output_filename)
                await message.answer_video(video=video_file)
            
            os.remove(output_filename)
        else:
            await message.answer("❌ Yuklab olishda xatolik yuz berdi.\nSabab: Fayl topilmadi yoki havolada xatolik bor.")
            
    except Exception as e:
        print(f"Xatolik tafsiloti: {e}")
        await message.answer("❌ Yuklab olishda xatolik yuz berdi.\nSabab: YouTube/Instagram himoyasi yoki video hajmi chegaradan (50 MB) katta.")
        if os.path.exists(output_filename):
            os.remove(output_filename)

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
