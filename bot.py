import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6858655581
BOT_NAME = "بوت تمويلك"

# ================= DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    banned INTEGER DEFAULT 0
)
""")

# قنوات اشتراك إجباري (تفتح البوت)
cur.execute("""
CREATE TABLE IF NOT EXISTS force_channels (
    username TEXT PRIMARY KEY
)
""")

# قنوات تجميع نقاط (مهام)
cur.execute("""
CREATE TABLE IF NOT EXISTS reward_channels (
    username TEXT PRIMARY KEY,
    reward INTEGER DEFAULT 10
)
""")

# لمنع التكرار (مرة وحدة لكل قناة)
cur.execute("""
CREATE TABLE IF NOT EXISTS user_rewards (
    user_id INTEGER,
    channel TEXT,
    PRIMARY KEY (user_id, channel)
)
""")

db.commit()

# ================= MENUS =================
def user_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة نقاط", callback_data="add_points")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="ban_user")],
        [InlineKeyboardButton("✅ فك حظر", callback_data="unban_user")],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data="stats")],
        [InlineKeyboardButton("🎯 قنوات تجميع النقاط", callback_data="reward_menu")]
    ])

def reward_admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ إضافة قناة تجميع", callback_data="reward_add")],
        [InlineKeyboardButton("❌ حذف قناة تجميع", callback_data="reward_del")],
        [InlineKeyboardButton("📋 عرض قنوات التجميع", callback_data="reward_list")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data="admin_back")]
    ])

# ================= HELPERS =================
async def check_force_sub(bot, user_id):
    cur.execute("SELECT username FROM force_channels")
    rows = cur.fetchall()
    for (ch,) in rows:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    # حظر
    cur.execute("SELECT banned FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if r and r[0] == 1:
        return

    # اشتراك إجباري
    if not await check_force_sub(context.bot, uid):
        cur.execute("SELECT username FROM force_channels")
        chs = cur.fetchall()
        if chs:
            btns = [[InlineKeyboardButton(c[0], url=f"https://t.me/{c[0].replace('@','')}")] for c in chs]
            await update.message.reply_text(
                "🚫 لازم تشترك بالقنوات أولاً ثم /start",
                reply_markup=InlineKeyboardMarkup(btns)
            )
            return

    cur.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
    db.commit()

    await update.message.reply_text(
        f"👋 أهلاً بك في {BOT_NAME}",
        reply_markup=user_menu()
    )

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())

# ================= CALLBACKS =================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    d = q.data

    # ===== USER =====
    if d == "balance":
        cur.execute("SELECT points FROM users WHERE user_id=?", (uid,))
        p = cur.fetchone()[0]
        await q.message.reply_text(f"💰 رصيدك: {p} نقطة")

    elif d == "invite":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await q.message.reply_text(f"👥 رابطك:\n{link}")

    elif d == "buy":
        await q.message.reply_text("🛒 شراء نقاط\nراسل الأدمن")

    elif d == "collect":
        cur.execute("SELECT username, reward FROM reward_channels")
        rows = cur.fetchall()
        if not rows:
            await q.message.reply_text("❌ لا توجد قنوات تجميع حالياً")
            return

        text = "📢 اشترك بالقنوات وخذ نقاط:\n\n"
        btns = []
        for ch, rw in rows:
            text += f"{ch} ➜ {rw} نقاط\n"
            btns.append([
                InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}"),
                InlineKeyboardButton("تحقق ✅", callback_data=f"check|{ch}")
            ])
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(btns))

    elif d.startswith("check|"):
        ch = d.split("|")[1]
        # مرة وحدة
        cur.execute("SELECT 1 FROM user_rewards WHERE user_id=? AND channel=?", (uid, ch))
        if cur.fetchone():
            await q.message.reply_text("⚠️ أخذت نقاط هذه القناة مسبقاً")
            return
        try:
            m = await context.bot.get_chat_member(ch, uid)
            if m.status not in ["member", "administrator", "creator"]:
                raise Exception
        except:
            await q.message.reply_text("❌ لم تشترك بعد")
            return

        cur.execute("SELECT reward FROM reward_channels WHERE username=?", (ch,))
        rw = cur.fetchone()[0]
        cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (rw, uid))
        cur.execute("INSERT INTO user_rewards (user_id, channel) VALUES (?,?)", (uid, ch))
        db.commit()
        await q.message.reply_text(f"✅ تم إضافة {rw} نقاط")

    # ===== ADMIN =====
    if uid != ADMIN_ID:
        return

    if d == "reward_menu":
        await q.message.reply_text("🎯 قنوات تجميع النقاط", reply_markup=reward_admin_menu())

    elif d == "reward_list":
        cur.execute("SELECT username, reward FROM reward_channels")
        rows = cur.fetchall()
        if not rows:
            await q.message.reply_text("❌ لا توجد قنوات")
        else:
            msg = "📋 قنوات التجميع:\n\n"
            for ch, rw in rows:
                msg += f"{ch} ➜ {rw} نقاط\n"
            await q.message.reply_text(msg)

    elif d == "reward_add":
        context.user_data["state"] = "reward_add"
        await q.message.reply_text("✏️ أرسل:\n@channel (النقاط 10 تلقائي)")

    elif d == "reward_del":
        context.user_data["state"] = "reward_del"
        await q.message.reply_text("✏️ أرسل:\n@channel")

    elif d == "admin_back":
        await q.message.reply_text("👑 لوحة الأدمن", reply_markup=admin_menu())

    elif d == "stats":
        cur.execute("SELECT COUNT(*) FROM users")
        await q.message.reply_text(f"📊 المستخدمين: {cur.fetchone()[0]}")

# ================= TEXT =================
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    st = context.user_data.get("state")
    if not st:
        return
    txt = update.message.text.strip()
    if st == "reward_add":
        if not txt.startswith("@"):
            await update.message.reply_text("❌ لازم @")
            return
        cur.execute("INSERT OR IGNORE INTO reward_channels (username, reward) VALUES (?,10)", (txt,))
        db.commit()
        await update.message.reply_text("✅ تمت إضافة قناة التجميع")
    elif st == "reward_del":
        cur.execute("DELETE FROM reward_channels WHERE username=?", (txt,))
        db.commit()
        await update.message.reply_text("❌ تم حذف قناة التجميع")
    context.user_data.clear()

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
