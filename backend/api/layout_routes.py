from flask import Blueprint, request, jsonify, current_app, send_from_directory
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from services.layout_service import LayoutService

layout_bp = Blueprint('layout', __name__, url_prefix='/api/layout')
logger = logging.getLogger(__name__)

@layout_bp.route('/recognize', methods=['POST'])
def recognize_layout():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file:
        try:
            filename = secure_filename(file.filename)
            # Generate unique ID for this task
            task_id = str(uuid.uuid4())
            
            # Create task directory
            upload_folder = current_app.config['UPLOAD_FOLDER']
            task_dir = os.path.join(upload_folder, 'tasks', task_id)
            os.makedirs(task_dir, exist_ok=True)
            
            file_path = os.path.join(task_dir, filename)
            file.save(file_path)
            
            logger.info(f"Starting layout recognition for task {task_id}, file: {filename}")
            
            # Process (Synchronous for now)
            service = LayoutService()
            results = service.analyze_layout(file_path, task_dir)
            
            # Add image URLs to results
            results['images'] = {
                'original': f'/api/layout/images/{task_id}/{filename}',
                'segmentation': f'/api/layout/images/{task_id}/segmentation_vis.jpg'
            }
            
            # Flatten the structure for frontend
            flat_result = {
                "total_wall_length_pixels": results['pixel_results']['total_wall_length_pixels'],
                "total_wall_length_mm": results['real_results'].get('total_wall_length_mm'),
                "image_width": results['pixel_results']['image_width'],
                "image_height": results['pixel_results']['image_height'],
                "rooms": results['real_results'].get('rooms', results['pixel_results']['rooms']), # Use real results if available, else pixel
                "images": results['images'],
                "scale_info": results['scale_info']
            }
            
            return jsonify({
                "status": "success",
                "message": "Analysis complete",
                "task_id": task_id,
                "data": flat_result
            })
            
        except Exception as e:
            logger.error(f"Error processing layout: {str(e)}", exc_info=True)
            return jsonify({"error": str(e), "status": "error"}), 500

@layout_bp.route('/images/<task_id>/<filename>')
def get_image(task_id, filename):
    upload_folder = current_app.config['UPLOAD_FOLDER']
    task_dir = os.path.join(upload_folder, 'tasks', task_id)
    return send_from_directory(task_dir, filename)
