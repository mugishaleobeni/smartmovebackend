import sys
import os

# Add the current directory to sys.path to import utils
sys.path.append(os.getcwd())

from utils.mailer import notify_new_car, notify_price_change
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    try:
        print("Testing MongoDB Connection...")
        client = MongoClient(os.getenv("MONGO_URI"))
        db = client.get_database('smart_move_transport')
        count = db.subscribers.count_documents({{}})
        print(f"Connection Successful! Found {{count}} subscribers.")
        return True
    except Exception as e:
        print(f"Database Connection Failed: {{e}}")
        return False

def test_notification_logic():
    print("\n--- Testing Notification Logic (No emails sent if SMTP is not configured) ---")
    print("Simulating New Car Notification...")
    try:
        # This will attempt to send emails if SMTP is configured in .env
        notify_new_car("Test Tesla Model S", "Electric Sedan")
        print("Notification logic executed.")
    except Exception as e:
        print(f"Logic failure: {{e}}")

if __name__ == "__main__":
    if test_connection():
        test_notification_logic()
        print("\nVerification Complete.")
    else:
        print("\nVerification Failed due to database connection.")
