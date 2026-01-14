import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ====== CONFIG ======
TOKEN = "8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI"
ADMIN_ID = 6858655581

# ====== DATABASE ======
db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")
db.commit()

# ====== USER KEYBOARD (13 زر) ======
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

# ====== ADMIN KEYBOARD ======
admin_keyboard = ReplyKeyboardMarkup(
    [
        ["➕ إضافة نقاط"],
        ["🚫 حظر مستخدم", "✅ فك حظر"],
        ["📊 الإحصائيات"],
        ["🏠 رجوع للقائمة"]
    ],
    resize_keyboard=True
)

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cursor.execute("SELECT banned FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()

    if row and row[0] == 1:
        await update.message.reply_text("🚫 أنت محظور")
        return

    if not row:
        cursor.execute(
            "INSERT INTO users (user_id, points, banned) VALUES (?, ?, ?)",
            (user_id, 0, 0)
        )
        db.commit()

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك\nاختر من القائمة 👇",
        reply_markup=user_keyboard
    )

# ====== ADMIN PANEL ======
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ هذا الأمر للأدمن فقط")
        return

    await update.message.reply_text(
        "👑 لوحة الأدمن",
        reply_markup=admin_keyboard
    )

# ====== BUTTON HANDLER ======
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = update.effective_user.id

    # ==== USER ====
    if text == "ℹ️ معلومات الحساب":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await update.message.reply_text(f"🆔 آيديك: {user_id}\n💰 نقاطك: {points}")

    elif text == "🎁 250 نقطة مجاناً":
        cursor.execute("UPDATE users SET points = points + 250 WHERE user_id=?", (user_id,))
        db.commit()
        await update.message.reply_text("🎁 تم إضافة 250 نقطة")

    elif text == "🎉 اضغط هنا (1000 نقطة)":
        cursor.execute("UPDATE users SET points = points + 1000 WHERE user_id=?", (user_id,))
        db.commit()
        await update.message.reply_text("🎉 تم إضافة 1000 نقطة")

    elif text == "🔗 رابط الدعوة":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await update.message.reply_text(f"🔗 رابطك:\n{link}")

    elif text == "🏠 رجوع للقائمة":
        await update.message.reply_text("🏠 القائمة الرئيسية", reply_markup=user_keyboard)

    # ==== ADMIN ====
    elif user_id == ADMIN_ID and text == "➕ إضافة نقاط":
        context.user_data["wait_add"] = True
        await update.message.reply_text("✏️ أرسل:\nID النقاط")

    elif user_id == ADMIN_ID and "wait_add" in context.user_data:
        try:
            uid, pts = map(int, text.split())
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (pts, uid))
            db.commit()
            await update.message.reply_text("✅ تم إضافة النقاط")
        except:
            await update.message.reply_text("❌ الصيغة خطأ")
        context.user_data.pop("wait_add")

    elif user_id == ADMIN_ID and text == "🚫 حظر مستخدم":
        context.user_data["wait_ban"] = True
        await update.message.reply_text("✏️ أرسل آيدي المستخدم")

    elif user_id == ADMIN_ID and "wait_ban" in context.user_data:
        try:
            uid = int(text)
            cursor.execute("UPDATE users SET banned = 1 WHERE user_id=?", (uid,))
            db.commit()
            await update.message.reply_text("🚫 تم الحظر")
        except:
            await update.message.reply_text("❌ خطأ")
        context.user_data.pop("wait_ban")

    elif user_id == ADMIN_ID and text == "📊 الإحصائيات":
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        await update.message.reply_text(f"📊 عدد المستخدمين: {total}")

# ====== RUN ======
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))

print("Bot is running...")
app.run_polling()
