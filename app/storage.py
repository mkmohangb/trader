from pymongo import MongoClient


client = MongoClient('localhost', 27017)
db = client.straddle_db
trades = db.trades
