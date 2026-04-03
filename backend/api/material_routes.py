#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料计算相关API路由

提供物料清单生成等功能的REST API接口
"""

from flask import Blueprint, request, jsonify
from typing import Dict, Any
import traceback
import time
from datetime import datetime

import sys
import os

# 添加services目录到Python路径
backend_path = os.path.dirname(os.path.dirname(__file__))
services_path = os.path.join(backend_path, 'services')
sys.path.insert(0, services_path)

try:
    from material_calculation_service import MaterialCalculationService
except ImportError as e:
    print(f"Error importing MaterialCalculationService: {e}")
    MaterialCalculationService = None

# 创建蓝图
material_bp = Blueprint('material', __name__, url_prefix='/api/material')

# 初始化服务
material_service = None
if MaterialCalculationService:
    try:
        material_service = MaterialCalculationService()
    except Exception as e:
        print(f"Error initializing MaterialCalculationService: {e}")


@material_bp.route('/generate-bom', methods=['POST'])
def generate_material_bom():
    """
    生成物料清单
    
    请求体格式:
    {
        "module_data": {
            "height": number,        // 模块高度(mm)
            "floor_area": number,    // 地面面积(m²)
            "wall_area": number,     // 墙面面积(m²)
            "ceiling_area": number   // 天花面积(m²)
        },
        "construction_practices": {
            "ceiling-structure": "选项1",
            "ceiling-finish": "选项2",
            "wall-structure": "选项3",
            "wall-finish": "选项4",
            "floor-structure": "选项5",
            "floor-finish": "选项6"
        }
    }
    
    返回格式:
    {
        "success": true,
        "data": {
            "items": [...],
            "summary": {...}
        },
        "message": "BOM生成成功"
    }
    """
    try:
        start_time = time.time()
        
        # 检查服务是否可用
        if not material_service:
            return jsonify({
                'success': False,
                'message': '材料计算服务不可用',
                'error': 'SERVICE_UNAVAILABLE'
            }), 503
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空',
                'error': 'INVALID_REQUEST_DATA'
            }), 400
        
        # 验证必需字段
        required_fields = ['module_data', 'construction_practices']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'缺少必需字段: {field}',
                    'error': 'MISSING_REQUIRED_FIELD'
                }), 400
        
        # 验证模块数据字段
        module_data = data['module_data']
        required_module_fields = ['height', 'floor_area', 'wall_area', 'ceiling_area']
        for field in required_module_fields:
            if field not in module_data:
                return jsonify({
                    'success': False,
                    'message': f'模块数据中缺少必需字段: {field}',
                    'error': 'MISSING_MODULE_FIELD'
                }), 400
        
        # 调用服务层生成BOM
        result = material_service.generate_material_bom(
            module_data=module_data,
            construction_practices=data['construction_practices'],
            project_type=data.get('project_type', '住宅'),
            room_type=data.get('room_type', '标准房间')
        )
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 添加处理信息到结果中
        if result.get('success') and 'data' in result:
            result['data']['processing_info'] = {
                'timestamp': datetime.now().isoformat(),
                'processing_time': processing_time
            }
        
        # 根据服务返回结果确定HTTP状态码
        if result.get('success', False):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e),
            'error': 'VALIDATION_ERROR'
        }), 400
        
    except Exception as e:
        # 记录详细错误信息
        error_trace = traceback.format_exc()
        print(f"生成物料清单时发生错误: {error_trace}")
        
        return jsonify({
            'success': False,
            'message': '服务器内部错误，请稍后重试',
            'error': 'INTERNAL_SERVER_ERROR',
            'details': str(e) if data.get('debug', False) else None
        }), 500


@material_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    try:
        if material_service:
            # 检查服务状态
            status = material_service.get_service_status()
            
            return jsonify({
                'success': True,
                'data': {
                    'service': 'material_calculation',
                    'status': status.get('status', 'unknown'),
                    'timestamp': datetime.now().isoformat(),
                    'details': status
                }
            })
        else:
            return jsonify({
                'success': False,
                'data': {
                    'service': 'material_calculation',
                    'status': 'unavailable',
                    'timestamp': datetime.now().isoformat(),
                    'error': '材料计算服务未初始化'
                }
            }), 503
        
    except Exception as e:
        return jsonify({
            'success': False,
            'data': {
                'service': 'material_calculation',
                'status': 'unhealthy',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }
        }), 500


# 错误处理器
@material_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '接口不存在',
        'error': 'NOT_FOUND'
    }), 404


@material_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'message': '请求方法不被允许',
        'error': 'METHOD_NOT_ALLOWED'
    }), 405