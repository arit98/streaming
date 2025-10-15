from pymongo import MongoClient
from config import MONGO_URL, DB_NAME

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
users_col = db["users"]
streams_col = db["streams"]
overlays_col = db["overlays"]