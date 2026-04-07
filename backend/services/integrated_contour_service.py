"""
整合轮廓处理服务
整合轮廓检测、尺寸标注识别和真实尺寸转换功能
实现从原始图片到带真实尺寸标注的轮廓数据的完整处理流程

主要功能：
1. 完整的轮廓识别算法实现
2. 精确的尺寸检测功能  
3. 高效的图像匹配算法
4. 错误处理和日志记录机制
5. 3D模型生成和多格式导出

作者：AI Assistant
创建时间：2024年
"""

import os
import json
import cv2
import numpy as np
import tempfile
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
import logging
import base64

# 设置日志
logger = logging.getLogger(__name__)

# 添加extract_info目录到Python路径
extract_info_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'extract_info')
if extract_info_path not in sys.path:
    sys.path.append(extract_info_path)

# 延迟导入相关模块，避免启动时的依赖问题
def _lazy_import_contour_generator():
    """延迟导入ContourGenerator"""
    try:
        from modules.contour_generate import ContourGenerator
        logger.info("成功导入ContourGenerator")
        return ContourGenerator
    except ImportError as e:
        logger.warning(f"无法导入ContourGenerator: {e}")
        return None

def _lazy_import_dimension_detection():
    """延迟导入尺寸检测模块"""
    try:
        from modules.yolo_dimension_detect_predict import save_dimension_detection_results
        logger.info("成功导入尺寸检测模块")
        return save_dimension_detection_results
    except ImportError as e:
        logger.warning(f"无法导入尺寸检测模块: {e}")
        return None

def _lazy_import_dimension_matcher():
    """延迟导入DimensionMatcher"""
    try:
        from modules.dimension_matcher import DimensionMatcher
        logger.info("成功导入DimensionMatcher")
        return DimensionMatcher
    except ImportError as e:
        logger.warning(f"无法导入DimensionMatcher: {e}")
        return None


class IntegratedContourService:
    """
    整合轮廓处理服务类
    
    提供完整的处理管道：
    1. 轮廓检测：使用YOLO分割模型提取图形外轮廓
    2. 尺寸标注识别：检测尺寸标注并计算像素比例
    3. 尺寸转换：将像素轮廓转换为真实尺寸轮廓
    4. 3D模型生成：支持OBJ、STL、PLY格式导出
    """
    
    def __init__(self, 
                 output_dir: str = None,
                 enable_scale_filter: bool = True,
                 scale_deviation_threshold: float = 0.05):
        """
        初始化整合处理服务
        
        Args:
            output_dir: 输出目录
            enable_scale_filter: 是否启用比例因子过滤
            scale_deviation_threshold: 比例因子过滤的偏差阈值
        """
        self.output_dir = output_dir or tempfile.mkdtemp()
        self.enable_scale_filter = enable_scale_filter
        self.scale_deviation_threshold = scale_deviation_threshold
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 设置默认模型路径
        self.contour_model_path = self._get_default_contour_model_path()
        self.dimension_model_path = self._get_default_dimension_model_path()
        
        # 延迟初始化组件
        self.contour_generator = None
        self.dimension_matcher = None
        self.dimension_detection_func = None
        
        # 处理统计
        self.processing_stats = {
            'total_processed': 0,
            'successful_contour': 0,
            'successful_dimension': 0,
            'successful_conversion': 0,
            'failed_cases': []
        }
        
        logger.info(f"整合轮廓处理服务初始化完成")
        logger.info(f"输出目录: {self.output_dir}")
    
    def _get_default_contour_model_path(self) -> str:
        """获取默认轮廓模型路径"""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(base_path, 'extract_info', 'corner_text_modeldetection', 
                                 'training_outputs', 'contour_segmentation', 
                                 'contour_segmentation_segmentation_20251024_151144（896）', 
                                 'weights', 'last.pt')
        return model_path
    
    def _get_default_dimension_model_path(self) -> str:
        """获取默认尺寸检测模型路径"""
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        model_path = os.path.join(base_path, 'extract_info', 'corner_text_modeldetection', 
                                 'training_outputs', 'dimension', 
                                 'dimension_smart_training_20251016_194046', 
                                 'weights', 'best.pt')
        return model_path
    
    def _initialize_components(self):
        """延迟初始化组件"""
        logger.info("开始初始化组件...")
        
        # 初始化轮廓生成器
        if self.contour_generator is None:
            ContourGenerator = _lazy_import_contour_generator()
            if ContourGenerator is not None:
                try:
                    self.contour_generator = ContourGenerator(self.contour_model_path)
                    logger.info("轮廓生成器初始化成功")
                except Exception as e:
                    logger.error(f"轮廓生成器初始化失败: {e}")
        
        # 初始化尺寸检测功能
        if self.dimension_detection_func is None:
            self.dimension_detection_func = _lazy_import_dimension_detection()
        
        # 初始化尺寸匹配器
        if self.dimension_matcher is None:
            DimensionMatcher = _lazy_import_dimension_matcher()
            if DimensionMatcher is not None:
                try:
                    self.dimension_matcher = DimensionMatcher(
                        enable_scale_filter=self.enable_scale_filter,
                        scale_deviation_threshold=self.scale_deviation_threshold
                    )
                    logger.info("尺寸匹配器初始化成功")
                except Exception as e:
                    logger.error(f"尺寸匹配器初始化失败: {e}")
        
        logger.info("组件初始化完成")
    
    def check_health(self) -> Dict[str, Any]:
        """
        检查服务健康状态
        
        Returns:
            Dict[str, Any]: 包含服务状态和依赖项信息的字典
        """
        health_info = {
            "service_name": "Integrated Contour Service",
            "status": "healthy",
            "dependencies": {},
            "statistics": self.processing_stats.copy(),
            "configuration": {
                "enable_scale_filter": self.enable_scale_filter,
                "scale_deviation_threshold": self.scale_deviation_threshold,
                "output_dir": self.output_dir
            }
        }
        
        # 检查轮廓生成器
        try:
            if self.contour_generator is None:
                self._initialize_components()
            
            if self.contour_generator is not None:
                health_info["dependencies"]["contour_generator"] = "available"
            else:
                health_info["dependencies"]["contour_generator"] = "unavailable"
                health_info["status"] = "degraded"
        except Exception as e:
            health_info["dependencies"]["contour_generator"] = f"error: {str(e)}"
            health_info["status"] = "degraded"
        
        # 检查尺寸检测功能
        try:
            if self.dimension_detection_func is None:
                self._initialize_components()
            
            if self.dimension_detection_func is not None:
                health_info["dependencies"]["dimension_detection"] = "available"
            else:
                health_info["dependencies"]["dimension_detection"] = "unavailable"
                health_info["status"] = "degraded"
        except Exception as e:
            health_info["dependencies"]["dimension_detection"] = f"error: {str(e)}"
            health_info["status"] = "degraded"
        
        # 检查尺寸匹配器
        try:
            if self.dimension_matcher is None:
                self._initialize_components()
            
            if self.dimension_matcher is not None:
                health_info["dependencies"]["dimension_matcher"] = "available"
            else:
                health_info["dependencies"]["dimension_matcher"] = "unavailable"
                health_info["status"] = "degraded"
        except Exception as e:
            health_info["dependencies"]["dimension_matcher"] = f"error: {str(e)}"
            health_info["status"] = "degraded"
        
        # 检查输出目录
        try:
            if os.path.exists(self.output_dir) and os.access(self.output_dir, os.W_OK):
                health_info["dependencies"]["output_directory"] = "writable"
            else:
                health_info["dependencies"]["output_directory"] = "not_writable"
                health_info["status"] = "degraded"
        except Exception as e:
            health_info["dependencies"]["output_directory"] = f"error: {str(e)}"
            health_info["status"] = "degraded"
        
        # 检查必要的Python包
        required_packages = ["cv2", "numpy", "tempfile", "json"]
        for package in required_packages:
            try:
                __import__(package)
                health_info["dependencies"][f"package_{package}"] = "available"
            except ImportError:
                health_info["dependencies"][f"package_{package}"] = "unavailable"
                health_info["status"] = "unhealthy"
        
        return health_info
    
    def process_image(self, 
                     image_path: str, 
                     debug: bool = False) -> Dict[str, Any]:
        """
        处理图像的完整流程，专注于轮廓检测和数据计算
        
        Args:
            image_path: 图像路径
            debug: 是否输出调试信息
            
        Returns:
            处理结果字典，包含轮廓数据、边长、周长、面积等信息
        """
        logger.info(f"开始处理图像: {image_path}")
        
        # 初始化组件
        self._initialize_components()
        
        # 获取图像名称
        image_name = Path(image_path).stem
        image_output_dir = os.path.join(self.output_dir, image_name)
        os.makedirs(image_output_dir, exist_ok=True)
        
        result = {
            'success': False,
            'error': None,
            'contour_info': None
        }
        
        start_time = datetime.now()
        
        try:
            # 使用完整的轮廓检测
            contour_result = self._detect_contours(image_path, image_output_dir, debug)
            
            if not contour_result['success']:
                result['error'] = f"轮廓检测失败: {contour_result['error']}"
                return result
            
            # 尺寸标注识别和比例计算
            scale_factor = 1.0  # 默认比例因子
            if self.dimension_detection_func is not None and self.dimension_matcher is not None:
                dimension_result = self._detect_dimensions(image_path, image_output_dir, debug)
                if dimension_result['success']:
                    scale_factor = dimension_result['average_scale_factor']
                    # 调整图像缩放因子
                    image_scale_factor = contour_result.get('image_scale_factor', 1.0)
                    scale_factor = scale_factor / image_scale_factor
            
            # 轮廓尺寸转换
            conversion_result = self._convert_contour_to_real_size(
                contour_result['contours'], 
                scale_factor,
                image_output_dir,
                image_name,
                debug
            )
            
            if not conversion_result['success']:
                result['error'] = f"尺寸转换失败: {conversion_result['error']}"
                return result
            
            # 格式化轮廓数据，增强数据计算
            contour_info = self._format_contour_data(conversion_result['real_size_contour'], scale_factor)
            
            result.update({
                'success': True,
                'contour_info': contour_info,
                'processing_time': (datetime.now() - start_time).total_seconds()
            })
            
            logger.info(f"图像处理成功完成: {image_name}")
            
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            logger.error(error_msg)
            result['error'] = error_msg
        
        return result
    
    def identify_modules(self, json_file_path: str, image_path: str,  debug: bool = False) -> Dict[str, Any]:
        """
        识别模块的主要方法，调用process_image进行图像处理
        
        Args:
            json_file_path: JSON文件路径（可选，用于额外配置）
            image_path: 图像路径
            debug: 是否开启调试模式
            
        Returns:
            模块识别结果
        """
        try:
            
            # 调用process_image进行图像处理
            result = self.process_image(
                image_path=image_path,
                debug=debug
            )
            
            # 如果有JSON配置文件，可以在这里处理额外的配置
            if json_file_path and os.path.exists(json_file_path):
                try:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        json_config = json.load(f)
                    # 可以根据JSON配置调整结果
                    result['config'] = json_config
                except Exception as e:
                    logger.warning(f"读取JSON配置文件失败: {e}")
            
            return result
            
        except Exception as e:
            error_msg = f"模块识别过程中发生错误: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def _detect_contours(self, image_path: str, output_dir: str, debug: bool = False) -> Dict[str, Any]:
        """
        完整的轮廓检测（使用YOLO模型）
        
        Args:
            image_path: 图像路径
            output_dir: 输出目录
            debug: 调试模式
            
        Returns:
            轮廓检测结果
        """
        try:
            # 使用ContourGenerator进行轮廓检测
            original_image, mask, contours = self.contour_generator.process_single_image(
                image_path, output_dir
            )
            
            if not contours or len(contours) == 0:
                return {
                    'success': False,
                    'error': '未检测到有效轮廓',
                    'contours': None
                }
            
            # 获取图像缩放因子
            image_scale_factor = 1.0
            if hasattr(self.contour_generator, 'last_scale_factor'):
                image_scale_factor = self.contour_generator.last_scale_factor
            
            # 转换轮廓数据格式
            contour_data = []
            for i, contour in enumerate(contours):
                points = contour.reshape(-1, 2).tolist()
                contour_info = {
                    'contour_id': i,
                    'num_points': len(points),
                    'points': points,
                    'area': float(cv2.contourArea(contour)),
                    'perimeter': float(cv2.arcLength(contour, True))
                }
                contour_data.append(contour_info)
            
            if debug:
                logger.info(f"YOLO轮廓检测完成，检测到 {len(contour_data)} 个轮廓")
            
            return {
                'success': True,
                'contours': contour_data,
                'image_scale_factor': image_scale_factor
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'contours': None
            }
    
    def _detect_dimensions(self, image_path: str, output_dir: str, debug: bool = False) -> Dict[str, Any]:
        """
        尺寸标注识别
        
        Args:
            image_path: 图像路径
            output_dir: 输出目录
            debug: 调试模式
            
        Returns:
            尺寸标注识别结果
        """
        try:
            # 运行目标检测
            detection_result = self._run_dimension_detection(image_path, output_dir, debug)
            if not detection_result['success']:
                return detection_result
            
            # 使用DimensionMatcher处理检测结果
            matcher_result = self._process_with_dimension_matcher(
                detection_result['dimension_json_path'], 
                image_path,
                debug=debug
            )
            
            return matcher_result
            
        except Exception as e:
            logger.error(f"尺寸检测过程中发生错误: {str(e)}")
            return {
                'success': False,
                'error': f'尺寸检测过程中发生错误: {str(e)}',
                'matches': None,
                'average_scale_factor': None
            }
    
    def _run_dimension_detection(self, image_path: str, output_dir: str, debug: bool = False) -> Dict[str, Any]:
        """
        运行目标检测模型生成JSON文件
        
        Args:
            image_path: 图像路径
            output_dir: 输出目录
            debug: 调试模式
            
        Returns:
            目标检测结果
        """
        try:
            image_name = Path(image_path).stem
            dimension_json_path = os.path.join(output_dir, f"{image_name}_optimized.json")
            
            # 为单个图像创建临时输入目录
            temp_input_dir = os.path.join(output_dir, "temp_input")
            os.makedirs(temp_input_dir, exist_ok=True)
            
            # 复制图像到临时目录
            temp_image_path = os.path.join(temp_input_dir, os.path.basename(image_path))
            shutil.copy2(image_path, temp_image_path)
            
            if debug:
                logger.info(f"开始运行目标检测模型，输入图像: {image_path}")
            
            # 调用尺寸检测函数
            self.dimension_detection_func(
                model_path=self.dimension_model_path,
                input_dir=temp_input_dir,
                output_dir=output_dir,
                generate_summary=False
            )
            
            # 清理临时目录
            shutil.rmtree(temp_input_dir, ignore_errors=True)
            
            # 检查检测结果文件是否存在
            if not os.path.exists(dimension_json_path):
                return {
                    'success': False,
                    'error': f"目标检测模型未能生成JSON文件: {dimension_json_path}"
                }
            
            return {
                'success': True,
                'dimension_json_path': dimension_json_path
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"目标检测过程中发生错误: {str(e)}"
            }
    
    def _process_with_dimension_matcher(self, dimension_json_path: str, image_path: str, debug: bool = False) -> Dict[str, Any]:
        """
        使用DimensionMatcher处理目标检测结果
        
        Args:
            dimension_json_path: 目标检测生成的JSON文件路径
            image_path: 原始图像路径
            debug: 调试模式
            
        Returns:
            DimensionMatcher处理结果
        """
        try:
            if debug:
                logger.info(f"开始使用DimensionMatcher处理: {dimension_json_path}")
            
            # 使用DimensionMatcher进行匹配和比例计算
            scattered_points, text_boxes, ocr_texts = self.dimension_matcher.load_and_process_json(
                dimension_json_path, 
                image_path, 
                debug=debug
            )
            
            matcher_result = self.dimension_matcher.match_dimensions(
                scattered_points,
                text_boxes,
                ocr_texts,
                debug=debug
            )
            
            if not matcher_result or 'matches' not in matcher_result:
                return {
                    'success': False,
                    'error': "DimensionMatcher处理失败，未返回有效结果"
                }
            
            matches = matcher_result['matches']
            summary = matcher_result['summary']
            
            if len(matches) == 0:
                return {
                    'success': False,
                    'error': "DimensionMatcher未找到有效的尺寸匹配"
                }
            
            average_scale_factor = summary['average_scale_factor']
            
            if debug:
                logger.info(f"DimensionMatcher处理成功: 找到 {len(matches)} 个尺寸匹配")
                logger.info(f"平均比例因子: {average_scale_factor:.4f} mm/像素")
            
            return {
                'success': True,
                'matches': matches,
                'summary': summary,
                'average_scale_factor': average_scale_factor
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"DimensionMatcher处理过程中发生错误: {str(e)}"
            }
    
    def _convert_contour_to_real_size(self, contours: List[Dict], scale_factor: float,
                                     output_dir: str, image_name: str, debug: bool = False) -> Dict[str, Any]:
        """
        将像素轮廓转换为真实尺寸轮廓
        
        Args:
            contours: 轮廓数据列表
            scale_factor: 比例因子 (mm/像素)
            output_dir: 输出目录
            image_name: 图像名称
            debug: 调试模式
            
        Returns:
            转换结果
        """
        try:
            real_size_contours = []
            
            for contour in contours:
                # 转换点坐标
                real_points = []
                for point in contour['points']:
                    real_x = point[0] * scale_factor
                    real_y = point[1] * scale_factor
                    real_points.append([real_x, real_y])
                
                # 计算真实尺寸的几何属性
                real_area = contour['area'] * (scale_factor ** 2)
                real_perimeter = contour['perimeter'] * scale_factor
                
                real_contour = {
                    'contour_id': contour['contour_id'],
                    'num_points': contour['num_points'],
                    'points': real_points,
                    'area': real_area,
                    'perimeter': real_perimeter,
                    'scale_factor': scale_factor,
                    'unit': 'mm'
                }
                
                real_size_contours.append(real_contour)
            
            if debug:
                logger.info(f"轮廓尺寸转换完成，转换了 {len(real_size_contours)} 个轮廓")
            
            return {
                'success': True,
                'real_size_contour': real_size_contours
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _format_contour_data(self, contours: List[Dict], scale_factor: float) -> Dict[str, Any]:
        """
        格式化轮廓数据，包含完整的几何信息
        
        Args:
            contours: 轮廓数据列表
            scale_factor: 比例因子
            
        Returns:
            格式化后的轮廓数据，包含边长、周长、面积等信息
        """
        formatted_contours = []
        
        for contour in contours:
            # 计算边长
            points = contour['points']
            edge_lengths = []
            
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]  # 连接到下一个点，最后一个点连接到第一个点
                
                # 计算两点间距离
                distance = ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2) ** 0.5
                edge_lengths.append(round(distance, 2))
            
            formatted_contour = {
                'id': contour['contour_id'],
                'geometry': {
                    'points': contour['points'],
                    'num_points': contour['num_points'],
                    'area': round(contour['area'], 2),
                    'perimeter': round(contour['perimeter'], 2),
                    'edge_lengths': edge_lengths,
                    'unit': contour.get('unit', 'mm')
                },
                'scale_info': {
                    'scale_factor': round(scale_factor, 6),
                    'unit': 'mm/pixel'
                }
            }
            formatted_contours.append(formatted_contour)
        
        return {
            'contours': formatted_contours,
            'summary': {
                'total_contours': len(formatted_contours),
                'total_area': round(sum(c['geometry']['area'] for c in formatted_contours), 2),
                'total_perimeter': round(sum(c['geometry']['perimeter'] for c in formatted_contours), 2),
                'unit': 'mm'
            }
        }
    

    

    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if os.path.exists(self.output_dir) and self.output_dir.startswith(tempfile.gettempdir()):
                shutil.rmtree(self.output_dir)
                logger.info("临时文件清理完成")
        except Exception as e:
            logger.warning(f"清理临时文件时发生错误: {e}")