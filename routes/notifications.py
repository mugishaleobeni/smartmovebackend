from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient

notifications_bp = Blueprint('notifications', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    notifications = list(db.notifications.find().sort("created_at", -1).limit(20))
    for n in notifications:
        n['_id'] = str(n['_id'])
        n['id'] = n['_id']
    return jsonify(notifications)

@notifications_bp.route('/<notif_id>', methods=['PATCH'])
def update_notification(notif_id):
    data = request.json
    db.notifications.update_one({"_id": ObjectId(notif_id)}, {"$set": data})
    return jsonify({"status": "updated"}), 200

@notifications_bp.route('/mark-all-read', methods=['POST'])
def mark_all_read():
    db.notifications.update_many({"is_read": False}, {"$set": {"is_read": True}})
    return jsonify({"status": "success"}), 200
