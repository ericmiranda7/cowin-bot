from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
#import get_sched
import os
import dotenv
dotenv.load_dotenv()

district = 0

def start(update: Update, _: CallbackContext) -> None:
  update.message.reply_text('Welcome !\nPlease give me some details with /setup')

def setup(update: Update, _: CallbackContext) -> None:
  keyboard = [
    [
      InlineKeyboardButton("North Goa", callback_data='0'),
      InlineKeyboardButton("South GOa", callback_data='1')
    ]
  ]

  reply_markup = InlineKeyboardMarkup(keyboard)

  update.message.reply_text(text='Please choose:', reply_markup=reply_markup)

def check(update: Update, _: CallbackContext) -> None:
  #centers = get_sched.get_formatted()
  update.message.reply_text(text=centers)


def button_handler(update: Update, _: CallbackContext) -> None:
  query = update.callback_query

  if query == '0' or query == '1':
    district = query

  query.answer()
  query.edit_message_text('Thank you.')

def main() -> None:
  updater = Updater(os.environ['BOT_API'])
  dispatcher = updater.dispatcher

  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("setup", setup))
  dispatcher.add_handler(CommandHandler("check", check))
  dispatcher.add_handler(CallbackQueryHandler(button_handler))

  updater.start_polling()
  updater.idle()

if __name__ == '__main__':
  main()