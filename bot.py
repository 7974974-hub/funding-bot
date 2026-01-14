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
        await q.message.reply_text("🛒 شراء نقاط\nراسل الأدمن: @YQOMARN")

    elif q.data == "collect":
        cursor.execute("UPDATE users SET points = points + 5 WHERE user_id=?", (uid,))
        db.commit()
        await q.message.reply_text("🎁 تم إضافة 5 نقاط")

    elif q.data == "redeem":
        await q.message.reply_text("♻️ الاستبدال سيتم تفعيله لاحقاً")

    elif q.data == "transfer":
        admin_states[uid] = "wait_transfer_id"
        await q.message.reply_text("🔄 أرسل آيدي المستخدم")

# ========= أزرار الأدمن =========
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    if q.data == "admin_add":
        admin_states[ADMIN_ID] = "add_user"
        await q.message.reply_text("📥 أرسل آيدي المستخدم")

    elif q.data == "admin_ban":
        admin_states[ADMIN_ID] = "ban_user"
        await q.message.reply_text("🚫 أرسل آيدي المستخدم")

    elif q.data == "admin_unban":
        admin_states[ADMIN_ID] = "unban_user"
        await q.message.reply_text("✅ أرسل آيدي المستخدم")

    elif q.data == "admin_stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await q.message.reply_text(f"📊 عدد المستخدمين: {count}")

# ========= إدخال نص =========
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.from_user.id
    text = update.message.text

    if uid not in admin_states:
        return

    state = admin_states[uid]

    if state == "add_user":
        context.user_data["target"] = int(text)
        admin_states[uid] = "add_points"
        await update.message.reply_text("➕ أرسل عدد النقاط")

    elif state == "add_points":
        target = context.user_data["target"]
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (int(text), target))
        db.commit()
        admin_states.pop(uid)
        await update.message.reply_text("✅ تم إضافة النقاط")

    elif state == "ban_user":
        cursor.execute("UPDATE users SET banned = 1 WHERE user_id=?", (int(text),))
        db.commit()
        admin_states.pop(uid)
        await update.message.reply_text("🚫 تم الحظر")

    elif state == "unban_user":
        cursor.execute("UPDATE users SET banned = 0 WHERE user_id=?", (int(text),))
        db.commit()
        admin_states.pop(uid)
        await update.message.reply_text("✅ تم فك الحظر")

    elif state == "wait_transfer_id":
        context.user_data["transfer_to"] = int(text)
        admin_states[uid] = "wait_transfer_amount"
        await update.message.reply_text("🔢 أرسل عدد النقاط")

    elif state == "wait_transfer_amount":
        to_id = context.user_data["transfer_to"]
        amount = int(text)
        cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, uid))
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, to_id))
        db.commit()
        admin_states.pop(uid)
        await update.message.reply_text("✅ تم التحويل")

# ========= RUN =========
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="admin"))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
