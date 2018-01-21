from pymongo import MongoClient
from ext_api.config import mongodb_connection, db_name

client = MongoClient(mongodb_connection)
db = client[db_name]
