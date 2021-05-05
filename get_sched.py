from pymongo.message import update
import requests
import pymongo
import datetime
import os
from bson.objectid import ObjectId
from dotenv import load_dotenv
load_dotenv()

client = pymongo.MongoClient(f"mongodb+srv://fullStackOpen:{os.environ['DB_PASS']}@cluster0.utvrz.mongodb.net/cowin?retryWrites=true&w=majority")

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
  print(data)
  
  # iterate through centers
  for center in data:
    for sessions in center.get('sessions'):
      list_of_sessions = []
      list_of_sessions.append(sessions)
      for session in list_of_sessions:
        if session.get('min_age_limit') == age:
          center_name = center.get('name')
          center_id = center.get('center_id')
          slots = session.get('available_capacity')
          
          
          exists = db.find_one({'_id': center_id})
          if not exists:
            hospital = {'_id': center_id, 'name': center_name, 'fourtyFive': [], 'eighteen': []}
            db.insert_one(hospital)
          if age == 45:
            db.update_one({'_id': center_id}, {'$push': {'fourtyFive': {session.get('date'): slots}}})
          """ elif age == 18:
            db.update_one({'_id': center_id}, {'$push': {'eighteen': {session.get('date'): slots}}}) """


def check_for_updates(dId, age):
  date = datetime.datetime.now()
  for i in range(6):
    update_db(dId, date.strftime('%d-%m-%Y'), age)
    date += datetime.timedelta(weeks=1) 

check_for_updates(151, 45)