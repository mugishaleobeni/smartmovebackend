from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient
from utils.mailer import notify_general_update

pricing_bp = Blueprint('pricing', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@pricing_bp.route('/', methods=['GET'])
def get_pricing_rules():
    rules = list(db.pricing_rules.find())
    for r in rules:
        r['_id'] = str(r['_id'])
        # Add id for compatibility with frontend interface
        r['id'] = r['_id']
    return jsonify(rules)

@pricing_bp.route('/', methods=['POST'])
def create_pricing_rule():
    data = request.json
    result = db.pricing_rules.insert_one(data)
    
    # Notify subscribers about new pricing rules/offers
    try:
        notify_general_update(
            data.get('name', 'New Special Offer'),
            f"We have introduced a new pricing plan: <strong>{data.get('name')}</strong>. Checkout our updated rates and special offers on the website!"
        )
    except Exception as e:
        print(f"Notification error: {e}")
        
    return jsonify({"id": str(result.inserted_id)}), 201

@pricing_bp.route('/<rule_id>', methods=['PUT'])
def update_pricing_rule(rule_id):
    data = request.json
    if '_id' in data: del data['_id']
    if 'id' in data: del data['id']
    db.pricing_rules.update_one({"_id": ObjectId(rule_id)}, {"$set": data})
    
    # Notify subscribers about rate changes
    try:
        notify_general_update(
            f"Update: {data.get('name', 'Rates Updated')}",
            f"We have updated our <strong>{data.get('name')}</strong> pricing plan. See the latest affordable rates on our website."
        )
    except Exception as e:
        print(f"Notification error: {e}")
        
    return jsonify({"status": "updated"}), 200

@pricing_bp.route('/<rule_id>', methods=['DELETE'])
def delete_pricing_rule(rule_id):
    db.pricing_rules.delete_one({"_id": ObjectId(rule_id)})
    return jsonify({"status": "deleted"}), 200
