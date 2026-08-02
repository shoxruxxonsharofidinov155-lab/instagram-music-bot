import asyncio
import os
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import instaloader
from shazamio import Shazam

async def handle(request):
    """Render port tekshiruvi uchun soxta veb-sahifa (Timed Out oldini oladi)."""
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

async def start_dummy_server():
    """Render Web Service taqdim etadigan PORT'da veb-serverni ishga tushirish."""
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server {port}-portda ishga tushdi.")

# Telegram Bot Token (Render Environment Variable'dan olinadi yoki quyidagi qiymat ishlatiladi)
BOT_TOKEN = os.environ.get("8632342746:AAHrdd5NOBWgzf_UzHjL-btoNYqMKyYPXxE")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shazam = Shazam()
L = instaloader.Instaloader()

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Salom! Menga Instagram Reels havolasini yuboring yoki musiqa topish uchun audio/video yuboring.")

@dp.message(F.audio | F.voice | F.video)
async def recognize_music(message: Message):
    msg = await message.answer("🔍 Musiqa aniqlanmoqda...")
    file_id = message.audio.file_id if message.audio else (message.voice.file_id if message.voice else message.video.file_id)
    file = await bot.get_file(file_id)
    file_path = f"{uuid.uuid4()}.mp3"
    await bot.download_file(file.file_path, file_path)
    
    try:
        out = await shazam.recognize(file_path)
        track = out.get('track')
        if track:
            title = track.get('title', 'Noma\'lum')
            subtitle = track.get('subtitle', 'Noma\'lum')
            await msg.edit_text(f"🎵 **Topildi:** {title} - {subtitle}", parse_mode="Markdown")
        else:
            await msg.edit_text("❌ Musiqa topilmadi.")
    except Exception as e:
        await msg.edit_text(f"❌ Musiqa tanishda xatolik: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

async def main():
    await start_dummy_server()
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
