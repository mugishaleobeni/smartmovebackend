import os
import requests
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime

# -------------------- INIT --------------------
ai_bp = Blueprint('ai', __name__)

MONGO_URI = os.getenv("MONGO_URI")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = MongoClient(MONGO_URI)
db = client.get_database('smart_move_transport')

cars_collection = db["cars"]
chat_collection = db["chat_history"]

# -------------------- CHAT --------------------
@ai_bp.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get("message")
        user_id = data.get("userId", "guest")
        history = data.get("history", [])

        if not message:
            return jsonify({"error": "Message is required"}), 400

        # -------------------- CARS CONTEXT --------------------
        cars = list(cars_collection.find({"status": {"$ne": "garage"}}))

        cars_text = "\n".join([
            f"- {c.get('name','Unknown')}: RWF {c.get('price_per_day',0)}/day | ID: [CAR:{str(c.get('_id'))}]"
            for c in cars
        ]) or "No cars available."

        # -------------------- SYSTEM PROMPT --------------------
        system_prompt = f"""
You are Smart Move Transport AI.

You help users with:
- Car booking
- Car selection
- Payment (MTN MoMo, Cash, Code)
- Customer support

Available cars:
{cars_text}

RULES:
- Be short and clear
- Recommend max 3 cars
- Always include car ID like [CAR:xxxx]
- Ask questions if needed
- Guide user to booking steps
"""

        # -------------------- HISTORY BUILD --------------------
        contents = [
            {
                "role": "user",
                "parts": [{"text": system_prompt}]
            }
        ]

        for msg in history:
            contents.append({
                "role": "model" if msg.get("role") in ["assistant", "model"] else "user",
                "parts": [{"text": msg.get("content", "")}]
            })

        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        # -------------------- GEMINI REQUEST (FIXED) --------------------
        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent"

        response = requests.post(
            gemini_url,
            json={"contents": contents},
            headers={
                "Content-Type": "application/json",
                "X-goog-api-key": GEMINI_API_KEY
            }
        )

        # -------------------- ERROR HANDLING --------------------
        if not response.ok:
            print("Gemini API Error:", response.text)
            return jsonify({
                "error": "AI request failed",
                "details": response.text
            }), 200

        result = response.json()

        candidates = result.get("candidates", [])
        if not candidates:
            return jsonify({"reply": "No response from AI"}), 200

        reply = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")

        # -------------------- SAVE CHAT --------------------
        if user_id != "guest":
            chat_collection.update_one(
                {"userId": user_id},
                {
                    "$push": {
                        "messages": [
                            {"role": "user", "content": message},
                            {"role": "assistant", "content": reply}
                        ]
                    },
                    "$set": {"updatedAt": datetime.utcnow()}
                },
                upsert=True
            )

        return jsonify({"reply": reply}), 200

    except Exception as e:
        print("Chat error:", e)
        return jsonify({"error": str(e)}), 500


# -------------------- SAVE HISTORY --------------------
@ai_bp.route('/chat/history', methods=['POST'])
def save_history():
    try:
        data = request.json
        user_id = data.get("userId")
        messages = data.get("messages", [])

        if not user_id or user_id == "guest":
            return jsonify({"error": "Valid user required"}), 400

        chat_collection.update_one(
            {"userId": user_id},
            {"$set": {"messages": messages, "updatedAt": datetime.utcnow()}},
            upsert=True
        )

        return jsonify({"message": "Saved"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------- GET HISTORY --------------------
@ai_bp.route('/chat/history/<user_id>', methods=['GET'])
def get_history(user_id):
    try:
        data = chat_collection.find_one({"userId": user_id})

        if not data:
            return jsonify({"messages": []}), 200

        return jsonify({"messages": data.get("messages", [])}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500