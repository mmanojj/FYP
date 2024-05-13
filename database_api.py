import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv('CONNECTION_STRING'))
db = client['Dialogflow-Mongodb']
collection = db['user_data']
appointment_collection = db['appointment']  
personal_info_collection = db["personal_information"]
medical_info_collection = db["medical_information"]

def save_user_data(key: str, value: str):
    document = {
        'key': key,
        'value': value
    }
    collection.insert_one(document)

def get_user_data(key: str) -> str:
    document = collection.find_one({'key': key})
    if document:
        # Check if the value is a dictionary
        if isinstance(document['value'], dict):
            # For age and job, extract specific keys
            if key == 'age':
                return str(document['value'].get('amount', ''))
            elif key == 'job':
                return str(document['value'].get('title', ''))
            # For other entities, extract directly
            else:
                return str(document['value'])
        else:
            return str(document['value'])
    else:
        return None

def save_appointment(activity: str, time: str, date: str):
    appointment_text = f"Your {activity} appointment is set at {time} on {date}"
    document = {
        'appointment_text': appointment_text
    }
    appointment_collection.insert_one(document)

def get_all_appointment_texts() -> list:
    appointment_texts = []
    cursor = appointment_collection.find({})
    for document in cursor:
        appointment_texts.append(document['appointment_text'])
    return appointment_texts

def save_personal_information(personal_info):
    personal_info_collection.insert_one({"info": personal_info})

def get_personal_information():
  personal_info_entries = personal_info_collection.find({}, {"_id": 0, "info": 1})
  return [entry["info"] for entry in personal_info_entries]

def save_medical_information(medical_info):
    medical_info_collection.insert_one({"info": medical_info})

def get_medical_information():
    medical_info_entries = medical_info_collection.find({}, {"_id": 0, "info": 1})
    return [entry["info"] for entry in medical_info_entries]

def clear_all_data():
  # Clear all data in all collections
  collection.delete_many({})
  appointment_collection.delete_many({})
  personal_info_collection.delete_many({})
  medical_info_collection.delete_many({})
  
