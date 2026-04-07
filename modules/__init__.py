#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装修物料清单生成系统 - 模块包
"""

__version__ = "1.0.0"
__author__ = "AI Assistant"

# 导出主要模块 - 使用绝对导入避免相对导入问题
try:
    from llm.modules.config_manager import ConfigManager
    from llm.modules.data_processor import DataProcessor, ProcessedData, ContourData
    from llm.modules.material_database import MaterialDatabase, MaterialSpec, CalculationResult, CalculationMethod
    from llm.modules.material_calculator import MaterialCalculator
    from llm.modules.bom_generator import BOMGenerator
    from llm.modules.yolo_dimension_detect_predict import save_dimension_detection_results
    from llm.modules.dimension_matcher import DimensionMatcher
    from llm.modules.contour_generate import ContourGenerator
except ImportError:
    # 如果绝对导入失败，尝试相对导入
    from .config_manager import ConfigManager
    from .data_processor import DataProcessor, ProcessedData, ContourData
    from .material_database import MaterialDatabase, MaterialSpec, CalculationResult, CalculationMethod
    from .material_calculator import MaterialCalculator
    from .bom_generator import BOMGenerator
    from .yolo_dimension_detect_predict import save_dimension_detection_results
    from .dimension_matcher import DimensionMatcher
    from .contour_generate import ContourGenerator


__all__ = [
    'ConfigManager',
    'DataProcessor', 
    'ProcessedData',
    'ContourData',
    'MaterialDatabase',
    'MaterialSpec', 
    'CalculationResult',
    'CalculationMethod',
    'MaterialCalculator',
    'BOMGenerator',
    'save_dimension_detection_results',
    'DimensionMatcher',
    'ContourGenerator'
]