from flask import Blueprint, jsonify, request, session
import firebase_admin
from firebase_admin import auth as firebase_auth
import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth_bp = Blueprint('auth', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@auth_bp.route('/login', methods=['POST'])
def login():
    id_token = request.json.get('idToken')
    if not id_token:
        return jsonify({"error": "No ID token provided"}), 400

    try:
        # Verify the Firebase ID token
        decoded_token = firebase_auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')

        # Find or create user in MongoDB
        user = db.users.find_one({"firebase_uid": uid})
        if not user:
            # Check if this is the first user in the system
            user_count = db.users.count_documents({})
            role = "admin" if user_count == 0 else "user"
            
            user_data = {
                "firebase_uid": uid,
                "email": email,
                "name": name,
                "picture": picture,
                "role": role,
                "created_at": decoded_token.get('iat')
            }
            # Special case for admin email from previous context (backward compatibility)
            if email == "leo@gmail.com":
                user_data["role"] = "admin"
            
            db.users.insert_one(user_data)
            user = user_data

        # Set session data
        session['user_id'] = str(user.get('_id'))
        session['role'] = user.get('role', 'user')

        return jsonify({
            "message": "Login successful",
            "user": {
                "uid": uid,
                "email": email,
                "name": name,
                "role": user.get('role', 'user')
            }
        }), 200

    except Exception as e:
        print(f"Auth Login Error: {str(e)}")
        return jsonify({"error": str(e), "message": "Firebase token verification failed"}), 401

@auth_bp.route('/register/manual', methods=['POST'])
def register_manual():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if db.users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400

    user_count = db.users.count_documents({})
    role = "admin" if user_count == 0 else "user"

    user_data = {
        "email": email,
        "name": name,
        "phone": phone,
        "password": generate_password_hash(password),
        "role": role,
        "created_at": datetime.utcnow()
    }

    db.users.insert_one(user_data)
    
    return jsonify({
        "message": "User registered successfully",
        "user": {
            "email": email,
            "name": name,
            "role": role
        }
    }), 201

@auth_bp.route('/login/manual', methods=['POST'])
def login_manual():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = db.users.find_one({"email": email})
    if not user or 'password' not in user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid email or password"}), 401

    # Set session data
    session['user_id'] = str(user.get('_id'))
    session['role'] = user.get('role', 'user')

    return jsonify({
        "message": "Login successful",
        "user": {
            "uid": user.get('firebase_uid'), # Might be None for manual
            "email": email,
            "name": user.get('name'),
            "role": user.get('role', 'user')
        }
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    if 'user_id' not in session:
        return jsonify({"authenticated": False}), 200
    
    try:
        from bson import ObjectId
        user = db.users.find_one({"_id": ObjectId(session['user_id'])})
        if not user:
            return jsonify({"authenticated": False}), 200
            
        return jsonify({
            "authenticated": True,
            "uid": user.get('firebase_uid'),
            "email": user.get('email'),
            "name": user.get('name'),
            "role": user.get('role', 'user')
        }), 200
    except Exception as e:
        return jsonify({"authenticated": False, "error": str(e)}), 200
