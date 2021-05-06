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
  districts = []
  data = get(dId, date).get('centers')
  
  # iterate through centers
  for center in data:
    for sessions in center.get('sessions'):
      curr_center = {
        '_id': center.get('center_id'),
        'name': center.get('name'),
      }

      db.update_one(
        {'_id': curr_center['_id']},
        {'$set': {
          '_id': curr_center['_id'],
          'name': curr_center['name'],
        },
        '$setOnInsert': {
          'fourtyFive': [],
          'eighteen': []
        }},
        upsert=True
      )

      db_center = db.find_one({'_id': curr_center['_id']})

      session_slots = sessions.get('available_capacity')
      session_date = sessions.get('date')
      print(session_date)
      session_age = sessions.get('min_age_limit')
      if session_age == 45:
        # cross-check session date with local db
        db_record = db_center['fourtyFive']
        exists = False
        for ind, rec in enumerate(db_record):
          for key_date, slots in rec.items():
            if key_date == session_date:
              if slots != session_slots:
                # update local db
                print('updating ', slots, session_slots)
                db.update_one({'_id': curr_center['_id']}, {'$set': {'fourtyFive.'+str(ind)+'.'+str(session_date): session_slots}})
                if session_slots > slots:
                  print('slot added')
                  if center.get('district_name') not in districts:
                    districts.append(center.get('district_name'))
              exists = True
        if not exists:
          # if date doesn't exist, insert it
          print('inserting')
          db.update_one({'_id': curr_center['_id']}, {'$push': {'fourtyFive': {session_date: session_slots}}})
      
      if session_age == 18:
        # cross-check session date with local db
        db_record = db_center['eighteen']
        exists = False
        for ind, rec in enumerate(db_record):
          for key_date, slots in rec.items():
            if key_date == session_date:
              if slots != session_slots:
                # update local db
                print('updating')
                new_data = 1
                db.update_one({'__id': curr_center['_id']}, {'$set': {'eighteen.'+str(ind)+'.'+str(session_date): session_slots}})
              exists = True
        if not exists:
          # if date doesn't exist, insert it
          new_data = 1
          db.update_one({'_id': curr_center['_id']}, {'$push': {'eighteen': {session_date: session_slots}}})    

  return districts


def check_for_updates(dId) -> int:
  districts = []
  date = datetime.datetime.now()
  for i in range(4):
    updates = update_db(dId, date.strftime('%d-%m-%Y'))
    if updates:
      districts.append(updates)
    date += datetime.timedelta(weeks=1)

  return districts

check_for_updates(151)