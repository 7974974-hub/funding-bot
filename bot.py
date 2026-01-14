import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581  # ✅ آيدي الأدمن

# ---------- DATABASE ----------
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
db.commit()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, points) VALUES (?, ?)",
            (user_id, 0)
        )
        db.commit()

    keyboard = [
        [
            InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect"),
            InlineKeyboardButton("💰 رصيدي", callback_data="balance")
        ],
        [
            InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy"),
            InlineKeyboardButton("🔗 رابط الدعوة", callback_data="invite")
        ]
    ]

    # زر الأدمن (يظهر فقط لك)
    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")]
        )

    await update.message.reply_text(
        "👋 أهلاً بك في **بوت تمويلك**\n👇 اختر من القائمة",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# ---------- BUTTONS ----------
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
            f"🔗 رابط الدعوة الخاص بك:\n{link}"
        )

    elif query.data == "collect":
        await query.message.reply_text(
            "🎯 تجميع النقاط\n"
            "سيتم إضافة قنوات للتجميع قريباً 👌"
        )

    elif query.data == "buy":
        await query.message.reply_text(
            "🛒 شراء نقاط\n"
            "راسل الأدمن: @YQOMARN"
        )

    # ---------- ADMIN PANEL ----------
    elif query.data == "admin" and user_id == ADMIN_ID:
        admin_keyboard = [
            [InlineKeyboardButton("➕ إضافة نقاط", callback_data="add_points")],
            [InlineKeyboardButton("➖ خصم نقاط", callback_data="remove_points")],
            [InlineKeyboardButton("📢 إذاعة رسالة", callback_data="broadcast")]
        ]
        await query.message.reply_text(
            "🛠 **لوحة تحكم الأدمن**",
            reply_markup=InlineKeyboardMarkup(admin_keyboard),
            parse_mode="Markdown"
        )

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
