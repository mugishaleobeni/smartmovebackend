from flask import Blueprint, request, jsonify
from bson import ObjectId
import os
import cloudinary
import cloudinary.uploader
from pymongo import MongoClient
from datetime import datetime

files_bp = Blueprint('files', __name__)

# MongoDB Setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client.get_database('smart_move_transport')

# Cloudinary configuration
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure = True
)

@files_bp.route('/folders', methods=['GET'])
def get_folders():
    parent_id = request.args.get('parent_id')
    query = {"parent_id": parent_id if parent_id else None}
    folders = list(db.folders.find(query))
    for f in folders:
        f['_id'] = str(f['_id'])
    return jsonify(folders)

@files_bp.route('/folders', methods=['POST'])
def create_folder():
    data = request.json
    folder = {
        "name": data.get('name'),
        "parent_id": data.get('parent_id'),
        "is_system": False,
        "created_at": datetime.utcnow().isoformat()
    }
    result = db.folders.insert_one(folder)
    return jsonify({"_id": str(result.inserted_id)}), 201

@files_bp.route('', methods=['GET'])
def get_files():
    folder_id = request.args.get('folder_id')
    query = {"folder_id": folder_id if folder_id else None}
    files = list(db.files.find(query))
    for f in files:
        f['_id'] = str(f['_id'])
    return jsonify(files)

@files_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    folder_id = request.form.get('folder_id')
    
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    try:
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(file)
        
        file_doc = {
            "name": file.filename,
            "url": upload_result.get('secure_url'),
            "public_id": upload_result.get('public_id'),
            "folder_id": folder_id if folder_id else None,
            "file_type": "image" if upload_result.get('resource_type') == 'image' else "pdf",
            "size": upload_result.get('bytes'),
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = db.files.insert_one(file_doc)
        file_doc['_id'] = str(result.inserted_id)
        
        return jsonify(file_doc), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@files_bp.route('/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    try:
        file_doc = db.files.find_one({"_id": ObjectId(file_id)})
        if not file_doc:
            return jsonify({"error": "File not found"}), 404
        
        # Delete from Cloudinary
        cloudinary.uploader.destroy(file_doc['public_id'])
        
        # Delete from MongoDB
        db.files.delete_one({"_id": ObjectId(file_id)})
        
        return jsonify({"message": "File deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
