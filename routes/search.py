from flask import Blueprint, jsonify, request
import os
from pymongo import MongoClient
from bson.objectid import ObjectId

search_bp = Blueprint('search', __name__)

# MongoDB Setup (re-using connection logic for the blueprint)
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database('smart_move_transport')

@search_bp.route('/', methods=['GET'])
def global_search():
    query = request.args.get('q', '')
    if not query or len(query) < 2:
        return jsonify([])

    results = []

    # 1. Search Cars (make, model)
    cars = list(db.cars.find({
        "$or": [
            {"make": {"$regex": query, "$options": "i"}},
            {"model": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5))

    for car in cars:
        results.append({
            "id": str(car["_id"]),
            "type": "car",
            "title": f"{car['make']} {car['model']}",
            "subtitle": f"Vehicle · {car.get('year', '')}",
            "url": f"/admin/cars?search={car['make']}"
        })

    # 2. Search Bookings (client name, phone)
    bookings = list(db.bookings.find({
        "$or": [
            {"client_name": {"$regex": query, "$options": "i"}},
            {"phone": {"$regex": query, "$options": "i"}}
        ]
    }).limit(5))

    for booking in bookings:
        results.append({
            "id": str(booking["_id"]),
            "type": "booking",
            "title": booking.get("client_name", "Unknown Client"),
            "subtitle": f"Booking · {booking.get('status', 'Pending')}",
            "url": f"/admin/bookings?search={booking.get('client_name')}"
        })

    return jsonify(results)
