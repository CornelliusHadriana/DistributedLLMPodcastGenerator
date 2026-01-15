import pymongo

db_client = pymongo.MongoClient('mongodb://127.0.0.1:27017')
db = db_client['newsletter_to_podcast']