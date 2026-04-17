from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient
from utils.mailer import notify_new_car, notify_price_change

cars_bp = Blueprint('cars', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@cars_bp.route('/', methods=['GET'])
def get_cars():
    cars = list(db.cars.find())
    for car in cars:
        car['_id'] = str(car['_id'])
    return jsonify(cars)

@cars_bp.route('/<car_id>', methods=['GET'])
def get_car(car_id):
    car = db.cars.find_one({"_id": ObjectId(car_id)})
    if car:
        car['_id'] = str(car['_id'])
        return jsonify(car)
    return jsonify({"error": "Car not found"}), 404

@cars_bp.route('/', methods=['POST'])
def add_car():
    data = request.json
    result = db.cars.insert_one(data)
    
    # Notify subscribers about the new car
    try:
        notify_new_car(data.get('name', 'New Car'), data.get('type', 'Vehicle'))
    except Exception as e:
        print(f"Notification error: {e}")
        
    return jsonify({"id": str(result.inserted_id)}), 201

@cars_bp.route('/<car_id>', methods=['PUT', 'PATCH'])
def update_car(car_id):
    data = request.json
    if '_id' in data:
        del data['_id']
        
    # Get current car data to check for price change
    old_car = db.cars.find_one({"_id": ObjectId(car_id)})
    
    result = db.cars.update_one({"_id": ObjectId(car_id)}, {"$set": data})
    
    if result.matched_count:
        # If price changed, notify subscribers
        # We check both 'price_per_day' and 'price' for compatibility with frontend versions
        pricing_keys = ['price', 'price_per_day']
        new_price = None
        for key in pricing_keys:
            if key in data:
                new_price = data[key]
                break
        
        if old_car and new_price is not None:
            # Check old car for either key
            old_price = old_car.get('price') or old_car.get('price_per_day')
            
            if str(old_price) != str(new_price):
                try:
                    notify_price_change(old_car.get('name', 'Car'), new_price)
                except Exception as e:
                    print(f"Notification error: {e}")
                    
        return jsonify({"message": "Car updated successfully"})
    return jsonify({"error": "Car not found"}), 404

@cars_bp.route('/<car_id>', methods=['DELETE'])
def delete_car(car_id):
    result = db.cars.delete_one({"_id": ObjectId(car_id)})
    if result.deleted_count:
        return jsonify({"message": "Car deleted successfully"})
    return jsonify({"error": "Car not found"}), 404
