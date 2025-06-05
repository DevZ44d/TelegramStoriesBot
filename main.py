from pyrogram import Client, filters, types
from config import API_ID, API_HASH, BOT_TOKEN, SESSION_STRING
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import traceback
import re

bot = Client("bot",
             api_id=API_ID,
             api_hash=API_HASH,
             bot_token=BOT_TOKEN)

client = Client("bot2",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STRING)


user_languages = {}

async def send_main_menu(user, message_obj, lang="ar", edit=False):
    name = user.first_name
    username = user.username or "unknown"
    mention = f"[{name}](https://t.me/{username})" if username != "unknown" else name

    texts = {
        "en": f"""
• Hello ¦ {mention}
- I am a bot that can download stories from Telegram, including photos and videos, from any user or channel.

- Just send a story link or username to start downloading stories instantly.
        """,

        "ar": f"""
• مرحباً ¦ {mention}
- أنا بوت يستطيع تحميل القصص من تيليجرام، سواء صور أو فيديوهات، من أي مستخدم أو قناة.

- أرسل رابط قصة أو اسم المستخدم للبدء بتحميل القصص فوراً. 
        """
    }

    buttons = [
        [
            InlineKeyboardButton("كيفية استخدام البوت؟" if lang == "ar" else "How to use the bot?", callback_data="how_to_use"),
            InlineKeyboardButton("🇸🇦 العربية" if lang == "ar" else "🇺🇸 English", callback_data="toggle_lang")
        ],
        [
            InlineKeyboardButton("👨‍💻 المطور" if lang == "ar" else "👨‍💻 Developer", url="https://t.me/eeeYccc")
        ]
    ]

    markup = InlineKeyboardMarkup(buttons)
    text = texts[lang]

    if edit:
        await message_obj.edit_text(text, reply_markup=markup)
    else:
        await message_obj.reply(text, reply_markup=markup)

@bot.on_message(filters.private & filters.command("start"))
async def start_command(app: Client, message: types.Message):
    user_languages[message.from_user.id] = "ar"
    await send_main_menu(message.from_user, message)

@bot.on_callback_query()
async def handle_callback(bot: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data
    lang = user_languages.get(user_id, "ar")

    if data == "toggle_lang":
        lang = "en" if lang == "ar" else "ar"
        user_languages[user_id] = lang
        await send_main_menu(callback_query.from_user, callback_query.message, lang=lang, edit=True)

    elif data == "how_to_use":
        usage_text = {
            "ar": "**📘 كيفية استخدام البوت:**\n\n"
                  "💠 ┇ أرسل رابط ستوري أو يوزر.\n"
                  "🏷 ┇ سيتم تحميل الستوري إذا كان متاحاً.\n\n",

            "en": "**📘 How to use the bot:**\n\n"
                  "💠 ┇ Send a story link or username.\n"
                  "🏷 ┇ The bot will download the story if available.\n\n"
        }
        await callback_query.message.edit_text(
            usage_text[lang],
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع" if lang == "ar" else "🔙 Back", callback_data="back_to_menu")]
            ])
        )

    elif data == "back_to_menu":
        await send_main_menu(callback_query.from_user, callback_query.message, lang=lang, edit=True)

    await callback_query.answer()

async def storlink(app: Client, message: types.Message, username, story_id):
    try:
        loading_msg = await message.reply("⏳")
        async with client:
            stories = await client.get_stories(chat_id=username, story_ids=[story_id])
            if not stories:
                return await loading_msg.edit_text("❌ لم يتم العثور على الستوري.")

            for story in stories:
                file = await story.download(in_memory=True)
                caption_text = story.caption or "لا يوجد وصف."
                caption = (
                    f"📖 من: @{username}\n"
                    f"⏰ التاريخ: {story.date}\n"
                    f" :ايدي 🆔{story.id}\n"
                    f"📝 الوصف: {caption_text}\n"
                )
                await bot.send_document(chat_id=message.chat.id, document=file, caption=caption)

            await loading_msg.delete()

    except Exception:
        traceback.print_exc()
        await message.reply("❌ حصل خطأ أثناء تحميل الستوري.")

async def stor(app: Client, message: types.Message, username):
    try:
        async with client:
            async for story in client.get_chat_stories(username):
                file = await story.download(in_memory=True)
                caption_text = story.caption or "لا يوجد وصف."
                caption = (
                    f"📖 من: @{username}\n"
                    f"⏰ التاريخ: {story.date}\n"
                    f" :ايدي 🆔{story.id}\n"
                    f"📝 الوصف: {caption_text}\n"
                )
                await bot.send_document(chat_id=message.chat.id, document=file, caption=caption)

    except Exception:
        traceback.print_exc()
        await message.reply("❌ حدث خطأ أثناء تحميل القصص.")

@bot.on_message(filters.private & filters.text)
async def handle_text(app: Client, message: types.Message):
    text = message.text.strip()


    if text.startswith('@'):
        await stor(app, message, text[1:])
        return  # stop here


    match = re.match(r"(https?://)?(www\.)?(t\.me|telegram\.me)/(?P<username>[a-zA-Z0-9_]+)/s/(?P<story_id>\d+)", text, re.IGNORECASE)
    if match:
        username = match.group("username")
        story_id = int(match.group("story_id"))
        await storlink(app, message, username, story_id)
    else:
        await message.reply("❌ يرجى إرسال يوزر مثل @username أو رابط ستوري صحيح.")

if __name__ == "__main__":
    bot.run()
