import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = "8632342746:AAHYorlOiRZUR59M9r7_IQgkR4XnMYG0ry0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    # Vercel yoki Netlify'ga joylagan index.html havolasini quyidagi url'ga yozasiz
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Huquqiy Portalni Ochish", web_app=WebAppInfo(url="https://luminous-caramel-50d975.netlify.app/"))]
    ])
    await message.answer(
        "Assalomu alaykum! Huquqiy kutubxona va portal botiga xush kelibsiz.\n\n"
        "Portalni ochish uchun quyidagi tugmani bosing:",
        reply_markup=keyboard
    )

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Huquqiy bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
