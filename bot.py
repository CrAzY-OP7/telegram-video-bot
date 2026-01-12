import yt_dlp
import requests
from typing import Dict, Any, cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "PASTE_YOUR_TOKEN_HERE"

REDIRECT_SERVER = "https://video-redirect-server.onrender.com"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg:
        await msg.reply_text("👋 Send me any video link (YouTube, Insta, Twitter, etc)")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    url = msg.text.strip()

    if context.user_data is None:
        context.user_data = {}

    context.user_data["url"] = url

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Video", callback_data="mode_video")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="mode_audio")]
    ])

    await msg.reply_text("Choose format:", reply_markup=keyboard)


async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if context.user_data is None or "url" not in context.user_data:
        await query.edit_message_text("❌ Session expired. Send the link again.")
        return

    url = context.user_data["url"]
    mode = query.data

    ydl_opts: Dict[str, Any] = {"quiet": True, "skip_download": True}
    ydl = cast(Any, yt_dlp.YoutubeDL(ydl_opts))
    info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []
    store: Dict[str, str] = {}

    if mode == "mode_video":
        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
                res = f.get("resolution")
                if res and res not in store:
                    store[res] = f["url"]
        title = "🎬 Choose video quality"

    else:
        for f in formats:
            if f.get("vcodec") == "none" and f.get("acodec") != "none" and f.get("url"):
                abr = f.get("abr")
                if abr:
                    key = f"{int(abr)} kbps"
                    if key not in store:
                        store[key] = f["url"]
        title = "🎵 Choose audio quality"

    if not store:
        await query.edit_message_text("❌ No streams found.")
        return

    context.user_data["streams"] = store

    buttons = [[InlineKeyboardButton(k, callback_data=k)] for k in store]
    await query.edit_message_text(title, reply_markup=InlineKeyboardMarkup(buttons))


async def quality_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if context.user_data is None:
        await query.edit_message_text("❌ Session expired.")
        return

    streams = context.user_data.get("streams")
    choice = query.data

    if not isinstance(streams, dict) or choice not in streams:
        await query.edit_message_text("❌ Invalid selection.")
        return

    real_url = streams[choice]

    # Ask redirect server to generate fast link
    r = requests.post(f"{REDIRECT_SERVER}/create", json={"url": real_url})
    fast_url = r.json()["link"]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Now", url=fast_url)]
    ])

    await query.edit_message_text(
        f"📥 {choice} ready!\nTap below to download at full speed:",
        reply_markup=keyboard
    )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(mode_selected, pattern="^mode_"))
app.add_handler(CallbackQueryHandler(quality_selected))

print("Bot running...")
app.run_polling()
