import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581  # آيديك

# ---------- DATABASE ----------
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")
db.commit()

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] == 1:
        await update.message.reply_text("🚫 أنت محظور من استخدام البوت")
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    keyboard = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ]

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك\nاختر من القائمة 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban")],
        [InlineKeyboardButton("✅ فك حظر مستخدم", callback_data="unban")],
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data="addpoints")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")]
    ]

    await update.message.reply_text(
        "👑 لوحة الأدمن",
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
        await query.message.reply_text(f"👥 رابطك:\n{link}\nكل دعوة = 10 نقاط")

    elif query.data == "collect":
        cursor.execute("UPDATE users SET points = points + 5 WHERE user_id=?", (user_id,))
        db.commit()
        await query.message.reply_text("🎁 تم إضافة 5 نقاط")

    elif query.data == "buy":
        await query.message.reply_text("🛒 شراء نقاط\nراسل الأدمن: @YQOMARN")

    # --- ADMIN ACTIONS ---
    elif query.data == "stats" and user_id == ADMIN_ID:
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        await query.message.reply_text(f"📊 عدد المستخدمين: {total}")

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
