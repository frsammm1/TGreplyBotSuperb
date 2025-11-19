import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode
import os, random, json
from aiohttp import web
import asyncio

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))
PORT = int(os.environ.get('PORT', '10000'))

message_map = {}
USER_DB_FILE = 'users.json'
broadcast_mode = {}

GREETINGS = [
    "✨ Got it! Sam will reply soon!",
    "📬 Message delivered! Hang tight!",
    "🎯 Your message is on its way to Sam!",
    "⚡ Sent! Sam will get back to you shortly!",
    "🌟 Message received! Sam will respond soon!",
    "💫 Delivered successfully! Stay tuned!",
    "🚀 Your message just landed! Sam will reply!",
    "🎨 Message sent! Sam's on it!",
    "🔔 Ding! Sam will see this soon!",
    "💌 Got your message! Sam will reply ASAP!",
    "🎉 Perfect! Your message reached Sam!",
    "✅ All set! Sam will be in touch!",
    "📨 Message received loud and clear!",
    "👍 Done! Sam will respond shortly!",
    "🌈 Great! Your message is with Sam now!",
    "💬 Awesome! Sam will check this soon!",
    "🎵 Nice! Sam will get back to you!",
    "⭐ Sweet! Your message is delivered!",
    "🔥 Cool! Sam will reply soon!",
    "💙 Thanks! Sam will respond ASAP!"
]

def load_users():
    try:
        if os.path.exists(USER_DB_FILE):
            with open(USER_DB_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_users(users):
    try:
        with open(USER_DB_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

users_db = load_users()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = update.effective_user
    
    if str(user_id) not in users_db and user_id != OWNER_ID:
        users_db[str(user_id)] = {
            'id': user_id,
            'name': user.full_name,
            'username': user.username,
            'first_seen': str(update.message.date),
            'status': 'active'
        }
        save_users(users_db)
        logger.info(f"New user: {user.full_name}")
    elif str(user_id) in users_db:
        users_db[str(user_id)]['status'] = 'active'
        users_db[str(user_id)]['name'] = user.full_name
        save_users(users_db)
    
    if user_id == OWNER_ID:
        total = len(users_db)
        active = sum(1 for u in users_db.values() if u.get('status') == 'active')
        blocked = sum(1 for u in users_db.values() if u.get('status') == 'blocked')
        await update.message.reply_text(
            f"👋 Welcome Sam!\n\n👥 Users: {total} | ✅ Active: {active} | 🚫 Blocked: {blocked}\n\n"
            f"📝 Commands:\n/broadcast - Start broadcast\n/users - All users\n/active - Active users\n"
            f"/blocked - Blocked users\n/stats - Statistics\n\nReply to messages to respond."
        )
    else:
        await update.message.reply_text("👋 Hi! Please send a message to Sam, he'll reply soon.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("⛔ Owner only.")
        return
    broadcast_mode[user_id] = True
    await update.message.reply_text("📢 Broadcast Mode ON! Send any message. /cancel to exit.")

async def cancel_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in broadcast_mode:
        del broadcast_mode[update.effective_user.id]
        await update.message.reply_text("❌ Broadcast cancelled.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if not users_db:
        await update.message.reply_text("📭 No users!")
        return
    msg = "👥 All Users:\n\n"
    for u in users_db.values():
        emoji = "✅" if u.get('status') == 'active' else "🚫"
        link = f'<a href="tg://user?id={u["id"]}">{u["name"]}</a>'
        msg += f"{emoji} {link} (ID: {u['id']})\n"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def list_active_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    active = {k: v for k, v in users_db.items() if v.get('status') == 'active'}
    if not active:
        await update.message.reply_text("📭 No active users!")
        return
    msg = "✅ Active Users:\n\n"
    for u in active.values():
        link = f'<a href="tg://user?id={u["id"]}">{u["name"]}</a>'
        msg += f"• {link} (ID: {u['id']})\n"
    msg += f"\n📊 Total: {len(active)}"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def list_blocked_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    blocked = {k: v for k, v in users_db.items() if v.get('status') == 'blocked'}
    if not blocked:
        await update.message.reply_text("✅ No blocked users!")
        return
    msg = "🚫 Blocked Users:\n\n"
    for u in blocked.values():
        link = f'<a href="tg://user?id={u["id"]}">{u["name"]}</a>'
        msg += f"• {link} (ID: {u['id']})\n"
    msg += f"\n📊 Total: {len(blocked)}"
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    total = len(users_db)
    active = sum(1 for u in users_db.values() if u.get('status') == 'active')
    blocked = sum(1 for u in users_db.values() if u.get('status') == 'blocked')
    await update.message.reply_text(
        f"📊 Statistics\n\n👥 Total: {total}\n✅ Active: {active}\n🚫 Blocked: {blocked}\n💬 Conversations: {len(message_map)}"
    )

async def handle_broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    success = fail = blocked = 0
    status_msg = await message.reply_text("📡 Broadcasting...")
    
    for uid_str, user in users_db.items():
        if user.get('status') != 'active':
            continue
        try:
            tid = int(uid_str)
            if message.text:
                await context.bot.send_message(tid, f"📢 Message from Sam:\n\n{message.text}")
            elif message.photo:
                await context.bot.send_photo(tid, message.photo[-1].file_id, caption=f"📢 Message from Sam:\n\n{message.caption or ''}")
            elif message.video:
                await context.bot.send_video(tid, message.video.file_id, caption=f"📢 Message from Sam:\n\n{message.caption or ''}")
            elif message.document:
                await context.bot.send_document(tid, message.document.file_id, caption=f"📢 Message from Sam:\n\n{message.caption or ''}")
            elif message.audio:
                await context.bot.send_audio(tid, message.audio.file_id, caption=f"📢 Message from Sam:\n\n{message.caption or ''}")
            elif message.voice:
                await context.bot.send_voice(tid, message.voice.file_id)
            elif message.video_note:
                await context.bot.send_video_note(tid, message.video_note.file_id)
            elif message.sticker:
                await context.bot.send_sticker(tid, message.sticker.file_id)
            elif message.animation:
                await context.bot.send_animation(tid, message.animation.file_id, caption=f"📢 Message from Sam:\n\n{message.caption or ''}")
            success += 1
        except Exception as e:
            err = str(e).lower()
            if 'blocked' in err or 'deactivated' in err or 'not found' in err:
                users_db[uid_str]['status'] = 'blocked'
                blocked += 1
            else:
                fail += 1
    
    save_users(users_db)
    await status_msg.edit_text(f"✅ Broadcast Done!\n\n✓ Sent: {success}\n🚫 Blocked: {blocked}\n✗ Failed: {fail}\n\nSend another or /cancel")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.message
    
    if user_id == OWNER_ID:
        if broadcast_mode.get(user_id):
            await handle_broadcast_message(update, context)
            return
        
        if message.reply_to_message:
            replied_id = message.reply_to_message.message_id
            if replied_id in message_map:
                target = message_map[replied_id]
                try:
                    if message.text:
                        await context.bot.send_message(target, message.text)
                    elif message.photo:
                        await context.bot.send_photo(target, message.photo[-1].file_id, caption=message.caption)
                    elif message.video:
                        await context.bot.send_video(target, message.video.file_id, caption=message.caption)
                    elif message.document:
                        await context.bot.send_document(target, message.document.file_id, caption=message.caption)
                    elif message.voice:
                        await context.bot.send_voice(target, message.voice.file_id)
                    elif message.audio:
                        await context.bot.send_audio(target, message.audio.file_id, caption=message.caption)
                    await message.reply_text("✅ Sent!")
                except Exception as e:
                    await message.reply_text(f"❌ Failed: {e}")
            else:
                await message.reply_text("⚠️ Reply to a forwarded message.")
    else:
        user = update.effective_user
        username = f"@{user.username}" if user.username else "No username"
        full_name = user.full_name or "Unknown"
        
        if str(user_id) not in users_db:
            users_db[str(user_id)] = {
                'id': user_id,
                'name': full_name,
                'username': user.username,
                'first_seen': str(message.date),
                'status': 'active'
            }
            save_users(users_db)
        
        link = f'<a href="tg://user?id={user_id}">{full_name}</a>'
        header = f"📨 New message:\n👤 {link}\n🆔 {user_id}\n📱 {username}\n{'─'*30}\n"
        
        try:
            if message.text:
                sent = await context.bot.send_message(OWNER_ID, f"{header}{message.text}", parse_mode=ParseMode.HTML)
            elif message.photo:
                await context.bot.send_message(OWNER_ID, header, parse_mode=ParseMode.HTML)
                sent = await context.bot.send_photo(OWNER_ID, message.photo[-1].file_id, caption=message.caption or '')
            elif message.video:
                await context.bot.send_message(OWNER_ID, header, parse_mode=ParseMode.HTML)
                sent = await context.bot.send_video(OWNER_ID, message.video.file_id, caption=message.caption or '')
            elif message.document:
                await context.bot.send_message(OWNER_ID, header, parse_mode=ParseMode.HTML)
                sent = await context.bot.send_document(OWNER_ID, message.document.file_id, caption=message.caption or '')
            elif message.voice:
                await context.bot.send_message(OWNER_ID, header, parse_mode=ParseMode.HTML)
                sent = await context.bot.send_voice(OWNER_ID, message.voice.file_id)
            elif message.audio:
                await context.bot.send_message(OWNER_ID, header, parse_mode=ParseMode.HTML)
                sent = await context.bot.send_audio(OWNER_ID, message.audio.file_id, caption=message.caption or '')
            elif message.sticker:
                await context.bot.send_message(OWNER_ID, f"{header}[Sticker]", parse_mode=ParseMode.HTML)
                sent = await context.bot.send_sticker(OWNER_ID, message.sticker.file_id)
            else:
                sent = await context.bot.send_message(OWNER_ID, f"{header}[Unsupported type]", parse_mode=ParseMode.HTML)
            
            message_map[sent.message_id] = user_id
            await message.reply_text(random.choice(GREETINGS))
        except Exception as e:
            logger.error(f"Error: {e}")
            await message.reply_text("❌ Error sending message. Try again.")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")

async def health_check(request):
    return web.Response(text="Bot running! ✅")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    logger.info(f"🌐 Web server on port {PORT}")

async def main():
    if not BOT_TOKEN or not OWNER_ID:
        logger.error("Set BOT_TOKEN and OWNER_ID!")
        return
    
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("cancel", cancel_broadcast))
    app.add_handler(CommandHandler("users", list_users))
    app.add_handler(CommandHandler("active", list_active_users))
    app.add_handler(CommandHandler("blocked", list_blocked_users))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    await start_web_server()
    logger.info("🤖 Bot started!")
    logger.info(f"👥 {len(users_db)} users loaded")
    
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
