import os
import json
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# Load the MongoDB URI from an environment variable
#uri = os.getenv("MONGODB_URI")

# Create a MongoDB client and connect to the server using Server API version 1
#client = MongoClient(uri, server_api=ServerApi('1'))

def test_connection():
    """Test the connection to the MongoDB server.

    This function attempts to 'ping' the MongoDB server to verify
    that the connection is working properly.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        uri = os.getenv("MONGODB_URI")
        if uri is None:
            raise ValueError("Missing environment variable: MONGODB_URI")
        client = MongoClient(uri, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return True
    except Exception as e:
        print(e)
        return False

# Select the MongoDB database and collection
#db = client["Jobliste"]
#collection = db["job_titles"]

def upload_job_titles_to_mongodb(json_file_path="job_titles.json"):
    """Upload job titles from a JSON file to MongoDB.

    This function reads a list of job titles from a local JSON file
    and uploads them to a MongoDB collection. If a document with the
    ID 'current_job_titles' already exists, it will be updated. Otherwise,
    a new document will be created.

    Args:
        json_file_path (str, optional): Path to the JSON file containing job titles.
        Defaults to 'job_titles.json'.

    Returns:
        bool: True if the upload is successful, False if an error occurs.
    """
    try:
        uri = os.getenv("MONGODB_URI")
        if uri is None:
            raise ValueError("Missing environment variable: MONGODB_URI")
        client = MongoClient(uri, server_api=ServerApi('1'))
        db = client["Jobliste"]
        collection = db["job_titles"]

        with open(json_file_path, "r", encoding="utf-8") as f:
            job_titles = json.load(f)

        collection.update_one(
            {"_id": "current_job_titles"},
            {"$set": {"job_titles": job_titles, "count": len(job_titles)}},
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error during MongoDB upload: {str(e)}")
        return False

# Execute connection test only when this script is run directly
if __name__ == '__main__':
    test_connection()