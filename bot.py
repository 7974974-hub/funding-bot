import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ---------- DATABASE ----------
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels (
    username TEXT PRIMARY KEY
)
""")

db.commit()

# ---------- CHECK SUB ----------
async def is_subscribed(bot, user_id):
    cursor.execute("SELECT username FROM channels")
    channels = cursor.fetchall()

    for (channel,) in channels:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        cursor.execute("SELECT username FROM channels")
        channels = cursor.fetchall()

        text = "🚫 لازم تشترك بالقنوات أولاً:\n\n"
        buttons = []

        for (channel,) in channels:
            text += f"👉 {channel}\n"
            buttons.append([InlineKeyboardButton(channel, url=f"https://t.me/{channel.replace('@','')}")])

        await update.message.reply_text(
            text + "\nوبعدها اكتب /start",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    keyboard = [
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["👥 رابط الدعوة", "🛒 شراء نقاط"]
    ]

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\nاختر من القائمة 👇",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(x, callback_data=x)] for row in keyboard for x in row])
    )

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("❌ حذف قناة", callback_data="remove_channel")],
        [InlineKeyboardButton("📋 عرض القنوات", callback_data="list_channels")]
    ]

    await update.message.reply_text(
        "👑 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- ADMIN BUTTONS ----------
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        return

    if query.data == "add_channel":
        context.user_data["action"] = "add_channel"
        await query.message.reply_text("✍️ أرسل يوزر القناة مثل:\n@channel")

    elif query.data == "remove_channel":
        context.user_data["action"] = "remove_channel"
        await query.message.reply_text("✍️ أرسل يوزر القناة للحذف")

    elif query.data == "list_channels":
        cursor.execute("SELECT username FROM channels")
        channels = cursor.fetchall()
        if not channels:
            await query.message.reply_text("❌ لا توجد قنوات")
        else:
            text = "📋 القنوات:\n\n"
            for (c,) in channels:
                text += f"- {c}\n"
            await query.message.reply_text(text)

# ---------- HANDLE ADMIN TEXT ----------
async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    action = context.user_data.get("action")
    text = update.message.text.strip()

    if action == "add_channel":
        if not text.startswith("@"):
            await update.message.reply_text("❌ لازم يبدأ بـ @")
            return
        cursor.execute("INSERT OR IGNORE INTO channels (username) VALUES (?)", (text,))
        db.commit()
        await update.message.reply_text(f"✅ تم إضافة القناة {text}")

    elif action == "remove_channel":
        cursor.execute("DELETE FROM channels WHERE username=?", (text,))
        db.commit()
        await update.message.reply_text(f"🗑️ تم حذف القناة {text}")

    context.user_data["action"] = None

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
