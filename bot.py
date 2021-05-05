from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
import get_sched
import os
import dotenv
dotenv.load_dotenv()
import db_connect
import pymongo

client = db_connect.client
db = db_connect.db
coll = db['users']

temp_user = {'name': '', 'district': 0, 'age': 0}

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
  if query.data == '0' or query.data == '1':
    temp_user['_id'] = query.message.chat.id
    temp_user['district'] = query.data
    reply_markup = ask_age()
    query.answer()
    query.edit_message_text('Please select your age:', reply_markup=reply_markup)
  elif query.data == '45' or query.data == '18':
    temp_user['age'] = query.data
    reply_markup = ask_notify()
    query.answer()
    query.edit_message_text('Would you like to be notified of new slots ?', reply_markup=reply_markup)
  elif query.data == 'Yes' or query.data == 'No':
    if query.data == 'Yes':
      temp_user['notify'] = 1
    else:
      temp_user['notify'] = 0
    query.answer()
    query.edit_message_text('Thank you.')
    save_user_to_db()

def save_user_to_db() -> None:
  key = {'_id': temp_user['_id']}
  data = {'$set': {'district': temp_user['district'], 'age': temp_user['age'], 'notify': temp_user['notify']}}
  coll.update_one(key, data, upsert=True)
  client.close()

def ask_notify() -> InlineKeyboardMarkup:
  keyboard = [
    [
      InlineKeyboardButton("Yes", callback_data='Yes'),
      InlineKeyboardButton("No", callback_data='No')
    ]
  ]
  return InlineKeyboardMarkup(keyboard)

def update_db(context):
  get_sched.check_for_updates(temp_user['district'])
  print('updating')


def ask_age() -> InlineKeyboardMarkup:
  keyboard = [
    [
      InlineKeyboardButton("45+", callback_data='45'),
      InlineKeyboardButton("18+", callback_data='18')
    ]
  ]
  return InlineKeyboardMarkup(keyboard)

def main() -> None:
  updater = Updater(os.environ['BOT_API'])

  # job queue
  jq = updater.job_queue
  jq.run_repeating(update_db, 10)

  dispatcher = updater.dispatcher

  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("setup", setup))
  dispatcher.add_handler(CommandHandler("check", check))
  dispatcher.add_handler(CallbackQueryHandler(button_handler))

  updater.start_polling()
  updater.idle()

if __name__ == '__main__':
  main()