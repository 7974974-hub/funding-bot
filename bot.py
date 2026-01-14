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

admin_wait = {}

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?,0)", (user_id,))
    db.commit()

    keyboard = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")])

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك\n👇 اختر من القائمة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- BUTTONS ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await query.message.reply_text(f"💰 رصيدك: {points} نقطة")

    elif query.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(f"🔗 رابطك:\n{link}")

    elif query.data == "collect":
        await query.message.reply_text(
            "🎯 لتجميع النقاط:\nاشترك بالقناة:\nhttps://t.me/Bot_TMWIK"
        )

    elif query.data == "buy":
        await query.message.reply_text("🛒 شراء نقاط\nراسل الأدمن: @YQOMARN")

    elif query.data == "admin" and user_id == ADMIN_ID:
        admin_kb = [
            [InlineKeyboardButton("➕ إضافة نقاط", callback_data="add")],
            [InlineKeyboardButton("➖ خصم نقاط", callback_data="remove")]
        ]
        await query.message.reply_text(
            "🛠 لوحة الأدمن",
            reply_markup=InlineKeyboardMarkup(admin_kb)
        )

    elif query.data == "add" and user_id == ADMIN_ID:
        admin_wait[user_id] = "add"
        await query.message.reply_text("✏️ أرسل:\nID POINTS\nمثال:\n6858655581 100")

    elif query.data == "remove" and user_id == ADMIN_ID:
        admin_wait[user_id] = "remove"
        await query.message.reply_text("✏️ أرسل:\nID POINTS\nمثال:\n6858655581 50")

# ---------- ADMIN TEXT ----------
async def admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in admin_wait:
        return

    try:
        target, pts = map(int, update.message.text.split())
    except:
        await update.message.reply_text("❌ صيغة خاطئة")
        return

    if admin_wait[uid] == "add":
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (pts, target))
        db.commit()
        await update.message.reply_text("✅ تم إضافة النقاط")

    elif admin_wait[uid] == "remove":
        cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (pts, target))
        db.commit()
        await update.message.reply_text("✅ تم خصم النقاط")

    admin_wait.pop(uid)

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_text))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()        
