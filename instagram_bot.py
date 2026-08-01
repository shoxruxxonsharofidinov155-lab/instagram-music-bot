import asyncio
import html
import os
import re
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import yt_dlp

# Telegram Bot Tokeningiz
BOT_TOKEN = "8632342746:AAFRoAHE2M7LoWA6kSXcyioy1CAKhJgK7Cw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def extract_shortcode(url: str) -> str | None:
    """Instagram havolasidan videoning ID (shortcode) kodini ajratib oladi."""
    match = re.search(r"instagram\.com/(?:p|reel|reels)/([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else None

async def download_from_embed(shortcode: str, output_filename: str) -> bool:
    """1-usul: Instagram Embed HTML manbasidan video linkini ajratib olish."""
    embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(embed_url, headers=headers, timeout=12) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    # HTML ichidan videoning haqiqiy URL manzilini qidirish
                    match = re.search(r'video_url["\']:\s*["\']([^"\']+)["\']', text)
                    if not match:
                        match = re.search(r'<video[^>]+src=["\']([^"\']+)["\']', text)

                    if match:
                        video_url = match.group(1).replace("\\u0026", "&").replace("\\/", "/")
                        video_url = html.unescape(video_url)

                        async with session.get(video_url, headers=headers, timeout=30) as v_resp:
                            if v_resp.status == 200:
                                with open(output_filename, "wb") as f:
                                    f.write(await v_resp.read())
                                return True
    except Exception:
        pass
    return False

async def download_from_fxtagram(shortcode: str, output_filename: str) -> bool:
    """2-usul: FxTagram ochiq manbali xizmati orqali yuklash."""
    api_url = f"https://api.fxtagram.com/p/{shortcode}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    try:
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(api_url, headers=headers, timeout=12) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    video_url = data.get("url") or data.get("media", {}).get("url")
                    
                    if not video_url and "selected_media" in data:
                        video_url = data["selected_media"].get("url")

                    if video_url:
                        async with session.get(video_url, timeout=30) as v_resp:
                            if v_resp.status == 200:
                                with open(output_filename, "wb") as f:
                                    f.write(await v_resp.read())
                                return True
    except Exception:
        pass
    return False

def download_with_ytdlp(url: str, output_filename: str) -> bool:
    """3-usul: yt-dlp kutubxonasi orqali mahalliy yuklab olish."""
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(output_filename) and os.path.getsize(output_filename) > 0
    except Exception:
        return False

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Salom! Menga Instagram Reels yoki video havolasini yuboring, men uni sizga yuklab beraman.")

@dp.message(F.text.contains("instagram.com"))
async def download_instagram_video(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("📥 Video yuklanmoqda, biroz kuting...")
    output_filename = f"video_{message.from_user.id}_{message.message_id}.mp4"

    shortcode = extract_shortcode(url)
    downloaded = False

    try:
        # 1. Embed orqali urinib ko'rish
        if shortcode:
            downloaded = await download_from_embed(shortcode, output_filename)

        # 2. FxTagram API orqali urinib ko'rish
        if not downloaded and shortcode:
            downloaded = await download_from_fxtagram(shortcode, output_filename)

        # 3. yt-dlp orqali urinib ko'rish
        if not downloaded:
            downloaded = await asyncio.to_thread(download_with_ytdlp, url, output_filename)

        if downloaded and os.path.exists(output_filename):
            await status_msg.edit_text("📤 Video Telegram'ga yuklanmoqda...")
            video_file = FSInputFile(output_filename)
            await message.answer_video(video=video_file, caption="Siz so'ragan video! 🎬")
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havola ochiq (Public) akkauntdan ekanligini tekshiring.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

    finally:
        if os.path.exists(output_filename):
            os.remove(output_filename)

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())