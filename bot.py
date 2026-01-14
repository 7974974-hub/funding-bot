import os
import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS force_channels (
    username TEXT PRIMARY KEY
)""")

cur.execute("""CREATE TABLE IF NOT EXISTS collect_channels (
    username TEXT PRIMARY KEY,
    reward INTEGER
)""")

db.commit()

# ================= KEYBOARDS =================
def main_menu():
    return ReplyKeyboardMarkup([
        ["🎯 تجميع نقاط", "💰 رصيدي"],
        ["🔁 تحويل نقاط", "👥 رابط الدعوة"],
        ["🛒 شراء نقاط", "ℹ️ معلومات الحساب"]
    ], resize_keyboard=True)

def admin_menu():
    return ReplyKeyboardMarkup([
        ["➕ إضافة نقاط", "🚫 حظر مستخدم"],
        ["✅ فك حظر", "📊 الإحصائيات"],
        ["📢 قنوات الاشتراك الإجباري"],
        ["🎯 قنوات تجميع النقاط"],
        ["⬅️ رجوع"]
    ], resize_keyboard=True)

def force_menu():
    return ReplyKeyboardMarkup([
        ["➕ إضافة قناة اشتراك"],
        ["❌ حذف قناة اشتراك"],
        ["📋 عرض قنوات الاشتراك"],
        ["⬅️ رجوع"]
    ], resize_keyboard=True)

def collect_menu():
    return ReplyKeyboardMarkup([
        ["➕ إضافة قناة تجميع"],
        ["❌ حذف قناة تجميع"],
        ["📋 عرض قنوات التجميع"],
        ["⬅️ رجوع"]
    ], resize_keyboard=True)

# ================= HELPERS =================
async def check_force(update, context):
    cur.execute("SELECT username FROM force_channels")
    channels = cur.fetchall()
    for (ch,) in channels:
        try:
            member = await context.bot.get_chat_member(ch, update.effective_user.id)
            if member.status in ["left", "kicked"]:
                return False, ch
        except:
            return False, ch
    return True, None

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    row = cur.fetchone()
    if row and row[0] == 1:
        return

    cur.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    db.commit()

    ok, ch = await check_force(update, context)
    if not ok:
        await update.message.reply_text(
            f"🚫 لازم تشترك بالقناة أولاً:\nhttps://t.me/{ch.replace('@','')}\n\nوبعدها اكتب /start"
        )
        return

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\nاختر من القائمة 👇",
        reply_markup=main_menu()
    )

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())

# ================= MESSAGES =================
async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    # رجوع
    if text == "⬅️ رجوع":
        if uid == ADMIN_ID:
            await update.message.reply_text("القائمة الرئيسية", reply_markup=main_menu())
        return

    # ADMIN MENUS
    if uid == ADMIN_ID:
        if text == "📢 قنوات الاشتراك الإجباري":
            await update.message.reply_text("إدارة قنوات الاشتراك", reply_markup=force_menu())
            return

        if text == "🎯 قنوات تجميع النقاط":
            await update.message.reply_text("إدارة قنوات التجميع", reply_markup=collect_menu())
            return

        # FORCE CHANNELS
        if text == "➕ إضافة قناة اشتراك":
            context.user_data["wait"] = "add_force"
            await update.message.reply_text("أرسل يوزر القناة مثل:\n@channel")
            return

        if context.user_data.get("wait") == "add_force":
            cur.execute("INSERT OR IGNORE INTO force_channels VALUES(?)", (text,))
            db.commit()
            context.user_data.clear()
            await update.message.reply_text("✅ تم إضافة قناة اشتراك")
            return

        if text == "📋 عرض قنوات الاشتراك":
            cur.execute("SELECT username FROM force_channels")
            ch = cur.fetchall()
            msg = "\n".join([c[0] for c in ch]) or "لا توجد قنوات"
            await update.message.reply_text(msg)
            return

        # COLLECT CHANNELS
        if text == "➕ إضافة قناة تجميع":
            context.user_data["wait"] = "add_collect"
            await update.message.reply_text("أرسل:\n@channel 10")
            return

        if context.user_data.get("wait") == "add_collect":
            try:
                ch, pts = text.split()
                cur.execute("INSERT OR REPLACE INTO collect_channels VALUES(?,?)", (ch, int(pts)))
                db.commit()
                context.user_data.clear()
                await update.message.reply_text("✅ تمت إضافة قناة تجميع")
            except:
                await update.message.reply_text("❌ صيغة خطأ")
            return

    # USER BUTTONS
    if text == "💰 رصيدي":
        cur.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        pts = cur.fetchone()[0]
        await update.message.reply_text(f"💰 رصيدك: {pts} نقطة")

    elif text == "🎯 تجميع نقاط":
        cur.execute("SELECT username,reward FROM collect_channels")
        rows = cur.fetchall()
        if not rows:
            await update.message.reply_text("❌ لا توجد قنوات حالياً")
            return
        msg = "🎯 قنوات التجميع:\n"
        for ch, r in rows:
            msg += f"{ch} = {r} نقطة\n"
        await update.message.reply_text(msg)

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
