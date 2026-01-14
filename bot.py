import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, points INTEGER DEFAULT 0, banned INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS force_channels (channel TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS collect_channels (channel TEXT, reward INTEGER)")
db.commit()

# ================= HELPERS =================
def is_admin(user_id):
    return user_id == ADMIN_ID

async def check_force_sub(update, context):
    user_id = update.effective_user.id
    cur.execute("SELECT channel FROM force_channels")
    channels = cur.fetchall()

    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch[0], user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    cur.execute("SELECT banned FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if row and row[0] == 1:
        return

    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    db.commit()

    if not await check_force_sub(update, context):
        cur.execute("SELECT channel FROM force_channels")
        txt = "🚫 لازم تشترك بالقنوات أولاً:\n\n"
        for ch in cur.fetchall():
            txt += f"{ch[0]}\n"
        await update.message.reply_text(txt + "\nوبعدها اكتب /start")
        return

    keyboard = [
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("🔄 تحويل نقاط", callback_data="transfer")],
        [InlineKeyboardButton("♻️ استبدال نقاط", callback_data="redeem")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ]

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}\nاختر من القائمة 👇",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= USER BUTTONS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id

    if q.data == "balance":
        cur.execute("SELECT points FROM users WHERE id=?", (uid,))
        pts = cur.fetchone()[0]
        await q.message.reply_text(f"💰 رصيدك: {pts} نقطة")

    elif q.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.message.reply_text(f"👥 رابطك:\n{link}\nكل دعوة = نقاط")

    elif q.data == "collect":
        cur.execute("SELECT channel, reward FROM collect_channels")
        rows = cur.fetchall()
        if not rows:
            await q.message.reply_text("لا توجد قنوات تجميع حالياً")
        else:
            txt = "🎯 قنوات تجميع النقاط:\n\n"
            for ch, r in rows:
                txt += f"{ch} ➜ {r} نقاط\n"
            await q.message.reply_text(txt)

    elif q.data == "transfer":
        await q.message.reply_text("🔄 أرسل:\n/transfer ID AMOUNT")

    elif q.data == "redeem":
        await q.message.reply_text("♻️ أرسل طلب الاستبدال للأدمن")

    elif q.data == "buy":
        await q.message.reply_text("🛒 شراء نقاط\nراسل الأدمن @YQOMARN")

# ================= ADMIN PANEL =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data="a_add")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="a_ban")],
        [InlineKeyboardButton("✅ فك حظر", callback_data="a_unban")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="a_stats")],
        [InlineKeyboardButton("📢 إدارة الاشتراك الإجباري", callback_data="a_force")],
        [InlineKeyboardButton("🎯 قنوات تجميع النقاط", callback_data="a_collect")]
    ]

    await update.message.reply_text(
        "👑 لوحة الأدمن",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================= ADMIN BUTTONS =================
async def admin_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not is_admin(q.from_user.id):
        return

    if q.data == "a_stats":
        cur.execute("SELECT COUNT(*) FROM users")
        u = cur.fetchone()[0]
        await q.message.reply_text(f"📊 عدد المستخدمين: {u}")

    elif q.data == "a_force":
        await q.message.reply_text("أرسل يوزر القناة لإضافتها اشتراك إجباري")

        context.user_data["mode"] = "force"

    elif q.data == "a_collect":
        await q.message.reply_text("أرسل: @channel points")
        context.user_data["mode"] = "collect"

    elif q.data == "a_add":
        await q.message.reply_text("أرسل: ID points")
        context.user_data["mode"] = "add_points"

    elif q.data == "a_ban":
        await q.message.reply_text("أرسل ID للحظر")
        context.user_data["mode"] = "ban"

    elif q.data == "a_unban":
        await q.message.reply_text("أرسل ID لفك الحظر")
        context.user_data["mode"] = "unban"

# ================= ADMIN INPUT =================
async def admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    if mode == "force":
        cur.execute("INSERT INTO force_channels VALUES (?)", (text,))
        db.commit()
        await update.message.reply_text("✅ تمت إضافة قناة اشتراك إجباري")

    elif mode == "collect":
        ch, pts = text.split()
        cur.execute("INSERT INTO collect_channels VALUES (?,?)", (ch, int(pts)))
        db.commit()
        await update.message.reply_text("✅ تمت إضافة قناة تجميع")

    elif mode == "add_points":
        uid, pts = text.split()
        cur.execute("UPDATE users SET points = points + ? WHERE id=?", (int(pts), int(uid)))
        db.commit()
        await update.message.reply_text("✅ تم إضافة النقاط")

    elif mode == "ban":
        cur.execute("UPDATE users SET banned=1 WHERE id=?", (int(text),))
        db.commit()
        await update.message.reply_text("🚫 تم الحظر")

    elif mode == "unban":
        cur.execute("UPDATE users SET banned=0 WHERE id=?", (int(text),))
        db.commit()
        await update.message.reply_text("✅ تم فك الحظر")

    context.user_data.clear()

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(CallbackQueryHandler(admin_buttons, pattern="^a_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_input))
    app.run_polling()

if __name__ == "__main__":
    main()
