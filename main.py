from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from twilio.rest import Client
import logging
from datetime import datetime

BOT_TOKEN = "7900914546:AAG3GfU8ju_ZLLIZvH45HgcUYAC4my_BrTY"
user_data = {}

REQUIRED_CHANNELS = [
    {"chat_id": "-1002666988893", "url": "https://t.me/+nIVhh9hJWs4wMjBl", "name": "🔗 Private Channel 1"},
    {"chat_id": "-1002271770904", "url": "https://t.me/World_Of_Method_Chat", "name": "🔗 Private Channel 2"},
    {"chat_id": "-1002737588796", "url": "https://t.me/World_of_Method", "name": "🔗 BackUp Channel"},
    {"chat_id": "-1002269602874", "url": "https://t.me/world_method_Twillo", "name": "🔗 Twilio Method Channel"},
]

main_menu_buttons_logged_out = [[KeyboardButton("🔑 Login")]]
main_menu_buttons_logged_in = [
    [KeyboardButton("📞 Buy Number"), KeyboardButton("🎲 Mix")],
    [KeyboardButton("🚪 Logout")]
]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FORWARD_GROUP_ID = -1002269602874

def is_private_chat(update: Update) -> bool:
    return update.effective_chat.type == "private"

async def check_user_membership(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> bool:
    user_id = update.effective_user.id
    not_joined = []

    for channel in REQUIRED_CHANNELS:
        chat_id = channel["chat_id"]
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel)
        except:
            not_joined.append(channel)

    if not_joined:
        buttons = [[InlineKeyboardButton(text=ch["name"], url=ch["url"])] for ch in not_joined]
        buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(buttons)

        if from_callback and update.callback_query:
            try:
                await update.callback_query.edit_message_text(
                    "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি। বট ব্যবহার করতে হলে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে ⛔",
                    reply_markup=reply_markup
                )
            except:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি। নিচের চ্যানেলগুলোতে জয়েন করুন ⬇️",
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                "⚠️ বট ব্যবহার করতে হলে নিচের চ্যানেলগুলোতে জয়েন করুন 👇",
                reply_markup=reply_markup
            )
        return False
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private_chat(update):
        return
    if not await check_user_membership(update, context):
        return
    user_id = update.effective_user.id
    reply_markup = ReplyKeyboardMarkup(main_menu_buttons_logged_in if user_id in user_data else main_menu_buttons_logged_out, resize_keyboard=True)
    await update.message.reply_text("👋 স্বাগতম! নিচের অপশনগুলো থেকে একটি বেছে নিন:", reply_markup=reply_markup)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private_chat(update):
        return
    if not await check_user_membership(update, context):
        return

    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "🔑 Login":
        await update.message.reply_text("🛡 SID TOKEN মাঝখানে স্পেস দিয়ে পাঠান:\n📌 উদাহরণ:\nACSIDxxxxxxxxxxxx 1234567890abcdef")

    elif text == "🚪 Logout":
        user_data.pop(user_id, None)
        await update.message.reply_text("✅ আপনি লগআউট হয়েছেন।", reply_markup=ReplyKeyboardMarkup(main_menu_buttons_logged_out, resize_keyboard=True))

    elif text == "📞 Buy Number":
        if user_id not in user_data:
            await update.message.reply_text("⚠️ অনুগ্রহ করে প্রথমে লগইন করুন।")
        else:
            await update.message.reply_text("🌐 একটি এরিয়া কোড লিখুন (যেমন: 437, 647, 213):")

    elif text == "🎲 Mix":
        await send_random_numbers(update, context)

    elif user_id in user_data and text.isdigit():
        await show_available_numbers(update, context, text)

    elif user_id in user_data:
        number_input = text.strip().replace(" ", "")
        if number_input.isdigit():
            number_input = "+" + number_input
        elif not number_input.startswith("+"):
            number_input = "+" + number_input
        user_data[user_id]["pending_number"] = number_input
        button = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm Buy", callback_data="buy_confirm")]])
        await update.message.reply_text(f"📲 বেছে নেয়া নাম্বার: {number_input}\n⏳ নিশ্চিত করতে নিচে চাপুন:", reply_markup=button)

    else:
        parts = [p.strip() for p in text.replace('\n', ' ').replace('|', ' ').replace(':', ' ').split() if p.strip()]
        if len(parts) == 2 and parts[0].startswith("AC"):
            sid, token = parts[0], parts[1]
            try:
                client = Client(sid, token)
                client.api.accounts(sid).fetch()
                user_data[user_id] = {"sid": sid, "token": token, "number": None}
                await update.message.reply_text("✅ লগইন সফল হয়েছে।", reply_markup=ReplyKeyboardMarkup(main_menu_buttons_logged_in, resize_keyboard=True))
            except Exception as e:
                await update.message.reply_text(f"❌ লগইন ব্যর্থ: {str(e)}")
        else:
            await update.message.reply_text("⚠️ সঠিক ইনপুট দিন অথবা অপশন বেছে নিন।")

async def show_available_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE, area_code: str):
    user_id = update.effective_user.id
    creds = user_data[user_id]
    client = Client(creds["sid"], creds["token"])

    try:
        numbers = client.available_phone_numbers("US").local.list(area_code=area_code, sms_enabled=True, limit=30)
        country = "US"
        if not numbers:
            numbers = client.available_phone_numbers("CA").local.list(area_code=area_code, sms_enabled=True, limit=30)
            country = "CA"

        if not numbers:
            await update.message.reply_text(f"❌ {area_code} এর জন্য কোনো নম্বর পাওয়া যায়নি।")
            return

        await update.message.reply_text(f"📍 {country} ({area_code}) এর জন্য পাওয়া নম্বরগুলো:")
        for num in numbers:
            await update.message.reply_text(num.phone_number)
    except Exception as e:
        await update.message.reply_text(f"❌ এরিয়া কোডে ত্রুটি: {str(e)}")

async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_data or "pending_number" not in user_data[user_id]:
        await query.edit_message_text("⚠️ কোনো নম্বর পেন্ডিং অবস্থায় নেই।")
        return

    number_to_buy = user_data[user_id]["pending_number"]
    creds = user_data[user_id]
    client = Client(creds["sid"], creds["token"])

    try:
        if creds.get("number"):
            incoming_numbers = client.incoming_phone_numbers.list()
            for number in incoming_numbers:
                if number.phone_number == creds.get("number"):
                    number.delete()
                    break

        bought = client.incoming_phone_numbers.create(phone_number=number_to_buy)
        user_data[user_id]["number"] = bought.phone_number

        button = InlineKeyboardMarkup([[InlineKeyboardButton("👁 View SMS", callback_data="view_sms")]])
        await query.edit_message_text(f"✅ নাম্বার কেনা হয়েছে: {bought.phone_number}", reply_markup=button)

    except Exception as e:
        await query.edit_message_text(f"❌ নম্বর কেনা যায়নি: {str(e)}")

async def view_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    creds = user_data.get(user_id)
    button = InlineKeyboardMarkup([[InlineKeyboardButton("👁 View SMS", callback_data="view_sms")]])

    if not creds or not creds.get("number"):
        await query.edit_message_text("⚠️ কোনো নাম্বার সেট করা নেই।", reply_markup=button)
        return

    try:
        client = Client(creds["sid"], creds["token"])
        messages = client.messages.list(to=creds["number"], limit=5)

        if not messages:
            await query.edit_message_text("📭 ওটিপি পাওয়া যায়নি।", reply_markup=button)
            return

        for msg in messages:
            full_message_line = msg.body.strip()
            otp = ''.join(filter(str.isdigit, full_message_line))[:6]
            timestamp = msg.date_sent.strftime('%Y-%m-%d %H:%M:%S')
            number_masked = creds['number']
            app_type = "twilio"
            country_flag = "🇨🇦" if "+1" in number_masked else "🌍"

            text = (
                f"🕰️ *Time:* `{timestamp}`\n"
                f"📞 *Number:* `{number_masked}`\n"
                f"🌍 *Country:* {country_flag}\n"
                f"🔑 *Your Main OTP:* `{otp}`\n"
                f"🍏 *Service:* `{app_type}`\n"
                f"📬 *Full Message:*\n"
                f"```text\n{full_message_line}\n```\n"
                f"👑 *Powered by:* [Robiul](@Robiul_TNE_R)"
            )

            await query.edit_message_text(text, reply_markup=button, parse_mode="Markdown")
            await context.bot.send_message(chat_id=FORWARD_GROUP_ID, text=text, parse_mode="Markdown")

    except Exception as e:
        await query.edit_message_text(f"❌ বার্তা আনতে সমস্যা: {str(e)}", reply_markup=button)

async def send_random_numbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_private_chat(update):
        return

    area_codes = ["647", "604", "403", "416", "587"]
    display = "🎲 Random area code numbers:\n"
    for code in area_codes:
        display += f"📍 Area {code}:\n"
        if code == "647":
            display += "+16474567890\n+16479876543\n"
        elif code == "587":
            display += "+15876543210\n+15879871234\n"
    display += "\n📝 একটি নম্বর কপি করে পাঠান কিনতে।"
    await update.message.reply_text(display)

async def handle_check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    not_joined = []
    for channel in REQUIRED_CHANNELS:
        chat_id = channel["chat_id"]
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                not_joined.append(channel)
        except:
            not_joined.append(channel)

    if not_joined:
        buttons = [[InlineKeyboardButton(text=ch["name"], url=ch["url"])] for ch in not_joined]
        buttons.append([InlineKeyboardButton("✅ চেক করুন", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(buttons)

        try:
            await query.edit_message_text(
                "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি। বট ব্যবহার করতে হলে অবশ্যই নিচের চ্যানেলগুলোতে জয়েন করতে হবে ⛔",
                reply_markup=reply_markup
            )
        except:
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text="❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি। নিচের চ্যানেলগুলোতে জয়েন করুন ⬇️",
                reply_markup=reply_markup
            )
    else:
        reply_markup = ReplyKeyboardMarkup(
            main_menu_buttons_logged_in if user_id in user_data else main_menu_buttons_logged_out,
            resize_keyboard=True
        )
        await query.edit_message_text("✅ আপনি সফলভাবে সবগুলো চ্যানেলে জয়েন করেছেন!\n👇 এখন নিচের অপশন থেকে একটি বেছে নিন:")
        await context.bot.send_message(chat_id=query.message.chat.id, text="👇 নিচের মেনু থেকে একটি বেছে নিন:", reply_markup=reply_markup)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(buy_confirm, pattern="^buy_confirm$"))
    app.add_handler(CallbackQueryHandler(view_sms, pattern="^view_sms$"))
    app.add_handler(CallbackQueryHandler(handle_check_membership, pattern="^check_membership$"))
    app.run_polling()

if __name__ == '__main__':
    main()
