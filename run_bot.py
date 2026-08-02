import asyncio
import os
import uuid
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import instaloader

# Fix for Python 3.13/3.14 audioop removal
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
import yt_dlp

BOT_TOKEN = "8632342746:AAHrdd5NOBWgzf_UzHjL-btoNYqMKyYPXxE"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Aniqlangan qo'shiqlar ma'lumotini vaqtincha saqlash uchun kesh (RAM)
MUSIC_CACHE = {}

# Instaloader sozlamalari
L = instaloader.Instaloader(
    download_pictures=False,
    download_video_thumbnails=False,
    download_geotags=False,
    download_comments=False,
    save_metadata=False
)

def get_direct_video_url(url: str) -> str | None:
    """Instagram Reel/Video linkidan to'g'ridan-to'g'ri MP4 manzilini ajratib oladi."""
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
        print(f"URL olishda xato: {e}")
        return None

async def download_video_file(video_url: str, output_path: str) -> bool:
    """Videoni aiohttp orqali tezkor kompyuterga yuklaydi."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(video_url, timeout=20) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
                    return True
    except Exception as e:
        print(f"Video yuklashda xato: {e}")
    return False

def sync_recognize_music(video_path: str) -> str | None:
    """ShazamAPI orqali videodagi musiqani tanib olish."""
    try:
        with open(video_path, 'rb') as f:
            mp3_file_content_to_recognize = f.read()
        
        shazam = Shazam(mp3_file_content_to_recognize)
        recognize_generator = shazam.recognizeSong()
        
        # Segmentlarni ketma-ket tekshirish
        for _ in range(5):
            try:
                offset, res = next(recognize_generator)
                if isinstance(res, dict) and 'track' in res:
                    title = res['track'].get('title', '')
                    artist = res['track'].get('subtitle', '')
                    if title and artist:
                        return f"{artist} - {title}"
                    elif title:
                        return title
            except StopIteration:
                break
    except Exception as e:
        print(f"Musiqa tanishda xato: {e}")
    return None

def download_mp3_by_search(search_query: str, output_prefix: str) -> str | None:
    """Qo'shiq nomini YouTube'dan qidirib, MP3 audio formatida yuklab beradi."""
    expected_file = f"{output_prefix}.mp3"
    ydl_opts = {
        'format': 'bestaudio/best',
        'default_search': 'ytsearch1',
        'outtmpl': output_prefix,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
        if os.path.exists(expected_file):
            return expected_file
    except Exception as e:
        print(f"MP3 yuklashda xatolik: {e}")
    return None

@dp.message(F.text == "/start")
async def start_cmd(message: Message):
    await message.answer("Salom! Menga Instagram Reels havolasini yuboring. Men videoni va undagi qo'shiqni (MP3) yuklab beraman! 🎬🎵")

@dp.message(F.text.contains("instagram.com"))
async def handle_instagram(message: Message):
    url = message.text.strip()
    status_msg = await message.answer("⚡️ Video va musiqa tahlil qilinmoqda...")
    
    video_filename = f"video_{message.from_user.id}_{message.message_id}.mp4"

    try:
        # 1. Video URL manzilini ajratish
        video_url = await asyncio.to_thread(get_direct_video_url, url)

        if video_url:
            await status_msg.edit_text("📥 Video va audio yuklanmoqda...")
            
            # 2. Videoni yuklab olish
            downloaded = await download_video_file(video_url, video_filename)

            if downloaded and os.path.exists(video_filename):
                # 3. ShazamAPI orqali musiqani tanib olish
                await status_msg.edit_text("🎵 Videodan musiqa aniqlanmoqda...")
                music_name = await asyncio.to_thread(sync_recognize_music, video_filename)

                # Tugma tayyorlash
                reply_markup = None
                caption_text = "Siz so'ragan video! 🎬"

                if music_name:
                    music_id = str(uuid.uuid4())[:8]
                    MUSIC_CACHE[music_id] = music_name
                    caption_text += f"\n\n🎵 **Musiqa:** {music_name}"
                    
                    button = InlineKeyboardButton(
                        text=f"🎵 {music_name[:25]}... (MP3 Yuklash)", 
                        callback_data=f"dlmusic:{music_id}"
                    )
                    reply_markup = InlineKeyboardMarkup(inline_keyboard=[[button]])

                await status_msg.edit_text("📤 Telegram'ga yuborilmoqda...")
                
                # Videoni yuborish
                await message.answer_video(
                    video=FSInputFile(video_filename), 
                    caption=caption_text,
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
                await status_msg.delete()
                return

        await status_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havola ochiq (Public) akkauntdan ekanligini tekshiring.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

    finally:
        if os.path.exists(video_filename):
            os.remove(video_filename)

@dp.callback_query(F.data.startswith("dlmusic:"))
async def process_music_download(callback: CallbackQuery):
    music_id = callback.data.split(":")[1]
    music_name = MUSIC_CACHE.get(music_id)

    if not music_name:
        await callback.answer("❌ Musiqa ma'lumoti topilmadi.", show_alert=True)
        return

    await callback.answer("📥 Musiqa qidirilmoqda va yuklanmoqda...")
    status_msg = await callback.message.answer(f"🔎 *{music_name}* musiqasi MP3 formatda yuklanmoqda...", parse_mode="Markdown")

    output_prefix = f"audio_{callback.from_user.id}_{callback.message.message_id}"
    
    try:
        # YouTube'dan MP3 qilib yuklab olish
        mp3_file = await asyncio.to_thread(download_mp3_by_search, music_name, output_prefix)

        if mp3_file and os.path.exists(mp3_file):
            await status_msg.edit_text("📤 MP3 Telegram'ga yuborilmoqda...")
            await callback.message.answer_audio(
                audio=FSInputFile(mp3_file),
                caption=f"🎧 *{music_name}*",
                parse_mode="Markdown"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Musiqani MP3 formatda yuklab bo'lmadi.")

    except Exception as e:
        await status_msg.edit_text(f"❌ Musiqani yuklashda xato: {e}")

    finally:
        expected_file = f"{output_prefix}.mp3"
        if os.path.exists(expected_file):
            os.remove(expected_file)

async def main():
    print("Musiqa tanish va Instagram bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
