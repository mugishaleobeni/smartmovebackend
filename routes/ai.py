import os
import requests
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime

# Initialize Blueprint
ai_bp = Blueprint('ai', __name__)

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client.get_database('smart_move_transport')
cars_collection = db["cars"]
chat_collection = db["chat_history"]

@ai_bp.route('/chat', methods=['POST'])
def chat():
    try:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            return jsonify({"error": "AI Service not configured"}), 501

        data = request.json
        message = data.get("message")
        user_id = data.get("userId", "guest")
        history = data.get("history", [])

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # Fetch available cars for context
        cars = list(cars_collection.find({"status": {"$ne": "garage"}}))
        cars_info = []
        for c in cars:
            car_id = str(c.get("_id"))
            name = c.get("name", "Unknown")
            price = c.get("price_per_day", 0)
            cars_info.append(f"- {name}: RWF {price}/day. ID to show card: [CAR:{car_id}]")
        
        cars_text = "\n".join(cars_info) if cars_info else "No cars available."

        system_prompt = f"""You are Smart Move Transport AI.
You help users with car selection, booking rides, payment guidance, and issue resolution.
Available cars database:
{cars_text}

Rules:
- Be short, clear, and helpful.
- Ask questions if needed.
- If recommending a car, MUST include its exact ID string format e.g., [CAR:64df...] so the frontend can render it!
- Explain payment methods (MTN MoMo, Cash, Code) if asked.

User ID: {user_id}
"""

        contents = []
        
        # Add history
        for msg in history:
            role = 'model' if msg.get("role") in ["assistant", "model"] else 'user'
            contents.append({"role": role, "parts": [{"text": msg.get("content")}]})
            
        # Add current message
        contents.append({"role": "user", "parts": [{"text": message}]})

        gemini_payload = {
            "systemInstruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": contents
        }

        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        response = requests.post(gemini_url, json=gemini_payload, headers={'Content-Type': 'application/json'})
        
        if not response.ok:
            print("Gemini API Error:", response.text)
            return jsonify({"error": "Failed to contact AI service"}), 502
            
        gemini_data = response.json()
        reply_text = gemini_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', "I'm sorry, I couldn't process that.")

        return jsonify({"reply": reply_text}), 200

    except Exception as e:
        print("Chat API unhandled error", e)
        return jsonify({"error": str(e)}), 500

@ai_bp.route('/chat/history', methods=['POST'])
def save_history():
    try:
        data = request.json
        user_id = data.get("userId")
        messages = data.get("messages", [])

        if not user_id or user_id == "guest":
            return jsonify({"error": "Valid User ID required"}), 400

        chat_collection.update_one(
            {"userId": user_id},
            {"$set": {"messages": messages, "updatedAt": datetime.utcnow()}},
            upsert=True
        )

        return jsonify({"message": "History saved successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@ai_bp.route('/chat/history/<user_id>', methods=['GET'])
def get_history(user_id):
    try:
        if not user_id or user_id == "guest":
            return jsonify({"messages": []}), 200

        history = chat_collection.find_one({"userId": user_id})
        if history:
            return jsonify({"messages": history.get("messages", [])}), 200
        return jsonify({"messages": []}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
