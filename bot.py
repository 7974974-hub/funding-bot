import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581

# ====== DATABASE ======
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value INTEGER
)
""")

cursor.execute("INSERT OR IGNORE INTO settings VALUES ('invite_points', 10)")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('gift_points', 50)")
db.commit()

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?,0)", (user_id,))
    db.commit()

    kb = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="gift")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🔗 رابط الدعوة", callback_data="invite")]
    ]

    if user_id == ADMIN_ID:
        kb.append([InlineKeyboardButton("🛠 لوحة الأدمن", callback_data="admin")])

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ====== CALLBACKS ======
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        p = cursor.fetchone()[0]
        await q.message.reply_text(f"💰 رصيدك: {p}")

    elif q.data == "gift":
        cursor.execute("SELECT value FROM settings WHERE key='gift_points'")
        g = cursor.fetchone()[0]
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (g, uid))
        db.commit()
        await q.message.reply_text(f"🎁 تم إضافة {g} نقطة")

    elif q.data == "invite":
        cursor.execute("SELECT value FROM settings WHERE key='invite_points'")
        ip = cursor.fetchone()[0]
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.message.reply_text(f"🔗 رابطك:\n{link}\n👤 كل شخص = {ip} نقطة")

    elif q.data == "admin" and uid == ADMIN_ID:
        kb = [
            [InlineKeyboardButton("➕ إضافة نقاط", callback_data="add")],
            [InlineKeyboardButton("➖ خصم نقاط", callback_data="remove")],
            [InlineKeyboardButton("⚙️ إعدادات", callback_data="settings")],
            [InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")],
            [InlineKeyboardButton("📊 إحصائيات", callback_data="stats")]
        ]
        await q.message.reply_text("🛠 لوحة الأدمن", reply_markup=InlineKeyboardMarkup(kb))

    elif q.data == "stats":
        cursor.execute("SELECT COUNT(*) FROM users")
        c = cursor.fetchone()[0]
        await q.message.reply_text(f"👥 عدد المستخدمين: {c}")

    elif q.data == "settings":
        await q.message.reply_text(
            "⚙️ الإعدادات:\n"
            "/set_invite 20\n"
            "/set_gift 100"
        )

    elif q.data == "add":
        await q.message.reply_text("✍️ اكتب:\n/add user_id points")

    elif q.data == "remove":
        await q.message.reply_text("✍️ اكتب:\n/remove user_id points")

    elif q.data == "broadcast":
        await q.message.reply_text("✍️ ارسل الرسالة للإذاعة")

# ====== ADMIN COMMANDS ======
async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text.split()

    if text[0] == "/add":
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (int(text[2]), int(text[1])))
        db.commit()
        await update.message.reply_text("✅ تم إضافة النقاط")

    elif text[0] == "/remove":
        cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (int(text[2]), int(text[1])))
        db.commit()
        await update.message.reply_text("✅ تم الخصم")

    elif text[0] == "/set_invite":
        cursor.execute("UPDATE settings SET value=? WHERE key='invite_points'", (int(text[1]),))
        db.commit()
        await update.message.reply_text("✅ تم تعديل نقاط الدعوة")

    elif text[0] == "/set_gift":
        cursor.execute("UPDATE settings SET value=? WHERE key='gift_points'", (int(text[1]),))
        db.commit()
        await update.message.reply_text("✅ تم تعديل هدية التجميع")

# ====== RUN ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & filters.COMMAND, admin_cmd))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
