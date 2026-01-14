import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# ====== الإعدادات ======
BOT_TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ====== قاعدة البيانات ======
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS force_channels (
    channel TEXT PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS collect_channels (
    channel TEXT PRIMARY KEY
)
""")

db.commit()

# ====== لوحات ======
user_keyboard = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["🔄 تحويل نقاط", "👥 رابط الدعوة"],
        ["🛒 شراء نقاط", "ℹ️ معلومات الحساب"],
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ إضافة نقاط", "🚫 حظر مستخدم"],
        ["✅ فك حظر", "📊 الإحصائيات"],
        ["📢 إدارة قنوات الاشتراك"],
        ["🎯 قنوات تجميع النقاط"],
        ["⬅️ رجوع"]
    ],
    resize_keyboard=True
)

force_channels_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ إضافة قناة اشتراك"],
        ["❌ حذف قناة اشتراك"],
        ["📋 عرض قنوات الاشتراك"],
        ["⬅️ رجوع"]
    ],
    resize_keyboard=True
)

collect_channels_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ إضافة قناة تجميع"],
        ["❌ حذف قناة تجميع"],
        ["📋 عرض قنوات التجميع"],
        ["⬅️ رجوع"]
    ],
    resize_keyboard=True
)

# ====== أدوات ======
def is_admin(user_id):
    return user_id == ADMIN_ID

def is_banned(user_id):
    cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    return row and row[0] == 1

# ====== أوامر ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    db.commit()

    if is_banned(user_id):
        await update.message.reply_text("🚫 أنت محظور")
        return

    # فحص الاشتراك الإجباري
    cursor.execute("SELECT channel FROM force_channels")
    channels = cursor.fetchall()

    for (ch,) in channels:
        try:
            member = await context.bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await update.message.reply_text(
                    f"🚫 لازم تشترك بالقناة أولاً:\nhttps://t.me/{ch.lstrip('@')}"
                )
                return
        except:
            pass

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\n👇 اختر من القائمة",
        reply_markup=user_keyboard
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_keyboard)

# ====== رسائل ======
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    if is_banned(user_id):
        return

    # ==== مستخدم ====
    if text == "💰 رصيدي":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await update.message.reply_text(f"💰 رصيدك: {points} نقطة")

    elif text == "👥 رابط الدعوة":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(f"👥 رابطك:\n{link}\n\nكل دعوة = 10 نقاط")

    elif text == "ℹ️ معلومات الحساب":
        await update.message.reply_text(f"🆔 ID: {user_id}\n📌 البوت: {BOT_NAME}")

    elif text == "🎯 تجميع نقاط":
        cursor.execute("SELECT channel FROM collect_channels")
        chans = cursor.fetchall()
        if not chans:
            await update.message.reply_text("❌ لا توجد قنوات حالياً")
        else:
            msg = "🎯 اشترك بالقنوات التالية:\n\n"
            for (c,) in chans:
                msg += f"https://t.me/{c.lstrip('@')}\n"
            await update.message.reply_text(msg)

    # ==== أدمن ====
    elif text == "📢 إدارة قنوات الاشتراك" and is_admin(user_id):
        await update.message.reply_text("📢 إدارة قنوات الاشتراك", reply_markup=force_channels_keyboard)

    elif text == "🎯 قنوات تجميع النقاط" and is_admin(user_id):
        await update.message.reply_text("🎯 إدارة قنوات التجميع", reply_markup=collect_channels_keyboard)

    elif text == "📊 الإحصائيات" and is_admin(user_id):
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await update.message.reply_text(f"📊 عدد المستخدمين: {count}")

    elif text == "⬅️ رجوع":
        if is_admin(user_id):
            await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_keyboard)
        else:
            await update.message.reply_text("⬅️ رجوع", reply_markup=user_keyboard)

# ====== تشغيل ======
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))

print("Bot is running...")
app.run_polling()
