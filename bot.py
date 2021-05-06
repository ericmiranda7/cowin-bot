from pymongo.message import query
from telegram import Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
from telegram.ext.callbackqueryhandler import CallbackQueryHandler
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
import get_sched
import os
import dotenv
dotenv.load_dotenv()
import db_connect
import copy

client = db_connect.client
db = db_connect.db
coll_users = db['users']
coll_states = db['states']

def start(update: Update, _: CallbackContext) -> None:
  update.message.reply_text('Welcome !\nPlease give me some details with /setup')

def setup(update: Update, _: CallbackContext) -> None:
  temp_user = {}
  temp_user['_id'] = update.message.chat.id
  coll_users.update_one({'_id': temp_user['_id']}, {'$set': {'_id': temp_user['_id']}}, upsert=True)
  states_list = coll_states.find({})

  # show states inline
  keyboard = []
  keyboard_row = []
  for indx, state in enumerate(states_list):
    state_id = state['_id']
    keyboard_row.append(
      InlineKeyboardButton(state['state_name'], callback_data=f's{state_id}')
    )
    if indx == 0:
      continue
    if (indx+1) % 3 == 0:
      keyboard.append(copy.deepcopy(keyboard_row))
      keyboard_row.clear()
    if indx == 36:
      keyboard.append(copy.deepcopy(keyboard_row))
      keyboard_row.clear()

  reply_markup = InlineKeyboardMarkup(keyboard)
  update.message.reply_text(text='Please choose a state:', reply_markup=reply_markup)

def get_state(update: Update, _: CallbackContext) -> int:
  temp_user = {}
  temp_user['_id'] = update.callback_query.from_user.id
  query = update.callback_query
  state_id = update.callback_query.data[1:]
  temp_user['state'] = int(state_id)
  coll_users.update_one({'_id': temp_user['_id']}, {'$set': {'state': int(state_id)}}, upsert=True)
  state = coll_states.find_one({'_id': int(state_id)})
  keyboard = []
  keyboard_row = []
  districts_list = state['districts']
  for indx, district in enumerate(districts_list):
    district_id = district['district_id']
    keyboard_row.append(
      InlineKeyboardButton(district['district_name'], callback_data=f'd{district_id}')
    )
    if indx == 0:
      continue
    if (indx+1) % 2 == 0:
      keyboard.append(copy.deepcopy(keyboard_row))
      keyboard_row.clear()
  
  reply_markup = InlineKeyboardMarkup(keyboard)
  query.answer()
  query.edit_message_text('Please choose a district:', reply_markup=reply_markup)

def get_district(update: Update, _: CallbackContext):
  temp_user = {}
  temp_user['_id'] = update.callback_query.from_user.id
  query = update.callback_query
  district_id = update.callback_query.data[1:]
  temp_user['district'] = int(district_id)
  coll_users.update_one({'_id': temp_user['_id']}, {'$set': {'district': int(district_id)}}, upsert=True)

  reply_markup = ask_age()
  query.answer()
  query.edit_message_text('What is your age ?', reply_markup=reply_markup)

def get_age(update: Update, _: CallbackContext):
  query = update.callback_query
  age = update.callback_query.data[1:]
  coll_users.update_one({'_id': update.callback_query.from_user.id}, {'$set': {'age': int(age)}}, upsert=True)

  reply_markup = ask_notify()
  query.answer()
  query.edit_message_text('Would you like to be notified ?', reply_markup=reply_markup)

def get_notify(update: Update, _: CallbackContext):
  query = update.callback_query
  coll_users.update_one(
    {'_id': query.from_user.id},
    {'$set': {'notify': int(query.data[1:])}}
  )
  query.answer()
  query.edit_message_text('Thank you.')

def check(update: Update, _: CallbackContext) -> None:
  #centers = get_sched.get_formatted()
  update.message.reply_text(text=centers)

def ask_notify() -> InlineKeyboardMarkup:
  keyboard = [
    [
      InlineKeyboardButton("Yes", callback_data='n1'),
      InlineKeyboardButton("No", callback_data='n0')
    ]
  ]
  return InlineKeyboardMarkup(keyboard)

def update_db(context: CallbackContext):
  check_update = get_sched.check_for_updates(151)
  print(check_update)
  if check_update:
    users = coll_users.find({})
    for doc in users:
      if doc['notify']:
        print('notify the user here')
        context.bot.send_message(chat_id=doc['_id'], text=f'{check_update}: slot was added')


  #update_user = get_sched.check_for_updates(151)
  print('db ran')
  

def ask_age() -> InlineKeyboardMarkup:
  keyboard = [
    [
      InlineKeyboardButton("45+", callback_data='a45'),
      InlineKeyboardButton("18+", callback_data='a18')
    ]
  ]
  return InlineKeyboardMarkup(keyboard)

def main() -> None:
  updater = Updater(os.environ['BOT_API'])

  # job queue
  jq = updater.job_queue
  jq.run_repeating(update_db, 30)

  dispatcher = updater.dispatcher

  dispatcher.add_handler(CommandHandler("start", start))
  dispatcher.add_handler(CommandHandler("check", check))
  dispatcher.add_handler(CommandHandler("setup", setup))
  dispatcher.add_handler(CallbackQueryHandler(get_state, pattern='^s'))
  dispatcher.add_handler(CallbackQueryHandler(get_district, pattern='^d'))
  dispatcher.add_handler(CallbackQueryHandler(get_age, pattern='^a'))
  dispatcher.add_handler(CallbackQueryHandler(get_notify, pattern='^n'))

  updater.start_polling()
  updater.idle()

if __name__ == '__main__':
  main()