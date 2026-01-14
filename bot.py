import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, ContextTypes,
    MessageHandler, filters
)

# ========= الإعدادات =========
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"
FORCE_CHANNELS = ["@Bot_TMWIK"]  # تقدر تضيف أكثر

# ========= قاعدة البيانات =========
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

# ========= حالات الأدمن =========
admin_states = {}

# ========= فحص الاشتراك =========
async def is_subscribed(bot, user_id):
    for ch in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(context.bot, user_id):
        await update.message.reply_text(
            "🚫 لازم تشترك بالقناة أولاً:\n"
            "https://t.me/Bot_TMWIK\n\n"
            "وبعدها اكتب /start"
        )
        return

    cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    if row and row[0] == 1:
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🔄 تحويل نقاط", callback_data="transfer")],
        [InlineKeyboardButton("♻️ استبدال نقاط", callback_data="redeem")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")]
    ])

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\nاختر من القائمة 👇",
        reply_markup=keyboard
    )

# ========= لوحة الأدمن =========
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data="admin_add")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban")],
        [InlineKeyboardButton("✅ فك حظر", callback_data="admin_unban")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")]
    ])

    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=keyboard)

# ========= أزرار =========
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        pts = cursor.fetchone()[0]
        await q.message.reply_text(f"💰 رصيدك: {pts} نقطة")

    elif q.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.message.reply_text(f"👥 رابطك:\n{link}\nكل دعوة = 10 نقاط")

    elif q.data == "buy":
        await q.message.reply_text("🛒 شراء نقاط\nراسل الأدمن: @YQOM
