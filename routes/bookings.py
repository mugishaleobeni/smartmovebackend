from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient

bookings_bp = Blueprint('bookings', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@bookings_bp.route('/', methods=['GET'])
def get_bookings():
    bookings = list(db.bookings.find().sort("created_at", -1))
    for b in bookings:
        b['_id'] = str(b['_id'])
    return jsonify(bookings)

@bookings_bp.route('/', methods=['POST'])
def create_booking():
    data = request.json
    result = db.bookings.insert_one(data)
    return jsonify({"id": str(result.inserted_id)}), 201

@bookings_bp.route('/<booking_id>', methods=['PATCH'])
def update_booking_status(booking_id):
    data = request.json
    status = data.get('status')
    if status:
        db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": {"status": status}})
        return jsonify({"status": "updated"}), 200
    return jsonify({"error": "Status missing"}), 400

@bookings_bp.route('/<booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    db.bookings.delete_one({"_id": ObjectId(booking_id)})
    return jsonify({"status": "deleted"}), 200
