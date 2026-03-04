import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_connection():
    uri = os.getenv("MONGO_URI")
    print(f"Testing connection to: {uri.split('@')[1] if '@' in uri else 'Generic URI'}")
    
    try:
        client = MongoClient(uri)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("SUCCESS: MongoDB Atlas Connection")
        
        db = client.get_database()
        print(f"Database Name: {db.name}")
        
    except Exception as e:
        print(f"FAILED: Connection Failed: {e}")

if __name__ == "__main__":
    verify_connection()
