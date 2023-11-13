from pymongo import MongoClient

# Importing MONGO_CLIENT from the configuration module
from app.api.config.env import MONGO_CLIENT

class Database:
    def __init__(self, uri: str):
        self._client = MongoClient(uri)
        self._db = self._client.example # Change example for DB name

    @property
    def client(self):
        return self._client

    @property
    def db(self):
        return self._db
    
    # Collections
    @property
    def items(self):
        return self._db.items
    
database = Database(MONGO_CLIENT)
