import os
import sqlite3
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import ReplyKeyboardMarkup

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

FORCE_CHANNELS = [
    "@Bot_TMWIK"
]

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    collect_points INTEGER,
    invite_points INTEGER,
    exchange_rate INTEGER
)
""")

cursor.execute("SELECT * FROM settings")
if not cursor.fetchone():
    cursor.execute("INSERT INTO settings VALUES (1, 5, 10, 100)")
db.commit()

# ---------- KEYBOARDS ----------
def user_keyboard():
    return ReplyKeyboardMarkup([
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["🔁 تحويل نقاط", "♻️ استبدال نقاط"],
        ["👥 رابط الدعوة", "🛒 شراء نقاط"],
        ["ℹ️ معلومات الحساب"]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["🚫 حظر مستخدم", "✅ فك حظر"],
        ["🎁 تعديل نقاط التجميع", "👥 تعديل نقاط الدعوة"],
        ["♻️ تعديل الاستبدال", "📊 الإحصائيات"],
        ["🔙 رجوع"]
    ], resize_keyboard=True)

# ---------- CHECK CHANNELS ----------
async def check_channels(bot, user_id):
    for ch in FORCE_CHANNELS:
        try:
            member = await bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await check_channels(context.bot, user_id):
        links = "\n".join([f"https://t.me/{c.replace('@','')}" for c in FORCE_CHANNELS])
        await update.message.reply_text(
            f"🚫 اشترك بالقنوات أولاً:\n{links}\n\nثم /start"
        )
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}",
        reply_markup=user_keyboard()
    )

# ---------- USER ----------
async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    cursor.execute("SELECT points, banned FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if not data or data[1] == 1:
        return

    points = data[0]

    cursor.execute("SELECT collect_points, invite_points, exchange_rate FROM settings")
    collect, invite, rate = cursor.fetchone()

    if text == "💰 رصيدي":
        await update.message.reply_text(f"💰 رصيدك: {points} نقطة")

    elif text == "🎯 تجميع نقاط":
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (collect, user_id))
        db.commit()
        await update.message.reply_text(f"🎁 تم إضافة {collect} نقاط")

    elif text == "👥 رابط الدعوة":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(
            f"👥 رابطك:\n{link}\nكل دعوة = {invite} نقاط"
        )

    elif text == "🔁 تحويل نقاط":
        context.user_data["transfer"] = True
        await update.message.reply_text("✏️ ارسل: آيدي_الشخص عدد_النقاط")

    elif text == "♻️ استبدال نقاط":
        await update.message.reply_text(
            f"♻️ كل {rate} نقطة = 1 تمويل\nراسل الأدمن للاستبدال"
        )

    elif text == "🛒 شراء نقاط":
        await update.message.reply_text("🛒 شراء نقاط\nراسل: @YQOMARN")

    elif text == "ℹ️ معلومات الحساب":
        await update.message.reply_text(f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}")

    elif context.user_data.get("transfer"):
        try:
            to_id, amount = map(int, text.split())
            if amount <= 0 or amount > points:
                raise
            cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (amount, user_id))
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, to_id))
            db.commit()
            await update.message.reply_text("✅ تم تحويل النقاط")
        except:
            await update.message.reply_text("❌ الصيغة خطأ")
        context.user_data.clear()

    elif text == "/admin" and user_id == ADMIN_ID:
        await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_keyboard())

# ---------- ADMIN ----------
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text

    if text == "🚫 حظر مستخدم":
        context.user_data["ban"] = True
        await update.message.reply_text("✏️ ارسل آيدي المستخدم")

    elif text == "✅ فك حظر":
        context.user_data["unban"] = True
        await update.message.reply_text("✏️ ارسل آيدي المستخدم")

    elif text == "🎁 تعديل نقاط التجميع":
        context.user_data["set"] = "collect"
        await update.message.reply_text("✏️ ارسل العدد")

    elif text == "👥 تعديل نقاط الدعوة":
        context.user_data["set"] = "invite"
        await update.message.reply_text("✏️ ارسل العدد")

    elif text == "♻️ تعديل الاستبدال":
        context.user_data["set"] = "exchange"
        await update.message.reply_text("✏️ ارسل عدد النقاط لكل 1 تمويل")

    elif text == "📊 الإحصائيات":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        await update.message.reply_text(f"📊 عدد المستخدمين: {users}")

    elif text.isdigit():
        n = int(text)
        if context.user_data.get("ban"):
            cursor.execute("UPDATE users SET banned=1 WHERE user_id=?", (n,))
            db.commit()
            await update.message.reply_text("🚫 تم الحظر")

        elif context.user_data.get("unban"):
            cursor.execute("UPDATE users SET banned=0 WHERE user_id=?", (n,))
            db.commit()
            await update.message.reply_text("✅ تم فك الحظر")

        elif context.user_data.get("set") == "collect":
            cursor.execute("UPDATE settings SET collect_points=?", (n,))
            db.commit()
            await update.message.reply_text("✅ تم التعديل")

        elif context.user_data.get("set") == "invite":
            cursor.execute("UPDATE settings SET invite_points=?", (n,))
            db.commit()
            await update.message.reply_text("✅ تم التعديل")

        elif context.user_data.get("set") == "exchange":
            cursor.execute("UPDATE settings SET exchange_rate=?", (n,))
            db.commit()
            await update.message.reply_text("✅ تم التعديل")

        context.user_data.clear()

    elif text == "🔙 رجوع":
        await update.message.reply_text("↩️ رجوع", reply_markup=user_keyboard())

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, admin_actions))
    app.add_handler(MessageHandler(filters.TEXT, user_actions))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
