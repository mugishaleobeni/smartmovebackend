from flask import Blueprint, jsonify, request
import os
from pymongo import MongoClient

settings_bp = Blueprint('settings', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@settings_bp.route('/agreement', methods=['GET'])
def get_agreement():
    setting = db.settings.find_one({"key": "contract_agreement"})
    if not setting:
        return jsonify({"text": ""})
    return jsonify({"text": setting.get('value', '')})

@settings_bp.route('/agreement', methods=['POST'])
def update_agreement():
    data = request.json
    text = data.get('text', '')
    
    db.settings.update_one(
        {"key": "contract_agreement"},
        {"$set": {"value": text, "updated_at": os.getenv("CURRENT_TIME")}}, # Note: using env time or just leave it
        upsert=True
    )
    return jsonify({"status": "success"})
