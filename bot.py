import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"
FORCE_CHANNEL = "@Bot_TMWIK"

# ---------- DATABASE ----------
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    invited INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY,
    gift_points INTEGER,
    invite_points INTEGER
)
""")

cursor.execute("SELECT * FROM settings")
if not cursor.fetchone():
    cursor.execute("INSERT INTO settings VALUES (1, 5, 10)")
db.commit()

# ---------- KEYBOARDS ----------
def user_keyboard():
    return ReplyKeyboardMarkup([
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["🔁 تحويل نقاط", "👥 رابط الدعوة"],
        ["🛒 شراء نقاط", "ℹ️ معلومات الحساب"]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["➕ إضافة نقاط", "➖ خصم نقاط"],
        ["🎁 تعديل هدية التجميع", "👥 تعديل نقاط الدعوة"],
        ["📊 الإحصائيات", "🔙 رجوع"]
    ], resize_keyboard=True)

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        member = await context.bot.get_chat_member(FORCE_CHANNEL, user_id)
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception
    except:
        await update.message.reply_text(
            f"🚫 لازم تشترك بالقناة أولاً:\nhttps://t.me/{FORCE_CHANNEL.replace('@','')}\n\nوبعدها اكتب /start"
        )
        return

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\n👇 اختر من القائمة",
        reply_markup=user_keyboard()
    )

# ---------- USER ACTIONS ----------
async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = cursor.fetchone()[0]

    cursor.execute("SELECT gift_points, invite_points FROM settings")
    gift, invite = cursor.fetchone()

    if text == "💰 رصيدي":
        await update.message.reply_text(f"💰 رصيدك الحالي: {points} نقطة")

    elif text == "🎯 تجميع نقاط":
        cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (gift, user_id))
        db.commit()
        await update.message.reply_text(f"🎁 تم إضافة {gift} نقاط")

    elif text == "👥 رابط الدعوة":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(
            f"👥 رابطك:\n{link}\n\nكل دعوة = {invite} نقاط"
        )

    elif text == "🛒 شراء نقاط":
        await update.message.reply_text("🛒 شراء نقاط\nراسل الأدمن: @YQOMARN")

    elif text == "ℹ️ معلومات الحساب":
        await update.message.reply_text(
            f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}"
        )

    elif text == "/admin" and user_id == ADMIN_ID:
        await update.message.reply_text("👑 لوحة تحكم الأدمن", reply_markup=admin_keyboard())

# ---------- ADMIN ----------
async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        return

    if text == "📊 الإحصائيات":
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(points) FROM users")
        total = cursor.fetchone()[0] or 0
        await update.message.reply_text(
            f"📊 الإحصائيات:\n👥 المستخدمين: {users}\n💰 مجموع النقاط: {total}"
        )

    elif text == "🎁 تعديل هدية التجميع":
        context.user_data["set"] = "gift"
        await update.message.reply_text("✏️ ارسل عدد النقاط الجديد")

    elif text == "👥 تعديل نقاط الدعوة":
        context.user_data["set"] = "invite"
        await update.message.reply_text("✏️ ارسل عدد نقاط الدعوة")

    elif text.isdigit():
        if context.user_data.get("set") == "gift":
            cursor.execute("UPDATE settings SET gift_points=?", (int(text),))
            db.commit()
            await update.message.reply_text("✅ تم تعديل هدية التجميع")

        elif context.user_data.get("set") == "invite":
            cursor.execute("UPDATE settings SET invite_points=?", (int(text),))
            db.commit()
            await update.message.reply_text("✅ تم تعديل نقاط الدعوة")

        context.user_data.clear()

    elif text == "🔙 رجوع":
        await update.message.reply_text("↩️ رجوع", reply_markup=user_keyboard())

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, user_actions))
    app.add_handler(MessageHandler(filters.TEXT, admin_actions))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
