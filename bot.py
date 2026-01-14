import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# 🔴 غيّر الآيدي مالتك فقط
ADMIN_ID = 6858655581  

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

# ---------- KEYBOARDS ----------
user_keyboard = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط", "🔁 تحويل نقاط"],
        ["💰 رصيدي", "🔗 رابط الدعوة"],
        ["🛒 شراء نقاط", "ℹ️ معلومات الحساب"]
    ],
    resize_keyboard=True
)

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

    await update.message.reply_text(
        "👋 أهلاً بك في *بوت تمويلك*\n\nاختر من القائمة 👇",
        reply_markup=user_keyboard,
        parse_mode="Markdown"
    )

# ---------- USER ACTIONS ----------
async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if text == "💰 رصيدي":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await update.message.reply_text(f"💰 رصيدك الحالي: {points} نقطة")

    elif text == "🔗 رابط الدعوة":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(
            f"🔗 رابط الدعوة الخاص بك:\n{link}\n\n"
            "👥 كل شخص يسجل عن طريقك تحصل نقاط (يحددها الأدمن)"
        )

    elif text == "🎯 تجميع نقاط":
        await update.message.reply_text(
            "🎯 *تجميع النقاط*\n\n"
            "سيتم إضافة قنوات للتجميع قريبًا 👌",
            parse_mode="Markdown"
        )

    elif text == "🔁 تحويل نقاط":
        await update.message.reply_text(
            "🔁 *تحويل النقاط*\n\n"
            "الميزة ستتفعل قريبًا",
            parse_mode="Markdown"
        )

    elif text == "🛒 شراء نقاط":
        await update.message.reply_text(
            "🛒 *شراء نقاط*\n\n"
            "راسل الأدمن: @YQOMARN",
            parse_mode="Markdown"
        )

    elif text == "ℹ️ معلومات الحساب":
        await update.message.reply_text(
            f"👤 آيديك: `{user_id}`\n"
            "📌 البوت: تمويل قنوات ومجموعات",
            parse_mode="Markdown"
        )

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "👑 *لوحة تحكم الأدمن*\n\n"
        "قريبًا:\n"
        "- إضافة نقاط\n"
        "- خصم نقاط\n"
        "- قنوات التجميع\n"
        "- الهدايا\n"
        "- الإذاعة",
        parse_mode="Markdown"
    )

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_actions))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
