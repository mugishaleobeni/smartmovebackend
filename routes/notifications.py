from flask import Blueprint, jsonify, request
from bson import ObjectId
import os
from datetime import datetime
from pymongo import MongoClient

notifications_bp = Blueprint('notifications', __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    notifications = list(db.notifications.find().sort("created_at", -1).limit(20))
    for n in notifications:
        n['_id'] = str(n['_id'])
        n['id'] = n['_id']
    return jsonify(notifications)

@notifications_bp.route('/test-email', methods=['POST'])
def test_email():
    from utils.mailer import send_email_async
    try:
        # Get target emails (from settings + admin users)
        from utils.mailer import get_admin_emails
        target_emails = get_admin_emails()
        
        if not target_emails:
            target_emails = ["smartmovetransportltd@gmail.com"]
            
        subject = "🧪 Smart Move Email Test"
        html_content = """
        <div style="font-family: sans-serif; padding: 20px; border: 1px solid #3b82f6; border-radius: 10px;">
            <h2 style="color: #3b82f6;">System Test Successful</h2>
            <p>This is a test email from your Smart Move Transport Dashboard.</p>
            <p>If you are receiving this, your email notification system is working correctly.</p>
            <hr/>
            <p style="font-size: 11px; color: #666;">Timestamp: """ + datetime.utcnow().isoformat() + """</p>
        </div>
        """
        
        for email in target_emails:
            send_email_async(email, subject, html_content)
            
        return jsonify({
            "status": "success",
            "message": f"Test email sent to {len(target_emails)} addresses",
            "recipients": target_emails
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@notifications_bp.route('/<notif_id>', methods=['PATCH'])
def update_notification(notif_id):
    data = request.json
    db.notifications.update_one({"_id": ObjectId(notif_id)}, {"$set": data})
    return jsonify({"status": "updated"}), 200

@notifications_bp.route('/mark-all-read', methods=['POST'])
def mark_all_read():
    db.notifications.update_many({"is_read": False}, {"$set": {"is_read": True}})
    return jsonify({"status": "success"}), 200
