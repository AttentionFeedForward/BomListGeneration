#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理模块

负责处理构造做法配置和用户输入数据，
为BOM生成提供标准化的数据结构。
支持从图纸解析轮廓数据计算面积。
"""

import json
import math
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ContourData:
    """轮廓数据类（来自图纸解析阶段）"""
    contour_area: float      # 轮廓面积(m²)
    contour_perimeter: float # 轮廓周长(m)
    module_height: float     # 模块高度(m)
    scale_factor: float      # 比例因子(mm/像素)
    pixel_points: List[List[float]]  # 像素坐标点
    real_points: List[List[float]]   # 真实坐标点(mm)
    
    @property
    def floor_area(self) -> float:
        """地面面积 = 轮廓面积"""
        return self.contour_area
    
    @property
    def ceiling_area(self) -> float:
        """天花面积 = 轮廓面积"""
        return self.contour_area
    
    @property
    def wall_area(self) -> float:
        """墙面面积 = 轮廓周长 × 模块高度"""
        return self.contour_perimeter * self.module_height
    
    @property
    def volume(self) -> float:
        """体积 = 轮廓面积 × 模块高度"""
        return self.contour_area * self.module_height


@dataclass
class BoxDimensions:
    """箱体尺寸数据类（传统方式输入）"""
    length: float  # 长度(m)
    width: float   # 宽度(m)
    height: float  # 高度(m)
    
    @property
    def floor_area(self) -> float:
        """地面面积"""
        return self.length * self.width
    
    @property
    def ceiling_area(self) -> float:
        """天花面积"""
        return self.length * self.width
    
    @property
    def wall_area(self) -> float:
        """墙体面积（不含门窗）"""
        return 2 * (self.length + self.width) * self.height
    
    @property
    def volume(self) -> float:
        """体积"""
        return self.length * self.width * self.height


@dataclass
class AreaInfo:
    """区域信息数据类"""
    area: float           # 面积(m²)
    length: float         # 长度(m)
    width: float          # 宽度(m)
    perimeter: float      # 周长(m)
    thickness: float = 0  # 厚度(m)

@dataclass
class ConstructionLayer:
    """构造层次数据类"""
    base_layer: str       # 基层构造做法
    surface_layer: str    # 饰面层构造做法
    area_info: AreaInfo   # 区域尺寸信息

@dataclass
class ConstructionMethods:
    """构造做法数据类（按天地墙分类）"""
    ceiling: ConstructionLayer    # 天花构造
    wall: ConstructionLayer       # 墙体构造
    floor: ConstructionLayer      # 地面构造


@dataclass
class ProcessedData:
    """处理后的数据"""
    dimensions: Optional[BoxDimensions] = None      # 传统尺寸输入（可选）
    contour_data: Optional[ContourData] = None      # 轮廓数据输入（可选）
    construction_methods: Optional[ConstructionMethods] = None
    areas: Optional[Dict[str, float]] = None
    construction_details: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @property
    def effective_dimensions(self):
        """获取有效的尺寸数据（优先使用轮廓数据）"""
        return self.contour_data if self.contour_data else self.dimensions


class DataProcessor:
    """数据处理器"""
    
    def __init__(self, config_manager):
        """初始化数据处理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.construction_config = self._load_construction_config()
        self.wastage_rate = config_manager.get('defaults.wastage_rate', 0.1)
    
    def _load_construction_config(self) -> Dict[str, Any]:
        """加载构造做法配置 (可选)
        
        Returns:
            构造做法配置字典
        """   
        try:
            config_path = self.config.get_paths()['construction_methods']
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    
    def get_construction_options(self) -> Dict[str, List[str]]:
        """获取构造做法选项
        
        Returns:
            构造做法选项字典
        """
        return self.construction_config.copy()
    
    def process_contour_input(self, contour_result: Dict[str, Any], 
                             module_height: float,
                             construction_dict: Dict[str, str]) -> ProcessedData:
        """处理轮廓数据输入（来自图纸解析阶段）
        
        Args:
            contour_result: 轮廓处理结果字典
            module_height: 用户指定的模块高度(m)
            construction_dict: 构造做法选择字典
            
        Returns:
            处理后的数据对象
        """
        # 从轮廓结果中提取数据
        real_size_contour = contour_result.get('real_size_contour', [])
        if not real_size_contour:
            raise ValueError("轮廓数据中缺少真实尺寸轮廓信息")
        
        # 获取第一个轮廓的数据（假设只有一个主要轮廓）
        main_contour = real_size_contour[0]
        
        # 提取轮廓面积和周长（单位转换：mm² -> m², mm -> m）
        contour_area_mm2 = main_contour.get('area', 0)
        contour_perimeter_mm = main_contour.get('perimeter', 0)
        
        contour_area_m2 = contour_area_mm2 / 1_000_000  # mm² -> m²
        contour_perimeter_m = contour_perimeter_mm / 1000  # mm -> m
        
        # 获取比例因子和坐标点
        scale_factor = contour_result.get('scale_factor', 1.0)
        
        # 获取像素坐标和真实坐标
        pixel_contour = contour_result.get('contour_data', [])
        pixel_points = pixel_contour[0].get('points', []) if pixel_contour else []
        real_points = main_contour.get('points', [])
        
        # 创建轮廓数据对象
        contour_data = ContourData(
            contour_area=contour_area_m2,
            contour_perimeter=contour_perimeter_m,
            module_height=module_height,
            scale_factor=scale_factor,
            pixel_points=pixel_points,
            real_points=real_points
        )
        
        # 创建各区域的面积信息（基于轮廓数据）
        ceiling_area_info = AreaInfo(
            area=contour_data.ceiling_area,
            length=0,  # 不规则形状，长宽不适用
            width=0,
            perimeter=contour_data.contour_perimeter
        )
        
        wall_area_info = AreaInfo(
            area=contour_data.wall_area,
            length=contour_data.contour_perimeter,  # 墙体总长度
            width=module_height,  # 墙体高度
            perimeter=2 * (contour_data.contour_perimeter + 2 * module_height)  # 墙体总周长
        )
        
        floor_area_info = AreaInfo(
            area=contour_data.floor_area,
            length=0,  # 不规则形状，长宽不适用
            width=0,
            perimeter=contour_data.contour_perimeter
        )
        
        # 创建构造做法对象
        construction_methods = ConstructionMethods(
            ceiling=ConstructionLayer(
                base_layer=construction_dict.get('天花基层', ''),
                surface_layer=construction_dict.get('天花饰面层', ''),
                area_info=ceiling_area_info
            ),
            wall=ConstructionLayer(
                base_layer=construction_dict.get('墙体基层', ''),
                surface_layer=construction_dict.get('墙体饰面层', ''),
                area_info=wall_area_info
            ),
            floor=ConstructionLayer(
                base_layer=construction_dict.get('地面基层', ''),
                surface_layer=construction_dict.get('地面饰面层', ''),
                area_info=floor_area_info
            )
        )
        
        # 计算各部位面积
        areas = self._calculate_areas_from_contour(contour_data)
        
        # 获取构造做法详细信息
        construction_details = self._get_construction_details(construction_methods)
        
        # 生成元数据
        metadata = {
            'wastage_rate': self.wastage_rate,
            'calculation_time': self._get_current_time(),
            'data_source': 'contour_analysis',  # 标识数据来源
            'scale_factor': scale_factor,
            'module_height': module_height,
            'contour_area_mm2': contour_area_mm2,
            'contour_perimeter_mm': contour_perimeter_mm,
            'complexity_level': self._assess_complexity(construction_methods)
        }
        
        return ProcessedData(
            contour_data=contour_data,
            construction_methods=construction_methods,
            areas=areas,
            construction_details=construction_details,
            metadata=metadata
        )

    def process_input(self, dimensions_dict: Dict[str, float], 
                     construction_dict: Dict[str, str]) -> ProcessedData:
        """处理用户输入数据
        
        Args:
            dimensions_dict: 尺寸数据字典
            construction_dict: 构造做法选择字典
            
        Returns:
            处理后的数据对象
        """
        # 创建尺寸对象
        dimensions = BoxDimensions(
            length=dimensions_dict.get('length', 6.0),
            width=dimensions_dict.get('width', 3.0),
            height=dimensions_dict.get('height', 2.8)
        )
        
        # 创建各区域的面积信息
        ceiling_area_info = AreaInfo(
            area=dimensions.ceiling_area,
            length=dimensions.length,
            width=dimensions.width,
            perimeter=2 * (dimensions.length + dimensions.width)
        )
        
        wall_area_info = AreaInfo(
            area=dimensions.wall_area,
            length=2 * (dimensions.length + dimensions.width),  # 墙体总长度
            width=dimensions.height,  # 墙体高度
            perimeter=2 * (2 * (dimensions.length + dimensions.width) + 4 * dimensions.height)  # 墙体总周长
        )
        
        floor_area_info = AreaInfo(
            area=dimensions.floor_area,
            length=dimensions.length,
            width=dimensions.width,
            perimeter=2 * (dimensions.length + dimensions.width)
        )
        
        # 创建构造做法对象
        construction_methods = ConstructionMethods(
            ceiling=ConstructionLayer(
                base_layer=construction_dict.get('天花基层', ''),
                surface_layer=construction_dict.get('天花饰面层', ''),
                area_info=ceiling_area_info
            ),
            wall=ConstructionLayer(
                base_layer=construction_dict.get('墙体基层', ''),
                surface_layer=construction_dict.get('墙体饰面层', ''),
                area_info=wall_area_info
            ),
            floor=ConstructionLayer(
                base_layer=construction_dict.get('地面基层', ''),
                surface_layer=construction_dict.get('地面饰面层', ''),
                area_info=floor_area_info
            )
        )
        
        # 计算各部位面积
        areas = self._calculate_areas(dimensions)
        
        # 获取构造做法详细信息
        construction_details = self._get_construction_details(construction_methods)
        
        # 生成元数据
        metadata = {
            'wastage_rate': self.wastage_rate,
            'calculation_time': self._get_current_time(),
            'room_type': self._determine_room_type(dimensions),
            'complexity_level': self._assess_complexity(construction_methods)
        }
        
        return ProcessedData(
            dimensions=dimensions,
            construction_methods=construction_methods,
            areas=areas,
            construction_details=construction_details,
            metadata=metadata
        )
    
    def _calculate_areas(self, dimensions: BoxDimensions) -> Dict[str, float]:
        """计算各部位面积（传统方式）
        
        Args:
            dimensions: 箱体尺寸
            
        Returns:
            面积字典
        """
        return {
            'floor_area': dimensions.floor_area,
            'ceiling_area': dimensions.ceiling_area,
            'wall_area': dimensions.wall_area,
            'total_area': dimensions.floor_area + dimensions.ceiling_area + dimensions.wall_area,
            'perimeter': 2 * (dimensions.length + dimensions.width),
            'volume': dimensions.volume
        }
    
    def _calculate_areas_from_contour(self, contour_data: ContourData) -> Dict[str, float]:
        """计算各部位面积（基于轮廓数据）
        
        Args:
            contour_data: 轮廓数据
            
        Returns:
            面积字典
        """
        return {
            'floor_area': contour_data.floor_area,
            'ceiling_area': contour_data.ceiling_area,
            'wall_area': contour_data.wall_area,
            'total_area': contour_data.floor_area + contour_data.ceiling_area + contour_data.wall_area,
            'perimeter': contour_data.contour_perimeter,
            'volume': contour_data.volume
        }
    
    def _get_construction_details(self, methods: ConstructionMethods) -> Dict[str, str]:
        """获取构造做法详细信息
        
        Args:
            methods: 构造做法对象
            
        Returns:
            构造做法详细信息字典
        """
        return {
            '天花基层': methods.ceiling.base_layer,
            '天花饰面层': methods.ceiling.surface_layer,
            '墙体基层': methods.wall.base_layer,
            '墙体饰面层': methods.wall.surface_layer,
            '地面基层': methods.floor.base_layer,
            '地面饰面层': methods.floor.surface_layer
        }
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串
        
        Returns:
            时间字符串
        """
        from datetime import datetime
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _determine_room_type(self, dimensions: BoxDimensions) -> str:
        """判断房间类型
        
        Args:
            dimensions: 箱体尺寸
            
        Returns:
            房间类型
        """
        area = dimensions.floor_area
        
        if area < 10:
            return "小型房间"
        elif area < 30:
            return "中型房间"
        else:
            return "大型房间"
    
    def _assess_complexity(self, methods: ConstructionMethods) -> str:
        """评估构造复杂度
        
        Args:
            methods: 构造做法对象
            
        Returns:
            复杂度等级
        """
        # 简单的复杂度评估逻辑
        custom_count = sum(1 for method in [methods.ceiling.base_layer, methods.ceiling.surface_layer,
                          methods.wall.base_layer, methods.wall.surface_layer, 
                          methods.floor.base_layer, methods.floor.surface_layer] 
                          if '自定义' in method)
        
        if custom_count >= 3:
            return "高"
        elif custom_count >= 1:
            return "中"
        else:
            return "低"
    
    def format_for_ai(self, data: ProcessedData) -> str:
        """格式化数据供AI处理
        
        Args:
            data: 处理后的数据
            
        Returns:
            格式化的文本描述
        """
        return f"""
项目信息：
- 房间尺寸：长{data.dimensions.length}m × 宽{data.dimensions.width}m × 高{data.dimensions.height}m
- 地面面积：{data.areas['floor_area']:.2f}m²
- 天花面积：{data.areas['ceiling_area']:.2f}m²
- 墙体面积：{data.areas['wall_area']:.2f}m²
- 房间周长：{data.areas['perimeter']:.2f}m
- 房间体积：{data.areas['volume']:.2f}m³

构造做法：
天花构造：
- 基层：{data.construction_methods.ceiling.base_layer}
- 饰面层：{data.construction_methods.ceiling.surface_layer}
- 面积：{data.construction_methods.ceiling.area_info.area:.2f}m²

墙体构造：
- 基层：{data.construction_methods.wall.base_layer}
- 饰面层：{data.construction_methods.wall.surface_layer}
- 面积：{data.construction_methods.wall.area_info.area:.2f}m²

地面构造：
- 基层：{data.construction_methods.floor.base_layer}
- 饰面层：{data.construction_methods.floor.surface_layer}
- 面积：{data.construction_methods.floor.area_info.area:.2f}m²

其他信息：
- 房间类型：{data.metadata['room_type']}
- 构造复杂度：{data.metadata['complexity_level']}
- 损耗率：{data.metadata['wastage_rate']*100:.1f}%
"""