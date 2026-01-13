import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 123456789  # 🔴 حط آيديك هنا
CHANNEL_USERNAME = "@Bot_TMWIK"

# ---------- DATABASE ----------
db = sqlite3.connect("users.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    inviter INTEGER,
    joined INTEGER DEFAULT 0
)
""")
db.commit()

# ---------- HELPERS ----------
async def is_subscribed(bot, user_id):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 تجميع نقاط", callback_data="collect")],
        [InlineKeyboardButton("👥 رابط الدعوة", callback_data="invite")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("🛒 شراء نقاط", callback_data="buy")],
        [InlineKeyboardButton("🏧 سحب نقاط", callback_data="withdraw")]
    ])

# ---------- START ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    inviter = None

    if context.args:
        try:
            inviter = int(context.args[0])
        except:
            pass

    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user.id,))
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (user_id, points, inviter) VALUES (?, ?, ?)",
            (user.id, 0, inviter)
        )
        if inviter:
            cursor.execute(
                "UPDATE users SET points = points + 10 WHERE user_id=?",
                (inviter,)
            )
        db.commit()

    await update.message.reply_text(
        "👋 أهلاً بك في *بوت تمويلك*\nاختر من القائمة 👇",
        reply_markup=menu(),
        parse_mode="Markdown"
    )

# ---------- BUTTONS ----------
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "balance":
        cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
        points = cursor.fetchone()[0]
        await query.message.reply_text(f"💰 رصيدك: {points} نقطة")

    elif query.data == "invite":
        link = f"https://t.me/{context.bot.username}?start={user_id}"
        await query.message.reply_text(
            f"👥 رابطك:\n{link}\n\n+10 نقاط لكل شخص"
        )

    elif query.data == "collect":
        if not await is_subscribed(context.bot, user_id):
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 اشترك بالقناة", url="https://t.me/Bot_TMWIK")],
                [InlineKeyboardButton("✅ تحقق", callback_data="check")]
            ])
            await query.message.reply_text(
                "❌ لازم تشترك بالقناة أولاً",
                reply_markup=btn
            )
        else:
            cursor.execute(
                "UPDATE users SET points = points + 5 WHERE user_id=?",
                (user_id,)
            )
            db.commit()
            await query.message.reply_text("✅ تم إضافة 5 نقاط")

    elif query.data == "check":
        if await is_subscribed(context.bot, user_id):
            cursor.execute(
                "UPDATE users SET points = points + 5 WHERE user_id=?",
                (user_id,)
            )
            db.commit()
            await query.message.reply_text("✅ تحقق ناجح +5 نقاط")
        else:
            await query.message.reply_text("❌ لسه مو مشترك")

    elif query.data == "buy":
        await query.message.reply_text(
            "🛒 شراء نقاط\n100 نقطة = 1$\nراسل الأدمن: @YQOMARN"
        )

    elif query.data == "withdraw":
        await query.message.reply_text(
            "🏧 اكتب عدد النقاط المراد سحبها"
        )
        context.user_data["withdraw"] = True

# ---------- WITHDRAW ----------
async def withdraw_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("withdraw"):
        return

    user_id = update.effective_user.id
    amount = int(update.message.text)

    cursor.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    points = cursor.fetchone()[0]

    if amount > points:
        await update.message.reply_text("❌ رصيدك غير كافي")
    else:
        await context.bot.send_message(
            ADMIN_ID,
            f"📥 طلب سحب\n👤 {user_id}\n💰 {amount} نقطة"
        )
        await update.message.reply_text("✅ تم إرسال طلبك")

    context.user_data["withdraw"] = False

# ---------- ADMIN ----------
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(
        "/add id points\n/remove id points\n/broadcast رسالة"
    )

async def add_points(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    uid, pts = map(int, context.args)
    cursor.execute("UPDATE users SET points = points + ? WHERE user_id=?", (pts, uid))
    db.commit()
    await update.message.reply_text("✅ تم الإضافة")

async def remove_points(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    uid, pts = map(int, context.args)
    cursor.execute("UPDATE users SET points = points - ? WHERE user_id=?", (pts, uid))
    db.commit()
    await update.message.reply_text("✅ تم الخصم")

async def broadcast(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = " ".join(context.args)
    cursor.execute("SELECT user_id FROM users")
    for u in cursor.fetchall():
        try:
            await context.bot.send_message(u[0], msg)
        except:
            pass
    await update.message.reply_text("📢 تم الإرسال")

# ---------- RUN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("add", add_points))
    app.add_handler(CommandHandler("remove", remove_points))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
