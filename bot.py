import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN =8559491392:AAG0FDmmL26jl3whCOY-sOrScWzehQ7g6VI
ADMIN_ID = 6858655581

db = sqlite3.connect("bot.db", check_same_thread=False)
cr = db.cursor()

cr.execute("""CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY,
points INTEGER DEFAULT 0,
banned INTEGER DEFAULT 0
)""")

cr.execute("""CREATE TABLE IF NOT EXISTS force_channels (
channel TEXT PRIMARY KEY
)""")

cr.execute("""CREATE TABLE IF NOT EXISTS collect_channels (
channel TEXT PRIMARY KEY,
reward INTEGER
)""")

db.commit()

def user_keyboard():
    return ReplyKeyboardMarkup([
        ["🎯 تجميع نقاط", "🔄 تحويل نقاط"],
        ["💰 رصيدي", "👥 رابط الدعوة"],
        ["🛒 شراء نقاط", "♻️ استبدال نقاط"],
        ["ℹ️ معلومات الحساب"]
    ], resize_keyboard=True)

def admin_keyboard():
    return ReplyKeyboardMarkup([
        ["➕ إضافة نقاط", "🚫 حظر مستخدم"],
        ["✅ فك حظر", "📊 الإحصائيات"],
        ["📢 إدارة الاشتراك الإجباري"],
        ["🎯 قنوات تجميع النقاط"],
        ["⬅️ رجوع"]
    ], resize_keyboard=True)

async def check_force(bot, user_id):
    cr.execute("SELECT channel FROM force_channels")
    for (ch,) in cr.fetchall():
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    cr.execute("SELECT banned FROM users WHERE id=?", (uid,))
    r = cr.fetchone()
    if not r:
        cr.execute("INSERT INTO users (id) VALUES (?)", (uid,))
        db.commit()
    elif r[0] == 1:
        return

    if not await check_force(context.bot, uid):
        cr.execute("SELECT channel FROM force_channels")
        chs = cr.fetchall()
        txt = "🚫 اشترك بالقنوات أولاً:\n\n"
        for c in chs:
            txt += f"{c[0]}\n"
        await update.message.reply_text(txt)
        return

    await update.message.reply_text(
        "👋 أهلاً بك في *بوت تمويلك*\nاختر من القائمة 👇",
        reply_markup=user_keyboard(),
        parse_mode="Markdown"
    )

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_keyboard())

async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if text == "💰 رصيدي":
        cr.execute("SELECT points FROM users WHERE id=?", (uid,))
        await update.message.reply_text(f"💰 رصيدك: {cr.fetchone()[0]} نقطة")

    elif text == "👥 رابط الدعوة":
        await update.message.reply_text(
            f"https://t.me/{context.bot.username}?start={uid}\nكل دعوة = 10 نقاط"
        )

    elif text == "🎯 تجميع نقاط":
        cr.execute("SELECT channel,reward FROM collect_channels")
        rows = cr.fetchall()
        if not rows:
            await update.message.reply_text("❌ لا توجد قنوات حالياً")
        else:
            msg = "🎯 قنوات التجميع:\n\n"
            for c,r in rows:
                msg += f"{c} ➜ {r} نقاط\n"
            await update.message.reply_text(msg)

    elif text == "📊 الإحصائيات" and uid == ADMIN_ID:
        cr.execute("SELECT COUNT(*) FROM users")
        await update.message.reply_text(f"👥 المستخدمين: {cr.fetchone()[0]}")

    elif text == "📢 إدارة الاشتراك الإجباري" and uid == ADMIN_ID:
        await update.message.reply_text("أرسل يوزر القناة مع @ للإضافة")

    elif text.startswith("@") and uid == ADMIN_ID:
        cr.execute("INSERT OR IGNORE INTO force_channels VALUES (?)", (text,))
        db.commit()
        await update.message.reply_text("✅ تمت إضافة قناة اشتراك إجباري")

    elif text == "🎯 قنوات تجميع النقاط" and uid == ADMIN_ID:
        await update.message.reply_text("أرسل: @channel 10")

    elif "@" in text and uid == ADMIN_ID and " " in text:
        ch, pts = text.split()
        cr.execute("INSERT OR REPLACE INTO collect_channels VALUES (?,?)", (ch,int(pts)))
        db.commit()
        await update.message.reply_text("✅ تمت إضافة قناة تجميع")

    elif text == "➕ إضافة نقاط" and uid == ADMIN_ID:
        context.user_data["add"] = True
        await update.message.reply_text("أرسل:
