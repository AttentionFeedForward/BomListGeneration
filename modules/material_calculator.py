#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能物料计算模块

实现板材排版计算、龙骨间距计算等智能计算功能
"""

import math
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from material_database import MaterialDatabase, MaterialSpec, CalculationResult, CalculationMethod


@dataclass
class LayoutCalculation:
    """排版计算结果"""
    quantity: int
    wastage_rate: float
    calculation_formula: str
    layout_description: str


class MaterialCalculator:
    """智能物料计算器"""
    
    def __init__(self, material_db: MaterialDatabase):
        """初始化计算器
        
        Args:
            material_db: 物料数据库实例
        """
        self.material_db = material_db
        self.default_wastage = 0.05  # 默认损耗率5%
    

    def calculate_material_quantity(self, material_code: str, area: float, 
                                  length: float = 0, width: float = 0,perimeter: float = 0,
                                  section: str = '地面', **kwargs) -> CalculationResult:
        """计算物料数量（使用数据库中的完整参数）
        
        Args:
            material_code: 物料编码
            area: 面积(m²)
            length: 长度(m)
            perimeter: 周长(m)
            section: 区域标识（天花、墙体、地面）
            **kwargs: 其他参数
            
        Returns:
            计算结果
        """
        # 直接使用数据库的计算方法
        return self.material_db.calculate_quantity(
            material_code=material_code,
            area=area,
            length=length,
            perimeter=perimeter,
            section=section,
            **kwargs
        )
    
    