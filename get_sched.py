from pymongo.message import update
import requests
import pymongo
import datetime
import os
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()

#client = pymongo.MongoClient(f"mongodb+srv://fullStackOpen:{os.environ['DB_PASS']}@cluster0.utvrz.mongodb.net/cowin?retryWrites=true&w=majority")
client = pymongo.MongoClient("mongodb://localhost:27017")

URL = 'https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict'
HEADER = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}
db = client['cowin']
db = db['hospitals']


def get(dId, date) -> dict:
  params = {'district_id': dId, 'date': date}
  r = requests.get(url=URL, params=params, headers=HEADER)
  return r.json()

def update_db(dId, date) -> int:
  centers = {'fourtyFive': [], 'eighteen': []}
  data = get(dId, date).get('centers')
  
  # iterate through centers
  for center in data:
    curr_center = {
        '_id': center.get('center_id'),
        'name': center.get('name'),
    }

    db.update_one(
        {'_id': curr_center['_id']},
        {'$setOnInsert': {
          '_id': curr_center['_id'],
          'name': curr_center['name'],
          'fourtyFive': {},
          'eighteen': {}
        }},
        upsert=True
    )
    
    for sessions in center.get('sessions'):
      session_slots = sessions.get('available_capacity')
      session_date = sessions.get('date')
      session_age = sessions.get('min_age_limit')
      if session_age == 45:
        db_key = 'fourtyFive'
      elif session_age == 18:
        db_key = 'eighteen'

      # cross-check session date with local db
      db_record = db.find_one(
        {'_id': curr_center['_id'],
        db_key+'.'+str(session_date): {'$exists': True}}
      )

      if db_record is not None:
        db_slots = db_record[db_key][str(session_date)]
        if db_slots != session_slots:
          if db_slots < session_slots:
            centers[db_key].append({'name': curr_center.get('name'), 'slots': session_slots})
          db.update_one(
            {'_id': curr_center['_id']},
            {'$set': {db_key+'.'+str(session_date): session_slots}}
          )
      else:
        db.update_one(
            {'_id': curr_center['_id']},
            {'$set': {db_key+'.'+str(session_date): session_slots}}
        )

  return centers


def check_for_updates(dId) -> int:
  centers = []
  date = datetime.datetime.now()
  for i in range(4):
    updates = update_db(dId, date.strftime('%d-%m-%Y'))
    if updates:
      centers.append(updates)
    date += datetime.timedelta(weeks=1)

  return centers