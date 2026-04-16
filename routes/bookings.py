from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient
from datetime import datetime
from utils.mailer import notify_admin_booking, notify_admin_action

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
    
    booking_date = data.get('booking_date')
    
    # Conflict Detection: check for ANY booking on the same date (Global Conflict)
    conflict = False
    if booking_date:
        existing = db.bookings.find_one({
            "booking_date": booking_date,
            "status": {"$ne": "cancelled"}
        })
        if existing:
            conflict = True
            data['has_conflict'] = True
            data['conflict_with'] = str(existing['_id'])
    
    result = db.bookings.insert_one(data)
    booking_id = str(result.inserted_id)
    
    # Fetch car data for notification enrichment
    car_id = data.get('car_id')
    car_data = None
    if car_id:
        try:
            car_data = db.cars.find_one({"_id": ObjectId(car_id)})
            if car_data:
                car_data['_id'] = str(car_data['_id'])
        except Exception:
            pass

    # Notify admins
    try:
        notify_admin_booking(data, car_data, conflict)
        
        # Internal Notification Record
        notif_data = {
            "title": "Double Booking Alert" if conflict else "New Booking Request",
            "message": f"{'⚠️ CONFLICT: ' if conflict else ''}New booking for {data.get('client_name')} - {car_data.get('name') if car_data else 'Vehicle'}",
            "type": "conflict" if conflict else "booking",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
            "related_id": booking_id
        }
        db.notifications.insert_one(notif_data)
        
    except Exception as e:
        print(f"Notification error: {str(e)}")

    return jsonify({"id": booking_id, "conflict": conflict}), 201

@bookings_bp.route('/<booking_id>', methods=['PATCH'])
def update_booking_status(booking_id):
    data = request.json
    
    # Extract fields from request body
    update_data = {}
    if 'status' in data:
        update_data['status'] = data['status']
    if 'driver' in data:
        update_data['driver'] = data['driver']
    if 'external_car' in data:
        update_data['external_car'] = data['external_car']
        
    if update_data:
        db.bookings.update_one({"_id": ObjectId(booking_id)}, {"$set": update_data})
        
        # Notify admin of update
        try:
            booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
            if booking:
                notify_admin_action("updated", booking)
        except Exception as e:
            print(f"Update notification error: {e}")
            
        return jsonify({"status": "updated"}), 200
    return jsonify({"error": "No valid fields to update"}), 400

@bookings_bp.route('/<booking_id>', methods=['DELETE'])
def delete_booking(booking_id):
    try:
        booking = db.bookings.find_one({"_id": ObjectId(booking_id)})
        if booking:
            notify_admin_action("deleted", booking)
    except Exception:
        pass
        
    db.bookings.delete_one({"_id": ObjectId(booking_id)})
    return jsonify({"status": "deleted"}), 200
