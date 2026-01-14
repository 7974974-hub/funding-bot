import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581
COLLECT_POINTS = 10

# ===== DATABASE =====
db = sqlite3.connect("bot.db", check_same_thread=False)
c = db.cursor()

c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, points INTEGER)")
c.execute("CREATE TABLE IF NOT EXISTS collected (id INTEGER PRIMARY KEY)")
db.commit()

# ===== KEYBOARD =====
menu = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط"],
        ["📢 تمويل قناتك"],
        ["ℹ️ معلومات الحساب"],
        ["💳 شراء نقاط"]
    ],
    resize_keyboard=True
)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    c.execute("INSERT OR IGNORE INTO users (id, points) VALUES (?,0)", (uid,))
    db.commit()
    await update.message.reply_text("👋 أهلاً بك\nاختر من القائمة 👇", reply_markup=menu)

# ===== INFO =====
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    c.execute("SELECT points FROM users WHERE id=?", (uid,))
    pts = c.fetchone()[0]
    await update.message.reply_text(f"🆔 آيديك: {uid}\n💰 نقاطك: {pts}")

# ===== COLLECT =====
async def collect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    c.execute("SELECT id FROM collected WHERE id=?", (uid,))
    if c.fetchone():
        await update.message.reply_text("❌ أنت جمّعت النقاط مسبقاً")
        return

    c.execute("UPDATE users SET points = points + ? WHERE id=?", (COLLECT_POINTS, uid))
    c.execute("INSERT INTO collected (id) VALUES (?)", (uid,))
    db.commit()
    await update.message.reply_text(f"✅ تم إضافة {COLLECT_POINTS} نقاط لرصيدك")

# ===== FUND =====
async def fund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 أرسل يوزر قناتك ليتم التمويل")

# ===== BUY =====
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💳 لشراء النقاط راسل الأدمن:\n@YOUMARN")

# ===== ADMIN =====
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👑 لوحة الأدمن جاهزة")

# ===== RUN =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))

app.add_handler(MessageHandler(filters.Regex("معلومات الحساب"), info))
app.add_handler(MessageHandler(filters.Regex("تجميع نقاط"), collect))
app.add_handler(MessageHandler(filters.Regex("تمويل قناتك"), fund))
app.add_handler(MessageHandler(filters.Regex("شراء نقاط"), buy))

print("Bot running...")
app.run_polling()
