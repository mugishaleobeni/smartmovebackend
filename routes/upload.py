from flask import Blueprint, request, jsonify
import cloudinary
import cloudinary.uploader
import os

upload_bp = Blueprint('upload', __name__)

# Cloudinary configuration
# Ideally these should be in .env
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    api_key = os.getenv("CLOUDINARY_API_KEY", "lQkpLZmthjXKYgB7EGrFhFlxo5g"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET", ""),
    secure = True
)

@upload_bp.route('', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file)
        
        return jsonify({
            "url": upload_result.get('secure_url'),
            "public_id": upload_result.get('public_id')
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
