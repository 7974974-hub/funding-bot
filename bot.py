import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581
ADMIN_USERNAME = "@YOUMARN"

# ---------- DATABASE ----------
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0
)
""")
db.commit()

# ---------- USER KEYBOARD ----------
user_keyboard = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط"],
        ["📣 تمويل قناتك"],
        ["ℹ️ معلومات الحساب"],
        ["💳 شراء نقاط"]
    ],
    resize_keyboard=True
)

# ---------- START ----------
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

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 لوحة الأدمن جاهزة (كما هي بدون تغيير)")

# ---------- ROUTER ----------
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # معلومات الحساب
    if text == "ℹ️ معلومات الحساب":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await update.message.reply_text(
            f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}"
        )

    # شراء نقاط
    elif text == "💳 شراء نقاط":
        await update.message.reply_text(
            f"💳 لشراء النقاط راسل الأدمن:\n{ADMIN_USERNAME}"
        )

    # تجميع نقاط (placeholder)
    elif text == "🎯 تجميع نقاط":
        await update.message.reply_text("🎯 سيتم تفعيل تجميع النقاط لاحقاً")

    # تمويل قناة
    elif text == "📣 تمويل قناتك":
        context.user_data["step"] = "channel"
        await update.message.reply_text("📣 أرسل يوزر القناة:")

    # خطوات تمويل القناة
    elif context.user_data.get("step") == "channel":
        context.user_data["channel"] = text
        context.user_data["step"] = "points"
        await update.message.reply_text("🔢 أرسل عدد النقاط:")

    elif context.user_data.get("step") == "points":
        try:
            points = int(text)
        except:
            await update.message.reply_text("❌ أرسل رقم صحيح")
            return

        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        user_points = cursor.fetchone()[0]

        if user_points < points:
            await update.message.reply_text("❌ نقاطك غير كافية")
            context.user_data.clear()
            return

        cursor.execute(
            "UPDATE users SET points = points - ? WHERE user_id=?",
            (points, user_id)
        )
        db.commit()

        channel = context.user_data["channel"]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                "📣 طلب تمويل قناة\n\n"
                f"👤 المستخدم: {user_id}\n"
                f"📢 القناة: {channel}\n"
                f"💰 النقاط: {points}"
            )
        )

        await update.message.reply_text("✅ تم إرسال طلبك للأدمن")
        context.user_data.clear()

# ---------- MAIN ----------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

print("Bot is running...")
app.run_polling()
