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

# -------------------- CHAT ROUTE --------------------
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

        # -------------------- FETCH CARS --------------------
        cars = list(cars_collection.find({"status": {"$ne": "garage"}}))
        cars_info = []

        for c in cars:
            car_id = str(c.get("_id"))
            name = c.get("name", "Unknown")
            price = c.get("price_per_day", 0)

            cars_info.append(
                f"- {name}: RWF {price}/day. ID: [CAR:{car_id}]"
            )

        cars_text = "\n".join(cars_info) if cars_info else "No cars available."

        # -------------------- SYSTEM PROMPT --------------------
        system_prompt = f"""You are Smart Move Transport AI.

You help users with:
- Car selection
- Booking rides
- Payment guidance
- Issue resolution

Available cars:
{cars_text}

Rules:
- Be short, clear, and helpful
- Ask questions when needed
- Recommend max 3 cars
- ALWAYS include car ID like: [CAR:xxxx]
- Guide user to next step (book, confirm, contact)
- Explain payment methods: MTN MoMo, Cash, Code

User ID: {user_id}
"""

        # -------------------- BUILD CHAT HISTORY --------------------
        filtered_contents = []

        for msg in history:
            role = "model" if msg.get("role") in ["assistant", "model"] else "user"
            filtered_contents.append({
                "role": role,
                "parts": [{"text": msg.get("content", "")}]
            })

        # Add current user message
        filtered_contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })

        # -------------------- GEMINI PAYLOAD (FIXED) --------------------
        gemini_payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": system_prompt}]
                }
            ] + filtered_contents
        }

        # ✅ Correct endpoint
        gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

        print("Gemini URL:", gemini_url)  # Debug log

        response = requests.post(
            gemini_url,
            json=gemini_payload,
            headers={"Content-Type": "application/json"}
        )

        # -------------------- ERROR HANDLING --------------------
        if not response.ok:
            print("Gemini API Error:", response.text)
            return jsonify({
                "error": "Failed to contact AI service",
                "details": response.text,
                "status": response.status_code
            }), 200

        gemini_data = response.json()

        # -------------------- SAFE RESPONSE PARSING --------------------
        candidates = gemini_data.get("candidates", [])

        if not candidates:
            return jsonify({"reply": "AI did not return a response."}), 200

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        reply_text = parts[0].get("text") if parts else "No response from AI."

        # -------------------- SAVE CHAT --------------------
        if user_id != "guest":
            chat_collection.update_one(
                {"userId": user_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [
                                {"role": "user", "content": message},
                                {"role": "assistant", "content": reply_text}
                            ]
                        }
                    },
                    "$set": {"updatedAt": datetime.utcnow()}
                },
                upsert=True
            )

        return jsonify({"reply": reply_text}), 200

    except Exception as e:
        print("Chat API unhandled error:", e)
        return jsonify({"error": str(e)}), 500


# -------------------- SAVE HISTORY --------------------
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
            {
                "$set": {
                    "messages": messages,
                    "updatedAt": datetime.utcnow()
                }
            },
            upsert=True
        )

        return jsonify({"message": "History saved successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------- GET HISTORY --------------------
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