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
db = client['cowin']
db = db["hospitals"]


def get(dId, date):
  params = {'district_id': dId, 'date': date}
  r = requests.get(url=URL, params=params)
  data = r.json()
  #print(data.get('centers')[1])
  return data

def update_db(dId, date, age):
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
      db_center = db.find_one({'_id': curr_center['_id']})


      curr_center['sessions'].append(sessions)
      for session in curr_center['sessions']:
        if session.get('min_age_limit') != age:
          continue
        session_slots = session.get('available_capacity')
        session_date = session.get('date')

        # check if center exists in db
        exists = db.find_one({'_id': curr_center['_id']})
        if not exists:
          hospital = {'_id': curr_center['_id'], 'name': curr_center['name'], 'fourtyFive': [], 'eighteen': []}
          db.insert_one(hospital)

        # cross-check session date with local db
        api_record = {session_date: session_slots}
        db_record = db_center['fourtyFive']

        exists = False
        for ind, rec in enumerate(db_record):
          for key_date, slots in rec.items():
            if key_date == session_date:
              if slots != session_slots:
                # update local db
                print('updating')
                db.update_one({'__id': curr_center['_id']}, {'$set': {'fourtyFive.'+str(ind)+'.'+str(date): session_slots}})
              exists = True
        
        if not exists:
          # if date doesn't exist, insert it
          db.update_one({'_id': curr_center['_id']}, {'$push': {'fourtyFive': {session_date: session_slots}}})
        

def check_for_updates(dId, age):
  date = datetime.datetime.now()
  for i in range(6):
    update_db(dId, date.strftime('%d-%m-%Y'), age)
    date += datetime.timedelta(weeks=1) 

check_for_updates(151, 45)