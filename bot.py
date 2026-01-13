import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# ====== SETTINGS ======
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAME = "@YQOMARN"
CHANNEL_USERNAME = "@Bot_TMWIK"
CHANNEL_NAME = "قناة بوت تمويلك"

# ====== DATABASE ======
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    inviter INTEGER
)
""")
db.commit()

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    inviter = None

    if context.args:
        try:
            inviter = int(context.args[0])
        except:
            inviter = None

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, points, inviter) VALUES (?, ?, ?)",
            (user.id, 0, inviter)
        )
        if inviter:
            cursor.execute(
                "UPDATE users SET points = points + 10 WHERE user_id=?",
                (inviter,)
            )
        db.commit()

    keyboard = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ]

    await update.message.reply_text(
        "👋 أهلاً بك في *بوت تمويلك*\nاختر من القائمة 👇",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ====== BUTTONS ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await query.message.reply_text(f"💰 رصيدك الحالي: {points} نقطة")

    elif query.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(
            f"👥 رابط الدعوة الخاص بك:\n{link}\n\n"
            "🔹 كل شخص يدخل عن طريقك = +10 نقاط"
        )

    elif query.data == "collect":
        await query.message.reply_text(
            f"🎯 *تجميع النقاط*\n\n"
            f"1️⃣ اشترك في القناة:\n"
            f"{CHANNEL_NAME}\n{CHANNEL_USERNAME}\n\n"
            "2️⃣ بعد الاشتراك ارجع للبوت\n\n"
            "⏳ (التحقق التلقائي يضاف لاحقاً)",
            parse_mode="Markdown"
        )

    elif query.data == "buy":
        await query.message.reply_text(
            "🛒 *شراء نقاط*\n\n"
            "💵 100 نقطة = 1$\n\n"
            f"📩 راسل الأدمن:\n{ADMIN_USERNAME}",
            parse_mode="Markdown"
        )

# ====== RUN ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
