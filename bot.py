import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581
FORCE_CHANNEL = "@Bot_TMWIK"
CHANNEL_LINK = "https://t.me/Bot_TMWIK"
ADMIN_USERNAME = "@YQOMARN"

# ================= DATABASE =================
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value INTEGER
)
""")

cursor.execute("INSERT OR IGNORE INTO settings VALUES ('invite_points', 10)")
cursor.execute("INSERT OR IGNORE INTO settings VALUES ('gift_points', 5)")
db.commit()

# ================= KEYBOARDS =================
user_kb = ReplyKeyboardMarkup(
    [
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["🔗 رابط الدعوة", "🔄 تحويل نقاط"],
        ["🛒 شراء نقاط", "ℹ️ معلومات الحساب"]
    ],
    resize_keyboard=True
)

admin_kb = ReplyKeyboardMarkup(
    [
        ["➕ إضافة نقاط", "➖ خصم نقاط"],
        ["⚙️ الإعدادات", "📢 إذاعة"],
        ["📊 إحصائيات", "🔙 رجوع"]
    ],
    resize_keyboard=True
)

# ================= HELPERS =================
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(FORCE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def get_setting(key):
    cursor.execute("SELECT value FROM settings WHERE key=?", (key,))
    return cursor.fetchone()[0]

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id

    if not await is_subscribed(context.bot, uid):
        await update.message.reply_text(
            f"🚫 لازم تشترك بالقناة أولاً:\n{CHANNEL_LINK}\n\nوبعدها اكتب /start"
        )
        return

    inviter = None
    if context.args:
        try:
            inviter = int(context.args[0])
        except:
            pass

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, points, invited_by) VALUES (?,?,?)",
            (uid, 0, inviter)
        )
        if inviter:
            ip = get_setting("invite_points")
            cursor.execute(
                "UPDATE users SET points = points + ? WHERE user_id=?",
                (ip, inviter)
            )
        db.commit()

    await update.message.reply_text(
        "👋 أهلاً بك في بوت تمويلك",
        reply_markup=user_kb
    )

# ================= USER ACTIONS =================
async def user_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    if text == "💰 رصيدي":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        p = cursor.fetchone()[0]
        await update.message.reply_text(f"💰 رصيدك: {p} نقطة")

    elif text == "🔗 رابط الدعوة":
        ip = get_setting("invite_points")
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(
            f"🔗 رابطك:\n{link}\n\n👤 كل شخص = {ip} نقطة"
        )

    elif text == "🎯 تجميع نقاط":
        gp = get_setting("gift_points")
        cursor.execute(
            "UPDATE users SET points = points + ? WHERE user_id=?",
            (gp, uid)
        )
        db.commit()
        await update.message.reply_text(f"🎁 تم إضافة {gp} نقاط")

    elif text == "🔄 تحويل نقاط":
        await update.message.reply_text(
            "🔄 التحويل قريباً\n(سيُفعل من الأدمن)"
        )

    elif text == "🛒 شراء نقاط":
        await update.message.reply_text(
            f"🛒 شراء نقاط\nراسل الأدمن: {ADMIN_USERNAME}"
        )

    elif text == "ℹ️ معلومات الحساب":
        await update.message.reply_text(
            f"👤 آيديك: {uid}\n📌 البوت: تمويل وتجميع نقاط"
        )

    # ---------- ADMIN ----------
    elif text == "/admin" and uid == ADMIN_ID:
        await update.message.reply_text(
            "🛠 لوحة الأدمن",
            reply_markup=admin_kb
        )

    elif uid == ADMIN_ID and text == "➕ إضافة نقاط":
        context.user_data["mode"] = "add"
        await update.message.reply_text("✏️ ارسل:\nID POINTS")

    elif uid == ADMIN_ID and text == "➖ خصم نقاط":
        context.user_data["mode"] = "remove"
        await update.message.reply_text("✏️ ارسل:\nID POINTS")

    elif uid == ADMIN_ID and text == "⚙️ الإعدادات":
        await update.message.reply_text(
            "⚙️ الإعدادات:\n"
            "/set_invite 20\n"
            "/set_gift 10"
        )

    elif uid == ADMIN_ID and text == "📢 إذاعة":
        context.user_data["broadcast"] = True
        await update.message.reply_text("✏️ ارسل رسالة الإذاعة")

    elif uid == ADMIN_ID and text == "📊 إحصائيات":
        cursor.execute("SELECT COUNT(*) FROM users")
        c = cursor.fetchone()[0]
        await update.message.reply_text(f"👥 عدد المستخدمين: {c}")

    elif uid == ADMIN_ID and text == "🔙 رجوع":
        await update.message.reply_text("رجعت للقائمة", reply_markup=user_kb)

    # ---------- ADMIN TEXT INPUT ----------
    elif uid == ADMIN_ID and context.user_data.get("mode"):
        try:
            tid, pts = map(int, text.split())
        except:
            await update.message.reply_text("❌ صيغة خاطئة")
            return

        if context.user_data["mode"] == "add":
            cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (pts, tid))
            db.commit()
            await update.message.reply_text("✅ تم إضافة النقاط")

        elif context.user_data["mode"] == "remove":
            cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (pts, tid))
            db.commit()
            await update.message.reply_text("✅ تم الخصم")

        context.user_data["mode"] = None

    elif uid == ADMIN_ID and context.user_data.get("broadcast"):
        cursor.execute("SELECT user_id FROM users")
        for u in cursor.fetchall():
            try:
                await context.bot.send_message(u[0], text)
            except:
                pass
        context.user_data["broadcast"] = False
        await update.message.reply_text("📢 تم الإرسال")

# ================= COMMAND SETTINGS =================
async def set_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    v = int(context.args[0])
    cursor.execute("UPDATE settings SET value=? WHERE key='invite_points'", (v,))
    db.commit()
    await update.message.reply_text("✅ تم تعديل نقاط الدعوة")

async def set_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    v = int(context.args[0])
    cursor.execute("UPDATE settings SET value=? WHERE key='gift_points'", (v,))
    db.commit()
    await update.message.reply_text("✅ تم تعديل هدية التجميع")

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("set_invite", set_invite))
    app.add_handler(CommandHandler("set_gift", set_gift))
    app.add_handler(MessageHandler(filters.TEXT, user_actions))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
