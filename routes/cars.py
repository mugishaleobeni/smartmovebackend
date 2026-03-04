from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient

cars_bp = Blueprint('cars', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database()

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
    return jsonify({"id": str(result.inserted_id)}), 201
