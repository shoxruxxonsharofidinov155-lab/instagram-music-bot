import asyncio
import os
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import instaloader
from shazamio import Shazam

# --- Render Dummy Web Server (Timed Out bermasligi uchun) ---
async def handle(request):
    return web.Response(text="Bot uzluksiz ishlamoqda!")

async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

# --- Bot Sozlamalari ---
BOT_TOKEN = "YOUR_NEW_BOT_TOKEN_HERE"  # BotFather'dan olingan yangi token

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shazam = Shazam()
L = instaloader.Instaloader()

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Salom! Menga Instagram link yuboring yoki musiqa izlash uchun audio/video yuboring.")

@dp.message(F.audio | F.voice | F.video)
async def recognize_music(message: Message):
    msg = await message.answer("🔍 Musiqa qidirilmoqda...")
    file_id = message.audio.file_id if message.audio else (message.voice.file_id if message.voice else message.video.file_id)
    file = await bot.get_file(file_id)
    file_path = f"{uuid.uuid4()}.mp3"
    await bot.download_file(file.file_path, file_path)
    
    try:
        out = await shazam.recognize(file_path)
        track = out.get('track')
        if track:
            title = track.get('title')
            subtitle = track.get('subtitle')
            await msg.edit_text(f"🎵 **Topildi:** {title} - {subtitle}")
        else:
            await msg.edit_text("❌ Musiqa topilmadi.")
    except Exception as e:
        await msg.edit_text("❌ Xatolik yuz berdi.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Asosiy Ishga Tushirish ---
async def main():
    await start_dummy_server()
    print("Musiqa tanish va Instagram bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
