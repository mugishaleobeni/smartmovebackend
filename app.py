import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from routes.cars import cars_bp
from routes.bookings import bookings_bp
from routes.expenses import expenses_bp

app = Flask(__name__)
CORS(app)

# Register Blueprints
app.register_blueprint(cars_bp, url_prefix='/api/cars')
app.register_blueprint(bookings_bp, url_prefix='/api/bookings')
app.register_blueprint(expenses_bp, url_prefix='/api/expenses')

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database() # Gets database from URI path

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
