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
db = db["hospitals"]


def get(dId, date):
  params = {'district_id': dId, 'date': date}
  r = requests.get(url=URL, params=params, headers=HEADER)
  data = r.json()
  #print(data.get('centers')[1])
  return data

def update_db(dId, date) -> int:
  new_data = 0
  data = get(dId, date)
  data = data.get('centers')
  
  # iterate through centers
  for center in data:
    for sessions in center.get('sessions'):
      curr_center = {
        '_id': center.get('center_id'),
        'name': center.get('name'),
        'sessions': [],
      }

      # check if center exists in db
      exists = db.find_one({'_id': curr_center['_id']})
      if not exists:
        hospital = {'_id': curr_center['_id'], 'name': curr_center['name'], 'fourtyFive': [], 'eighteen': []}
        db.insert_one(hospital)
        new_data = 1

      db_center = db.find_one({'_id': curr_center['_id']})

      curr_center['sessions'].append(sessions)
      for session in curr_center['sessions']:
        session_slots = session.get('available_capacity')
        session_date = session.get('date')
        session_age = session.get('min_age_limit')

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
                  new_data = 1
                  db.update_one({'_id': curr_center['_id']}, {'$set': {'fourtyFive.'+str(ind)+'.'+str(session_date): session_slots}})
                exists = True

          if not exists:
            # if date doesn't exist, insert it
            print('inserting')
            new_data = 1
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

  return new_data


def check_for_updates(dId) -> int:
  no_of_updates = 0
  date = datetime.datetime.now()
  for i in range(6):
    no_of_updates += update_db(dId, date.strftime('%d-%m-%Y'))
    date += datetime.timedelta(weeks=1)

  return no_of_updates

check_for_updates(151)