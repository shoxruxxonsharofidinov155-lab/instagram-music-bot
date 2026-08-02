import asyncio
import os
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import instaloader
import yt_dlp

# Fix for Python 3.13+ audioop removal
try:
    import audioop
except ImportError:
    try:
        import audioop_lts as audioop
        import sys
        sys.modules['audioop'] = audioop
    except ImportError:
        pass

from ShazamAPI import Shazam

BOT_TOKEN = "8632342746:AAFRoAHE2M7LoWA6kSXcyioy1CAKhJgK7Cw"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Instaloader configuration
L = instaloader.Instaloader(
    download_pictures=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False
)

# Music cache dictionary
MUSIC_CACHE = {}

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

def get_direct_video_url(url: str) -> str | None:
    """Instagram havolasidan to'g'ridan-to'g'ri video URL manzilini ajratadi."""
    try:
        if "reel/" in url:
            shortcode = url.split("reel/")[1].split("/")[0].split("?")[0]
        elif "reels/" in url:
            shortcode = url.split("reels/")[1].split("/")[0].split("?")[0]
        elif "p/" in url:
            shortcode = url.split("p/")[1].split("/")[0].split("?")[0]
        else:
            return None

        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if post.is_video:
            return post.video_url
        return None
    except Exception as e:
        print(f"URL olishda xatolik: {e}")
        return None

async def download_file(url: str, path: str) -> bool:
    """Videoni tezkor yuklab olish."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                if resp.status == 200:
                    with open(path, "wb") as f:
                        f.write(await resp.read())
                    return True
    except Exception as e:
        print(f"Fayl yuklashda xatolik: {e}")
    return False

def sync_recognize_music(video_path: str) -> str | None:
    """Shazam orqali videodagi musiqani aniqlaydi."""
    try:
        with open(video_path, 'rb') as f:
            content = f.read()
        shazam = Shazam(content)
        for _, res in shazam.recognizeSong():
            if 'track' in res:
                return f"{res['track']['subtitle']} - {res['track']['title']}"
    except Exception as e:
        print(f"Musiqa tanishda xatolik: {e}")
    return None

def download_mp3(query: str, output_path: str):
    """Musiqani YouTube'dan mp3 formatida yuklab olish."""
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([query])

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Salom! Instagram Reels linkini yuboring, men video va uning musiqasini yuklab beraman.")

@dp.message(F.text.contains("instagram.com"))
async def handle_instagram(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("⚡️ Video tahlil qilinmoqda...")
    
    video_filename = f"video_{message.from_user.id}_{message.message_id}.mp4"

    try:
        # 1. Video URL olinadi
        video_url = await asyncio.to_thread(get_direct_video_url, url)

        if video_url:
            await status_msg.edit_text("📥 Video yuklanmoqda...")
            downloaded = await download_file(video_url, video_filename)

            if downloaded and os.path.exists(video_filename):
                # 2. Musiqa tanib olinadi
                await status_msg.edit_text("🎵 Video ichidagi musiqa aniqlanmoqda...")
                music_name = await asyncio.to_thread(sync_recognize_music, video_filename)

                reply_markup = None
                caption = "Siz so'ragan video! 🎬"

                if music_name:
                    music_id = str(len(MUSIC_CACHE) + 1)
                    MUSIC_CACHE[music_id] = music_name
                    caption += f"\n\n🎧 Musiqa: **{music_name}**"
                    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="🎵 MP3 Yuklash", callback_data=f"dl:{music_id}")
                    ]])

                await status_msg.edit_text("📤 Telegram'ga yuborilmoqda...")
                await message.answer_video(
                    video=FSInputFile(video_filename),
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                await status_msg.delete()
                return

        await status_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havola ochiq (Public) akkauntdan ekanligini tekshiring.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik: {e}")

    finally:
        if os.path.exists(video_filename):
            os.remove(video_filename)

@dp.callback_query(F.data.startswith("dl:"))
async def process_music_download(callback: CallbackQuery):
    music_id = callback.data.split(":")[1]
    music_name = MUSIC_CACHE.get(music_id)

    if not music_name:
        await callback.answer("❌ Musiqa topilmadi!", show_alert=True)
        return

    await callback.answer("📥 Musiqa yuklanmoqda, kuting...")
    output_base = f"audio_{callback.from_user.id}_{music_id}"
    mp3_filename = f"{output_base}.mp3"

    try:
        await asyncio.to_thread(download_mp3, music_name, output_base)

        if os.path.exists(mp3_filename):
            audio_file = FSInputFile(mp3_filename)
            await callback.message.answer_audio(
                audio=audio_file,
                caption=f"🎧 {music_name}"
            )
        else:
            await callback.message.answer("❌ MP3 faylini yuklab bo'lmadi.")

    except Exception as e:
        await callback.message.answer(f"❌ Musiqa yuklashda xatolik: {e}")

    finally:
        if os.path.exists(mp3_filename):
            os.remove(mp3_filename)

async def main():
    # Render Timed Out xatosining oldini olish uchun soxta veb-serverni ishga tushiramiz
    await start_dummy_server()
    print("Bot 24/7 rejimda ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
