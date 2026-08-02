import asyncio
import os
import re
import uuid
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
import instaloader
from shazamio import Shazam

# --- Bot Sozlamalari ---
# Agar tokeningiz yangilangan bo'lsa, shu yerni o'zgartiring
BOT_TOKEN = "8632342746:AAFnfdQAVpsFr1agIE0hCrgAtrAeXpakyRM"

# Render/VPS da ishlayotgani uchun Proxy shart emas
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
shazam = Shazam()

# --- Instaloader sozlamalari ---
L = instaloader.Instaloader(
    download_pictures=False,
    download_videos=True,
    download_video_thumbnails=False,
    download_geotags=False,
    post_metadata_txt_pattern="",
    save_metadata=False
)

# --- /start buyrug'i ---
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Salom! Menga Instagram link yuboring (video yuklash uchun) yoki musiqa izlash uchun audio/video/ovozli xabar yuboring.")

# --- 1. INSTAGRAM LINK ORQALI VIDEO YUKLASH ---
@dp.message(F.text.contains("instagram.com"))
async def download_instagram_video(message: Message):
    msg = await message.answer("📥 Instagram'dan video yuklanmoqda, biroz kuting...")
    
    # Linkdan shortcode'ni ajratib olish
    match = re.search(r'(?:reel|p)/([^/?#&]+)', message.text)
    if not match:
        await msg.edit_text("❌ Yaroqli Instagram havolasi topilmadi.")
        return
        
    shortcode = match.group(1)
    target_dir = f"downloads_{uuid.uuid4().hex}"
    
    try:
        # Videoni yuklab olish
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=target_dir)
        
        # Yuklangan mp4 faylni topish
        video_file = None
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".mp4"):
                    video_file = os.path.join(root, file)
                    break
        
        if video_file:
            await msg.edit_text("📤 Video Telegram'ga yuklanmoqda...")
            video = FSInputFile(video_file)
            await message.answer_video(video=video, caption="✅ Video yuklab olindi!")
            await msg.delete()
        else:
            await msg.edit_text("❌ Video fayli topilmadi.")
            
    except Exception as e:
        await msg.edit_text("❌ Videoni yuklashda xatolik yuz berdi. (Instagram yopiq profil bo'lishi mumkin)")
    finally:
        # Vaqtincha ochilgan papka va fayllarni tozalab tashlash (server to'lib ketmasligi uchun)
        if os.path.exists(target_dir):
            for root, dirs, files in os.walk(target_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(target_dir)

# --- 2. AUDIOLARDAN MUSIQA QIDIRISH (SHAZAM) ---
@dp.message(F.audio | F.voice | F.video)
async def recognize_music(message: Message):
    msg = await message.answer("🔍 Musiqa qidirilmoqda...")
    
    # Fayl ID'sini ajratib olish (audio, ovozli xabar yoki video bo'lishidan qat'i nazar)
    file_id = message.audio.file_id if message.audio else (
        message.voice.file_id if message.voice else message.video.file_id
    )
    
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
        await msg.edit_text("❌ Musiqa aniqlashda xatolik yuz berdi.")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

# --- Asosiy ishga tushirish qismi ---
async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
