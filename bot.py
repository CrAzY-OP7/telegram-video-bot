import yt_dlp
from typing import Dict, Any, cast
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

BOT_TOKEN = "8105658961:AAGTz1_FxV8KAUk6pQN9BTA4naMKk-FQ5rM"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg:
        await msg.reply_text("👋 Send me any video link (YouTube, Insta, Twitter, etc)")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text:
        return

    url = msg.text.strip()
    await msg.reply_text("📡 Link received.\nChoose what you want:")

    if context.user_data is None:
        context.user_data = {}

    context.user_data["url"] = url

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Video", callback_data="mode_video")],
        [InlineKeyboardButton("🎵 Audio (MP3)", callback_data="mode_audio")]
    ])

    await msg.reply_text("Select format:", reply_markup=keyboard)


async def mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if context.user_data is None or "url" not in context.user_data:
        await query.edit_message_text("❌ Session expired. Send the link again.")
        return

    mode = query.data
    url = context.user_data["url"]

    ydl_opts: Dict[str, Any] = {"quiet": True, "skip_download": True}
    ydl = cast(Any, yt_dlp.YoutubeDL(ydl_opts))
    info = ydl.extract_info(url, download=False)

    formats = info.get("formats") or []

    buttons = []
    store: Dict[str, str] = {}

    if mode == "mode_video":
        for f in formats:
            if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("url"):
                res = f.get("resolution")
                if res and res not in store:
                    store[res] = f["url"]

        if not store:
            await query.edit_message_text("❌ No combined video streams found.\n(4K is video-only on YouTube)")
            return

        title = "🎬 Choose video quality"

    else:  # audio
        for f in formats:
            if f.get("acodec") != "none" and f.get("vcodec") == "none" and f.get("url"):
                abr = f.get("abr")
                if abr:
                    key = f"{int(abr)} kbps"
                    if key not in store:
                        store[key] = f["url"]

        if not store:
            await query.edit_message_text("❌ No audio streams found.")
            return

        title = "🎵 Choose audio quality"

    if context.user_data is None:
        context.user_data = {}

    context.user_data["streams"] = store

    for k in store:
        buttons.append([InlineKeyboardButton(k, callback_data=k)])

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

    url = streams[choice]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬇️ Download Now", url=url)]
    ])

    await query.edit_message_text(
        f"📥 {choice} ready.\nTap below to download:",
        reply_markup=keyboard
    )


app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(mode_selected, pattern="^mode_"))
app.add_handler(CallbackQueryHandler(quality_selected))

print("Bot running...")
app.run_polling()
