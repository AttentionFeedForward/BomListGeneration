"""
模块识别API路由模块

该模块提供模块识别相关的RESTful API接口，包括：
1. 模块识别接口 (/api/module/identify) - 接收图像和检测数据，返回识别结果
2. 健康检查接口 (/api/module/health) - 检查服务状态和依赖项

主要功能：
- 文件上传处理（图像文件和JSON数据文件）
- 请求参数验证和数据格式检查
- 调用业务逻辑服务执行模块识别
- 统一的响应格式和错误处理
- 临时文件管理和清理

支持的图像格式：jpg, jpeg, png, bmp
支持的参数：
- confidence_threshold: 置信度阈值 (0.0-1.0)
- debug: 是否启用调试模式 (true/false)

错误处理：
- 400: 请求参数错误、文件格式错误、数据验证失败
- 404: 文件不存在
- 500: 服务内部错误
"""

import os
import json
import tempfile
import shutil
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from marshmallow import Schema, fields, ValidationError, validate

from services.integrated_contour_service import IntegratedContourService

# 创建蓝图
module_bp = Blueprint("module", __name__, url_prefix="/api/module")

# 全局服务实例
integrated_service = None


def get_integrated_service() -> IntegratedContourService:
    """
    获取整合轮廓服务实例

    从Flask应用配置中读取参数，创建并返回IntegratedContourService实例。
    使用配置文件中的参数或默认值来初始化服务。

    Returns:
        IntegratedContourService: 配置好的整合轮廓服务实例

    Raises:
        ImportError: 当依赖模块不可用时
        ValueError: 当配置参数值无效时
    """
    global integrated_service
    if integrated_service is None:
        # 从配置中获取参数
        config = current_app.config
        integrated_service = IntegratedContourService(
            enable_scale_filter=config.get("MODULE_ENABLE_SCALE_FILTER", True),
            scale_deviation_threshold=config.get("MODULE_SCALE_DEVIATION_THRESHOLD", 0.05),
        )
    return integrated_service


def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@module_bp.route("/health", methods=["GET"])
def health_check():

    """
    健康检查接口

    检查整合轮廓服务的健康状态和依赖项可用性。

    Request:
        Method: GET
        URL: /api/module/health

    Response:
        200: 服务健康
        {
            "success": true,
            "data": {
                "service_name": "Integrated Contour Service",
                "status": "healthy",
                "timestamp": "2024-01-01T12:00:00Z",
                "dependencies": {
                    "dimension_matcher": {
                        "status": "available",
                        "message": "Module loaded successfully"
                    },
                    "opencv": {
                        "status": "available",
                        "message": "OpenCV is available"
                    }
                }
            }
        }

        503: 服务不健康
        {
            "success": false,
            "data": {
                "service_name": "Integrated Contour Service",
                "status": "unhealthy",
                "dependencies": {...}
            }
        }

        500: 健康检查失败
        {
            "success": false,
            "error": "Health check failed: 错误描述"
        }

    Returns:
        JSON响应包含服务状态和依赖项信息
    """
    try:
        # 获取整合服务实例并执行健康检查
        service = get_integrated_service()
        health_info = service.check_health()

        # 添加时间戳
        health_info["timestamp"] = datetime.now().isoformat()

        # 根据健康状态确定HTTP状态码
        status_code = 200
        if health_info["status"] == "unhealthy":
            status_code = 503
        elif health_info["status"] == "degraded":
            status_code = 200  # 降级但仍可用

        return jsonify({"success": True, "data": health_info}), status_code

    except Exception as e:
        current_app.logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "Health check failed", "details": str(e)}), 500


# 轮廓处理相关的Schema
class ContourProcessSchema(Schema):
    """轮廓处理请求参数验证Schema"""
    confidence_threshold = fields.Float(
        load_default=lambda: current_app.config.get("CONFIDENCE_THRESHOLD", 0.5),
        validate=validate.Range(min=0, max=1, error="confidence_threshold must be between 0 and 1")
    )
    debug = fields.Boolean(load_default=False)


@module_bp.route("/process-contour", methods=["POST"])
def process_contour():
    """
    处理图像轮廓并计算几何属性
    
    接收图像文件和可选的JSON数据，提取轮廓，计算几何属性（边长、周长、面积等）。
    3D模型生成由前端负责。
    
    请求参数:
        - image: 图像文件 (必需)
        - json_data: JSON数据文件 (可选)
        - confidence_threshold: 置信度阈值 (可选, 默认0.5, 范围0-1)
        - debug: 调试模式 (可选, 默认false)
    
    响应格式:
        成功 (200):
        {
            "success": true,
            "data": {
                "contour_info": { ... },
                "processing_time": ...
            }
        }
        
        错误 (400/500):
        {
            "success": false,
            "error": "错误描述"
        }
    """
    temp_dir = None
    try:
        # 验证请求参数
        schema = ContourProcessSchema()
        try:
            args = schema.load(request.form)
        except ValidationError as e:
            return jsonify({"success": False, "error": "参数验证失败", "details": e.messages}), 400
        
        # 检查是否有图像文件
        if 'image' not in request.files:
            return jsonify({"success": False, "error": "缺少图像文件"}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({"success": False, "error": "未选择图像文件"}), 400
            
        json_file = request.files.get("json_data")

        # 验证文件类型
        allowed_image_extensions = {'jpg', 'jpeg', 'png', 'bmp'}
        if not allowed_file(image_file.filename, allowed_image_extensions):
            return jsonify({"success": False, "error": "不支持的图像格式，请使用jpg、jpeg、png或bmp格式"}), 400
            
        if json_file and not allowed_file(json_file.filename, {"json"}):
            return jsonify({"success": False, "error": "不支持的JSON文件格式，请使用json格式"}), 400
        
        # 创建临时目录保存文件
        temp_dir = tempfile.mkdtemp()
        try:
            # 保存图像文件
            image_filename = secure_filename(image_file.filename)
            image_path = os.path.join(temp_dir, image_filename)
            image_file.save(image_path)

            json_path = None
            if json_file:
                json_filename = secure_filename(json_file.filename)
                json_path = os.path.join(temp_dir, json_filename)
                json_file.save(json_path)
            
            # 获取整合轮廓服务实例
            contour_service = get_integrated_service()
            
            # 获取配置的置信度阈值
            # default_confidence = current_app.config.get("MODULE_DETECTION_CONFIG", {}).get("confidence_threshold", 0.5)

            # 处理图像并生成结果
            result = contour_service.identify_modules(
                image_path=image_path,
                json_file_path=json_path,
                debug=args.get('debug', False)
            )
            
            # 检查处理结果
            if not result.get('success'):
                return jsonify({
                    "success": False,
                    "error": result.get('error', '轮廓处理失败')
                }), 500
            
            return jsonify({
                "success": True,
                "data": result
            }), 200
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    except Exception as e:
        current_app.logger.error(f"轮廓处理失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": "轮廓处理失败", "details": str(e)}), 500
