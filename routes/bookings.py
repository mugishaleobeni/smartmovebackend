from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient
from datetime import datetime

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
    
    # Add creation timestamp if missing
    if 'created_at' not in data:
        data['created_at'] = datetime.utcnow().isoformat()
    
    result = db.bookings.insert_one(data)
    booking_id = str(result.inserted_id)
    
    # Create notification for admins
    try:
        notif_data = {
            "title": "New Booking Request",
            "message": f"New booking for {data.get('client_name')} - Total: RWF {data.get('total_price')}",
            "type": "booking",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
            "related_id": booking_id
        }
        db.notifications.insert_one(notif_data)
        
        # Simulate Email to Admin
        print(f"--- EMAIL SIMULATION ---")
        print(f"To: admin@smartmove.com")
        print(f"Subject: New Booking Alert - {data.get('client_name')}")
        print(f"Body: A new booking has been placed for vehicle ID {data.get('car_id')}.")
        print(f"Details: {data.get('pickup_location')} -> {data.get('dropoff_location')}")
        print(f"Total: RWF {data.get('total_price')}")
        print(f"------------------------")
        
    except Exception as e:
        print(f"Notification error: {str(e)}")

    return jsonify({"id": booking_id}), 201

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
