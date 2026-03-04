from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from pymongo import MongoClient

expenses_bp = Blueprint('expenses', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database()

@expenses_bp.route('/', methods=['GET'])
def get_expenses():
    expenses = list(db.expenses.find().sort("expense_date", -1))
    for e in expenses:
        e['_id'] = str(e['_id'])
    return jsonify(expenses)

@expenses_bp.route('/', methods=['POST'])
def log_expense():
    data = request.json
    result = db.expenses.insert_one(data)
    return jsonify({"id": str(result.inserted_id)}), 201
