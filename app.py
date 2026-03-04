import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

from routes.cars import cars_bp
from routes.bookings import bookings_bp
from routes.expenses import expenses_bp
from routes.auth import auth_bp
from routes.upload import upload_bp
from routes.pricing import pricing_bp
from routes.notifications import notifications_bp
import firebase_admin
from firebase_admin import credentials
from flask_session import Session

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False
CORS(app, supports_credentials=True, origins=["http://localhost:8080", "http://localhost:5173"])

# Session Configuration
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "smartmove-secret-key")
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Firebase Admin Setup
# Note: You need a serviceAccountKey.json file in the root directory
try:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Firebase Admin Error (likely missing serviceAccountKey.json): {e}")

# Register Blueprints
app.register_blueprint(cars_bp, url_prefix='/api/cars')
app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
app.register_blueprint(expenses_bp, url_prefix='/api/expenses')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(upload_bp, url_prefix='/api/upload')
app.register_blueprint(pricing_bp, url_prefix='/api/pricing')
app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database('smart_move_transport') # Gets database from URI path

@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Check if database is reachable
        client.admin.command('ping')
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "message": "Smart Move Transport Backend is active"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "degraded",
            "database": "disconnected",
            "error": str(e)
        }), 500

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "app": "Smart Move Transport Backend",
        "version": "1.0.0",
        "endpoints": ["/health", "/api/cars", "/api/bookings", "/api/expenses"]
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
