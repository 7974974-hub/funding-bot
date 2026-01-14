import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581          # آيدي الأدمن
FORCE_CHANNEL = "@Bot_TMWIK"   # قناة الاشتراك الإجباري
CHANNEL_LINK = "https://t.me/Bot_TMWIK"
ADMIN_USERNAME = "@YQOMARN"

# ================== DATABASE ==================
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
db.commit()

# ================== CHECK SUB ==================
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ================== START ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        keyboard = [
            [InlineKeyboardButton("📢 الاشتراك بالقناة", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ تحقق", callback_data="check_sub")]
        ]
        await update.message.reply_text(
            "🚫 يجب الاشتراك بالقناة أولاً",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id, points) VALUES (?,0)", (user_id,))
    db.commit()

    keyboard = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("🔄 تحويل نقاط", callback_data="transfer")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")])

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك\n👇 اختر من القائمة",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== BUTTONS ==================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "check_sub":
        if await is_subscribed(context.bot, user_id):
            await query.message.reply_text("✅ تم التحقق\nاكتب /start")
        else:
            await query.message.reply_text("❌ اشترك بالقناة ثم تحقق")

    elif query.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await query.message.reply_text(f"💰 رصيدك الحالي: {points} نقطة")

    elif query.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(
            f"🔗 رابط الدعوة الخاص بك:\n{link}\n\n"
            "👤 كل شخص = +10 نقاط"
        )

    elif query.data == "collect":
        await query.message.reply_text(
            "🎯 تجميع النقاط\n"
            "📢 اشترك بالقناة ثم تحقق\n\n"
            f"{CHANNEL_LINK}"
        )

    elif query.data == "buy":
        await query.message.reply_text(
            "🛒 شراء نقاط\n"
            "💵 راسل الأدمن:\n"
            f"{ADMIN_USERNAME}"
        )

    elif query.data == "admin" and user_id == ADMIN_ID:
        await query.message.reply_text(
            "🛠 لوحة الأدمن\n"
            "حالياً الأساس شغال ✔"
        )

# ================== RUN ==================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
