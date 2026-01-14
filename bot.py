import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS channels (
    username TEXT PRIMARY KEY
)
""")

db.commit()

# ================= KEYBOARDS =================
def user_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🔁 تحويل نقاط", callback_data="transfer")],
        [InlineKeyboardButton("♻️ استبدال نقاط", callback_data="redeem")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data="add_points")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user")],
        [InlineKeyboardButton("✅ فك حظر", callback_data="unban_user")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("📢 إدارة القنوات", callback_data="channels_menu")]
    ])

def channels_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة قناة", callback_data="add_channel")],
        [InlineKeyboardButton("❌ حذف قناة", callback_data="remove_channel")],
        [InlineKeyboardButton("📋 عرض القنوات", callback_data="list_channels")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")]
    ])

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cur.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row and row[0] == 1:
        return

    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\nاختر من القائمة 👇",
        reply_markup=user_menu()
    )

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())

# ================= CALLBACKS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    # ===== USER =====
    if data == "balance":
        cur.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        p = cur.fetchone()[0]
        await query.message.reply_text(f"💰 رصيدك: {p} نقطة")

    elif data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await query.message.reply_text(f"👥 رابطك:\n{link}\nكل دعوة = 10 نقاط")

    elif data == "buy":
        await query.message.reply_text("🛒 شراء نقاط\nراسل الأدمن")

    elif data == "collect":
        await query.message.reply_text("🎯 سيتم إضافة قنوات للتجميع قريباً")

    elif data == "transfer":
        await query.message.reply_text("🔁 اكتب ID المستخدم والمبلغ")

    elif data == "redeem":
        await query.message.reply_text("♻️ الاستبدال قيد الإعداد")

    # ===== ADMIN =====
    if uid != ADMIN_ID:
        return

    if data == "channels_menu":
        await query.message.reply_text("📢 إدارة القنوات", reply_markup=channels_menu())

    elif data == "list_channels":
        cur.execute("SELECT username FROM channels")
        rows = cur.fetchall()
        if not rows:
            await query.message.reply_text("❌ لا توجد قنوات")
        else:
            txt = "\n".join([f"@{r[0]}" for r in rows])
            await query.message.reply_text(f"📋 القنوات:\n{txt}")

    elif data == "admin_back":
        await query.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())

    elif data == "stats":
        cur.execute("SELECT COUNT(*) FROM users")
        count = cur.fetchone()[0]
        await query.message.reply_text(f"📊 عدد المستخدمين: {count}")

    elif data == "add_channel":
        context.user_data["state"] = "add_channel"
        await query.message.reply_text("✏️ أرسل يوزر القناة بدون @")

    elif data == "remove_channel":
        context.user_data["state"] = "remove_channel"
        await query.message.reply_text("✏️ أرسل يوزر القناة بدون @")

# ================= TEXT HANDLER =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    state = context.user_data.get("state")
    text = update.message.text.replace("@", "")

    if state == "add_channel":
        cur.execute("INSERT OR IGNORE INTO channels VALUES (?)", (text,))
        db.commit()
        await update.message.reply_text("✅ تم إضافة القناة")
        context.user_data.clear()

    elif state == "remove_channel":
        cur.execute("DELETE FROM channels WHERE username=?", (text,))
        db.commit()
        await update.message.reply_text("❌ تم حذف القناة")
        context.user_data.clear()

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
