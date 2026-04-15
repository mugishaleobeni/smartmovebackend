from flask import Blueprint, jsonify, request
import os
from pymongo import MongoClient
from datetime import datetime

newsletter_bp = Blueprint('newsletter', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@newsletter_bp.route('/subscribe', methods=['POST'])
def subscribe():
    data = request.json
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    # Check if already exists
    existing = db.subscribers.find_one({"email": email})
    if existing:
        return jsonify({"message": "Already subscribed"}), 200
        
    db.subscribers.insert_one({
        "email": email,
        "subscribed_at": datetime.utcnow()
    })
    
    return jsonify({"status": "success", "message": "Successfully subscribed"}), 201
