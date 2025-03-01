import redis
import json
import os
from pymongo import MongoClient

# Load environment variables
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
MONGO_DB_USERNAME = os.getenv("MONGO_DB_ROOT_USERNAME")
MONGO_DB_PASSWORD = os.getenv("MONGO_DB_ROOT_PASSWORD")
COLLECTION_NAME = "destinations"

# Initialize Redis and MongoDB
redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)
mongo_client = MongoClient(
    "mongodb://mongo_user:mongo_pass@mongodb:27017/",
    authSource="admin"  # 👈 Ensure authentication happens in the "admin" database
)
mongo_db = mongo_client.get_database("globetrotter_mongo")
destination_collection = mongo_db[COLLECTION_NAME]

# Initialize Redis with destination data
def initialize_redis():
    redis_client.delete('destinations')  # Ensure fresh list
    redis_client.delete('destination_names')
    redis_client.set('global_pointer', 0)

    # Fetch from MongoDB
    destinations = list(destination_collection.find({}, {"_id": 0, "city": 1, "country": 1, "clues": 1, "fun_fact": 1, "trivia": 1}))

    # ✅ Store as LIST, not string!
    for destination in destinations:
        redis_client.rpush('destinations', json.dumps(destination))

    destination_names = [f"{d['city']}, {d['country']}" for d in destinations]
    
    if destination_names:
        redis_client.delete('destination_names')  # Ensure fresh list
        redis_client.rpush('destination_names', *destination_names) # Store names directly as strings


# Run initialization
if __name__ == "__main__":
    initialize_redis()
    print("✅ Redis initialized successfully!")
