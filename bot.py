import sqlite3
import time
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ====== الإعدادات ======
TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581

COLLECT_CHANNEL = "@Bot_TMWIK"
COLLECT_POINTS = 10
DAILY_POINTS = 20

# ====== DATABASE ======
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS daily (
    user_id INTEGER PRIMARY KEY,
    last_claim INTEGER
)
""")

db.commit()

# ====== القوائم ======
user_keyboard = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط", "📢 تمويل قناتك"],
        ["ℹ️ معلومات الحساب", "💳 شراء نقاط"],
        ["🎁 250 نقطة مجاناً"]
    ],
    resize_keyboard=True
)

admin_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ إضافة نقاط", "⛔ حظر مستخدم"],
        ["📊 الإحصائيات"],
        ["🔙 رجوع"]
    ],
    resize_keyboard=True
)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, points) VALUES (?,0)", (user_id,))
        db.commit()

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك\nاختر من القائمة 👇",
        reply_markup=user_keyboard
    )

# ====== معلومات الحساب ======
async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = cursor.fetchone()[0]
    await update.message.reply_text(
        f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}"
    )

# ====== تجميع نقاط ======
async def collect_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(COLLECT_CHANNEL, user_id)
        if member.status in ["member", "administrator", "creator"]:
            cursor.execute(
                "UPDATE users SET points = points + ? WHERE user_id=?",
                (COLLECT_POINTS, user_id)
            )
            db.commit()
            await update.message.reply_text(
                f"✅ تم إضافة {COLLECT_POINTS} نقاط لرصيدك 🎯"
            )
        else:
            await update.message.reply_text(
                f"❌ اشترك بالقناة أولاً:\nhttps://t.me/{COLLECT_CHANNEL[1:]}"
            )
    except:
        await update.message.reply_text(
            f"❌ اشترك بالقناة أولاً:\nhttps://t.me/{COLLECT_CHANNEL[1:]}"
        )

# ====== هدية يومية ======
async def daily_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = int(time.time())

    cursor.execute("SELECT last_claim FROM daily WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row and now - row[0] < 86400:
        await update.message.reply_text("⏳ أخذت هديتك اليوم، ارجع بعد 24 ساعة")
        return

    cursor.execute(
        "INSERT OR REPLACE INTO daily (user_id, last_claim) VALUES (?,?)",
        (user_id, now)
    )
    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (DAILY_POINTS, user_id)
    )
    db.commit()

    await update.message.reply_text(
        f"🎁 تم إضافة {DAILY_POINTS} نقطة كهدية يومية"
    )

# ====== تمويل قناتك ======
async def fund_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 أرسل يوزر قناتك ليتم التمويل")

# ====== شراء نقاط ======
async def buy_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💳 لشراء النقاط راسل الأدمن مباشرة:\n@YOUMARN"
    )

# ====== لوحة الأدمن ======
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "👑 لوحة الأدمن (جاهزة كما هي)",
        reply_markup=admin_keyboard
    )

# ====== تشغيل البوت ======
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))

app.add_handler(MessageHandler(filters.Regex("معلومات الحساب"), account_info))
app.add_handler(MessageHandler(filters.Regex("تجميع نقاط"), collect_points))
app.add_handler(MessageHandler(filters.Regex("250 نقطة مجاناً"), daily_gift))
app.add_handler(MessageHandler(filters.Regex("تمويل قناتك"), fund_channel))
app.add_handler(MessageHandler(filters.Regex("شراء نقاط"), buy_points))

print("Bot is running...")
app.run_polling()
