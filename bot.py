import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ====== CONFIG ======
TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581

# ====== DATABASE ======
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
db.commit()

# ====== USER KEYBOARD (13 BUTTONS) ======
user_keyboard = ReplyKeyboardMarkup(
    [
        ["👤 تمويل أعضاء حقيقي"],
        ["🎯 تجميع نقاط", "🔄 تحويل نقاط"],
        ["♻️ تمويلات جارية", "ℹ️ معلومات الحساب"],
        ["🎁 250 نقطة مجاناً"],
        ["🔗 رابط الدعوة", "⚙️ التحديثات"],
        ["🎉 اضغط هنا (1000 نقطة)"],
        ["⭐ شراء نقاط بنجوم"],
        ["🎁 25 عضو مجاناً", "♻️ قسم الاستبدال"],
        ["🏠 رجوع للقائمة"]
    ],
    resize_keyboard=True
)

# ====== ADMIN KEYBOARD (مستقلة) ======
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

# ====== /start USER ======
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
        "👋 أهلاً بك في بوت تمويلك\nاختر من القائمة 👇",
        reply_markup=user_keyboard
    )

# ====== /admin ======
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر مخصص للأدمن فقط")
        return

    await update.message.reply_text(
        "👑 لوحة الأدمن",
        reply_markup=admin_keyboard
    )

# ====== USER INFO ======
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = cursor.fetchone()[0]

    await update.message.reply_text(
        f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}"
    )

# ====== MAIN ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("info", info))

print("Bot is running...")
app.run_polling()
