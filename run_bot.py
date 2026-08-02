import asyncio
import os
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
import instaloader
from ShazamAPI import Shazam

# --- Render Port / Dummy Web Server (Timed Out bermasligi uchun) ---
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
# BotFather bergan yangi tokeningizni quyidagi qo'shtirnoq ichiga yozing:
BOT_TOKEN = "8632342746:AAHrdd5NOBWgzf_UzHjL-btoNYqMKyYPXxE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
L = instaloader.Instaloader()

@dp.message(F.text == "/start")
def cmd_start(message: Message):
    message.answer("Salom! Menga Instagram link yuboring yoki musiqa izlash uchun audio/video yuboring.")

# --- Asosiy Ishga Tushirish ---
async def main():
    # 1. Dummy serverni ishga tushiramiz (Render o'chirib qo'ymasligi uchun)
    await start_dummy_server()
    print("Musiqa tanish va Instagram bot ishga tushdi...")
    
    # 2. Telegram bot pollingni boshlaymiz
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
