from pymongo import MongoClient
import os
from utils.logger_config import setup_logging


class MongoDB:
    def __init__(self, db_name: str, uri: str = None):

        self.client = MongoClient(uri or os.getenv("MONGO_URI"))
        self.db = self.client[db_name]
        self.logger = setup_logging()

    def create_collection(self, name: str):

        if name not in self.db.list_collection_names():
            self.db.create_collection(name)
            self.logger.info(f"Collection '{name}' created.")
            return {"message": f"Collection '{name}' created."}
        else:
            self.logger.info(f"Collection '{name}' already exists.")
            return {"message": f"Collection '{name}' already exists."}

    def insert(self, data: dict, collection_name: str):

        collection = self.db[collection_name]
        result = collection.insert_one(data)
        self.logger.info(f"Document inserted with ID: {result.inserted_id}")
        return str(result.inserted_id)

    def get_databases(self):

        databases = self.client.list_database_names()
        self.logger.info(f"Retrieved databases: {databases}")
        return databases

    def get_collections(self):

        collections = self.db.list_collection_names()
        self.logger.info(f"Retrieved collections: {collections}")
        return collections
    def serialize_mongo_document(self, document):
        if "_id" in document:
            document["_id"] = str(document["_id"])
        return document
    def get_collection_data(self, collection_name: str,query: dict = None):

        collection = self.db[collection_name]
        query = query or {}
        data = list(collection.find(query))
        self.logger.info(
            f"Retrieved {len(data)} documents from collection '{collection_name}'."
        )
        serialized_data = [self.serialize_mongo_document(doc) for doc in data]
        return serialized_data
