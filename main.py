import asyncio
import os
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile

BOT_TOKEN = "8632342746:AAFRoAHE2M7LoWA6kSXcyioy1CAKhJgK7Cw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Salom! Menga Instagram Reels yoki video havolasini yuboring, men uni sizga yuklab beraman.")

@dp.message(F.text.contains("instagram.com"))
async def download_instagram_video(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("📥 Video yuklanmoqda, biroz kuting...")

    output_filename = f"video_{message.from_user.id}.mp4"

    # Barqaror va ochiq Instagram Downloader API (SnapInsta backend)
    api_url = "https://api.vkrnot.com/v2/instagram"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    payload = f"url={url}"

    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 1. So'rov yuborish
            async with session.post(api_url, data=payload, headers=headers, timeout=20) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    video_url = None
                    # JSON tarkibini chuqurroq tekshirish
                    if "data" in data:
                        if isinstance(data["data"], list) and len(data["data"]) > 0:
                            video_url = data["data"][0].get("url") or data["data"][0].get("video")
                        elif isinstance(data["data"], dict):
                            video_url = data["data"].get("url") or data["data"].get("video")
                    elif "url" in data:
                        video_url = data["url"]

                    if video_url:
                        # 2. Videoni kompyuterga yuklab olish
                        async with session.get(video_url) as video_resp:
                            if video_resp.status == 200:
                                with open(output_filename, "wb") as f:
                                    f.write(await video_resp.read())

                                await status_msg.edit_text("📤 Video yuborilmoqda...")
                                
                                # 3. Telegram'ga yuborish
                                video_file = FSInputFile(output_filename)
                                await message.answer_video(video=video_file, caption="Siz so'ragan video! 🎬")
                                await status_msg.delete()
                                return

            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havola to'g'riligini va akkaunt ochiqligini tekshiring.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

async def main():
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())