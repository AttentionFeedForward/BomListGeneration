#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物料库管理模块

提供物料数据管理、查询和计算功能，
支持板材排版计算、龙骨间距计算等智能算法。
"""

import math
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class MaterialType(Enum):
    """物料类型枚举"""
    BOARD = "板材"  # 石膏板、水泥纤维板等
    TILE = "瓷砖"   # 地砖、墙砖
    CEILING_PANEL = "铝扣板"  # 天花铝扣板
    KEEL = "龙骨"   # 轻钢龙骨
    INSULATION = "保温材料"  # 岩棉、玻璃棉
    COATING = "涂料"  # 防霉涂料等
    FASTENER = "紧固件"  # 螺钉、射钉等
    SEALANT = "密封材料"  # 接缝带、密封胶等
    OTHER = "其他"


class CalculationMethod(Enum):
    """计算方法枚举"""
    AREA_DIRECT = "面积直算"  # 直接按面积计算
    AREA_LAYOUT = "面积排版"  # 按排版计算（板材、瓷砖等）
    AREA_DIRECT_PAINT="涂料面积计算"
    LENGTH_SPACING = "长度间距"  # 按间距计算（龙骨等）
    VOLUME_DENSITY = "体积密度"  # 按体积密度计算
    PERIMETER_RATIO = "周长比例"  # 按周长比例计算
    CUSTOM_FORMULA = "自定义公式"  # 自定义计算公式


@dataclass
class MaterialSpec:
    """物料规格数据类"""
    code: str  # 物料编码
    name: str  # 物料名称
    specification: list[str] # 规格描述
    unit: str  # 计量单位
    material_type: MaterialType  # 物料类型
    calculation_method: CalculationMethod  # 计算方法
    
    # 尺寸参数
    length: Optional[float] = None  # 长度(mm)
    width: Optional[float] = None   # 宽度(mm)
    thickness: Optional[float] = None  # 厚度(mm)
    
    # 计算参数
    coverage_area: Optional[float] = None  # 覆盖面积(m²/单位)
    spacing: Optional[float] = None  # 间距(mm)
    wastage_rate: float = 0.1  # 损耗率
    
    # 其他参数
    density: Optional[float] = None  # 密度(kg/m³)
    usage_ratio: Optional[float] = None  # 使用比例
    custom_formula: Optional[str] = None  # 自定义公式
    
    # 描述信息
    description: str = ""  # 详细描述
    usage_purpose: str = ""  # 用途说明
    notes: str = ""  # 备注


@dataclass
class CalculationResult:
    """计算结果数据类"""
    material_code: str
    material_name: str
    specification: list
    unit: str
    quantity: float
    calculation_formula: str  # 计算公式
    usage_purpose: str  # 材料用途
    notes: str = ""


class MaterialDatabase:
    """物料库管理类"""
    
    def __init__(self, config_manager=None, container_height=None):
        """初始化物料库
        
        Args:
            config_manager: 配置管理器实例
            container_height: 箱体高度(mm)，用于动态设置物料规格
        """
        self.config = config_manager
        self.materials: Dict[str, MaterialSpec] = {}
        self._load_default_materials(container_height)
    
    def update_container_dimensions(self, container_height):
        """更新箱体尺寸并重新加载物料数据
        
        Args:
            container_height: 箱体高度(mm)
        """
        self.materials.clear()  # 清空现有物料数据
        self._load_default_materials(container_height)
    
    def _load_default_materials(self, container_height=None):
        """加载默认物料数据
        
        Args:
            container_height: 箱体高度(mm)，用于动态设置物料规格
        """
        # 石膏板系列
        self.add_material(MaterialSpec(
            code="GYB-1200x2400-9.5",
            name="9.5mm石膏板",
            specification=["1200×2400×9.5mm"],
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=2400,
            width=1200,
            thickness=9.5,
            coverage_area=2.88,  # 1.2*2.4
            wastage_rate=0.1,
            description="标准石膏板，用于墙体和天花基层",
            usage_purpose="基层板材"
        ))

        self.add_material(MaterialSpec(
            code="GYB-1200x2400-9",
            name="9mm石膏板",
            specification=["1200×2400×9mm"],
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=2400,
            width=1200,
            thickness=9,
            coverage_area=2.88,  # 1.2*2.4
            wastage_rate=0.1,
            description="标准石膏板，用于墙体和天花基层",
            usage_purpose="基层板材"
        ))
        # 水泥纤维板系列
        self.add_material(MaterialSpec(
            code="FCB-1200x2400-10",
            name="10mm水泥纤维板",
            specification=["1200×2400×10mm"], 
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=2400,
            width=1200,
            thickness=10,
            coverage_area=2.88,
            wastage_rate=0.1,
            description="用于卫生间、厨房等有水房间的墙体",
            usage_purpose="基层板材"
        ))
        #防火板
        self.add_material(MaterialSpec(
            code="FRB-1200x2400-12.5",
            name="12.5mm防火板",
            specification=["1200×2400×12.5mm"],   
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=2400,
            width=1200,
            thickness=12.5,
            coverage_area=2.88,
            wastage_rate=0.1,
            description="用于有防火要求的墙体",
            usage_purpose="基层板材"
        ))
        # 集成墙板系列
        # 根据箱体高度动态设置规格
        alc_spec = f"{container_height}*600*100mm" if container_height else "箱体高度*600*100mm"
        aba_spec = f"{container_height}*300*80mm" if container_height else "箱体高度*300*80mm"
        
        self.add_material(MaterialSpec(
            code="ALC-600-100",
            name="ALC墙板",
            specification=[alc_spec],
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=container_height,  # 设置长度为箱体高度
            width=600,
            thickness=100,
            coverage_area=(container_height * 600 / 1000000) if container_height else None,  # 转换为平方米
            wastage_rate=0.1,
            description="一体化墙板，适用于快速建造",
            usage_purpose="一体板"
        ))
        self.add_material(MaterialSpec(
            code="ABA-300-80",
            name="ABA一体化墙板",
            specification=[aba_spec],
            unit="块",
            material_type=MaterialType.BOARD,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=container_height,  # 设置长度为箱体高度
            width=300,
            thickness=80,
            coverage_area=(container_height * 300 / 1000000) if container_height else None,  # 转换为平方米
            wastage_rate=0.1,
            description="一体化墙板，适用于快速建造",
            usage_purpose="一体板"
        ))
        # 轻钢龙骨系列
        self.add_material(MaterialSpec(
            code="KEEL-C50-0.6",
            name="50系列竖向龙骨",
            specification=["50*50*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=400,  
            wastage_rate=0.05,
            description="50系列竖龙骨，用于墙体和天花骨架",
            usage_purpose="骨架"
        ))
        self.add_material(MaterialSpec(
            code="KEEL-U50-0.6",
            name="50系列天地龙骨",
            specification=["50*40*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.PERIMETER_RATIO,
            usage_ratio=1.0, 
            wastage_rate=0.05,
            description="50系列边龙骨，用于墙体和天花骨架边框",
            usage_purpose="骨架"
        ))
        self.add_material(MaterialSpec(
            code="KEEL-HC50-0.6",
            name="50系列穿心龙骨",
            specification=["50*36*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=1200, 
            usage_ratio=1.0,  
            wastage_rate=0.05,
            description="50系列穿心龙骨，用于墙体和天花骨架",
            usage_purpose="骨架"
        ))

        self.add_material(MaterialSpec(
            code="KEEL-C75-0.6",
            name="75系列竖向龙骨",
            specification=["75*50*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=400,  
            wastage_rate=0.05,
            description="75系列竖龙骨，用于墙体和天花骨架",
            usage_purpose="骨架"
        ))
        
        self.add_material(MaterialSpec(
            code="KEEL-U75-0.6",
            name="75系列天地龙骨",
            specification=["75*40*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.PERIMETER_RATIO,
            usage_ratio=1.0,  
            wastage_rate=0.05,
            description="75系列边龙骨，用于墙体和天花骨架边框",
            usage_purpose="骨架"
        ))
        self.add_material(MaterialSpec(
            code="KEEL-HC75-0.6",
            name="75系列穿心龙骨",
            specification=["75*36*0.6mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=1200, 
            wastage_rate=0.05,
            description="75系列穿心龙骨，用于墙体和天花骨架",
            usage_purpose="骨架"
        ))
        # 天花龙骨系列
        self.add_material(MaterialSpec(
            code="AL-MAIN-38x24x1.0",
            name="天花主龙骨",
            specification=["38x24x1.0mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=900,
            wastage_rate=0.05,
            description="承载次龙骨及面板",
            usage_purpose="骨架"
        ))

        self.add_material(MaterialSpec(
            code="AL-CROSS-24x24x0.8-300",
            name="天花次龙骨",
            specification=["24x24x0.8mm"],
            unit="m",
            material_type=MaterialType.KEEL,
            calculation_method=CalculationMethod.LENGTH_SPACING,
            spacing=300,
            wastage_rate=0.05,
            description="直接承托铝扣板，通过卡件或挂件连接主龙骨",
            usage_purpose="骨架"
        ))

        self.add_material(MaterialSpec(
            code="HANGER-ROD-D8",
            name="天花吊杆",
            specification=["φ8mm全丝吊杆，含膨胀螺栓及螺母"],
            unit="套",
            material_type=MaterialType.FASTENER,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="天花面积 * 1.2",  # 约每平米1.2个
            wastage_rate=0.05,
            description="用于吊挂天花主龙骨",
            usage_purpose="吊顶固定"
        ))
        # 铝扣板系列      
        self.add_material(MaterialSpec(
            code="ALU-300x300-3",
            name="铝扣板",
            specification=["300×300×3mm"],
            unit="片",
            material_type=MaterialType.CEILING_PANEL,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=300,
            width=300,
            thickness=3,
            coverage_area=0.09,  # 0.3*0.3
            wastage_rate=0.05,
            description="方形铝扣板，用于天花饰面",
            usage_purpose="饰面层"
        ))
        
        # 瓷砖系列
        self.add_material(MaterialSpec(
            code="TILE-600x600-10",
            name="地砖",
            specification=["600×600×10mm"],
            unit="片",
            material_type=MaterialType.TILE,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=600,
            width=300,
            thickness=10,
            coverage_area=0.36,
            wastage_rate=0.08,
            description="标准瓷砖，用于墙地面饰面",
            usage_purpose="饰面层"
        ))
        self.add_material(MaterialSpec(
            code="TILE-300x600-10",
            name="墙砖",
            specification=["300×600×10mm"],
            unit="片",
            material_type=MaterialType.TILE,
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=600,
            width=300,
            thickness=10,
            coverage_area=0.18,
            wastage_rate=0.08,
            description="标准墙砖，用于墙面饰面",
            usage_purpose="饰面层"
        ))

        self.add_material(MaterialSpec(
            code="VINYL-LVP-120x180x4",
            name="乙烯基地板",
            specification=["1200×180×4mm，SPC锁扣式"],
            unit="片",
            material_type=MaterialType.TILE,  # 使用瓷砖/地板类型
            calculation_method=CalculationMethod.AREA_LAYOUT,
            length=1200,      # 单片长度（毫米）
            width=180,        # 单片宽度（毫米）
            thickness=4,      # 厚度（毫米）
            coverage_area=0.216,  # 单片覆盖面积：1.2m × 0.18m = 0.216㎡
            wastage_rate=0.05,    # 损耗率5%（锁扣式安装损耗较低）
            description="SPC锁扣乙烯基地板，防水耐磨，适用于家庭地面",
            usage_purpose="地面饰面层"
        ))
        # 岩棉系列
        self.add_material(MaterialSpec(
            code="ROCKWOOL-50-60",
            name="60kg/m³岩棉",
            specification=["50mm厚，容重60kg/m³"],
            unit="m²",
            material_type=MaterialType.INSULATION,
            calculation_method=CalculationMethod.AREA_DIRECT,
            thickness=50,
            density=60,
            wastage_rate=0.05,
            description="岩棉保温材料，用于墙体保温",
            usage_purpose="保温层"
        ))
        self.add_material(MaterialSpec(
            code="ROCKWOOL-75-80",
            name="80kg/m³岩棉",
            specification=["75mm厚，容重80kg/m³"],
            unit="m²",
            material_type=MaterialType.INSULATION,
            calculation_method=CalculationMethod.AREA_DIRECT,
            thickness=75,
            density=80,
            wastage_rate=0.05,
            description="岩棉保温材料，用于墙体保温",
            usage_purpose="保温层"
        ))

        # 涂料系列
        self.add_material(MaterialSpec(
            code="COATING-ANTIMOLD",
            name="无机防霉涂料",
            specification=["两遍成活"],
            unit="m²",
            material_type=MaterialType.COATING,
            calculation_method=CalculationMethod.AREA_DIRECT_PAINT,
            wastage_rate=0.05,
            description="无机防霉涂料，用于墙体和天花饰面",
            usage_purpose="饰面层"
        ))
        self.add_material(MaterialSpec(
            code="COATING-putty",
            name="腻子",
            specification=["两遍成活"],
            unit="m²",
            material_type=MaterialType.COATING,
            calculation_method=CalculationMethod.AREA_DIRECT_PAINT,
            wastage_rate=0.05,
            description="腻子，用于墙体和天花饰面",
            usage_purpose="饰面层"
        ))
        self.add_material(MaterialSpec(
            code="COATING-WATERPROOF",
            name="防水涂料",
            specification=["聚合物水泥防水涂料，1.5mm厚"],
            unit="kg",
            material_type=MaterialType.COATING,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="防水面积 * 2.5", # 两遍约2.5kg/m2
            wastage_rate=0.05,
            description="用于卫生间、厨房防水",
            usage_purpose="防水层"
        ))

        self.add_material(MaterialSpec(
            code="COATING-Epoxy",
            name="环氧地坪涂料",
            specification=["厚度约0.5mm/遍，涂刷2遍"],
            unit="m²",
            material_type=MaterialType.COATING,
            calculation_method=CalculationMethod.AREA_DIRECT_PAINT,
            wastage_rate=0.05,
            description="用于地面",
            usage_purpose="基层"
        ))

        # 紧固件系列
        self.add_material(MaterialSpec(
            code="SCREW-3.5x25",
            name="自攻螺丝",
            specification=["ST4.2*25mm"],
            unit="个",
            material_type=MaterialType.FASTENER,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="板材面积 * 12",  # 每平米约12个
            wastage_rate=0.1,
            description="自攻钉，用于固定板材",
            usage_purpose="板材固定"
        ))
        self.add_material(MaterialSpec(
            code="EXP-BOLT-M8x60",
            name="膨胀螺栓",
            specification=["M8×60mm"],
            unit="个",
            material_type=MaterialType.FASTENER,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="地龙骨长度总和 / 0.6",  # 每600mm设置一个锚固点
            wastage_rate=0.05,
            description="膨胀螺栓，用于龙骨与主体结构的固定",
            usage_purpose="龙骨固定"
            ))

        # 辅助材料系列
        self.add_material(MaterialSpec(
            code="MORTAR-CEMENT",
            name="水泥砂浆",
            specification=["M10水泥砂浆，配比1:3"],
            unit="m³",
            material_type=MaterialType.OTHER,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="铺贴面积 * 0.02",  # 假设20mm厚度
            wastage_rate=0.05,
            description="用于地面找平或墙面抹灰",
            usage_purpose="找平层"
        ))

        self.add_material(MaterialSpec(
            code="ADHESIVE-TILE",
            name="瓷砖粘结剂",
            specification=["20kg/袋"],
            unit="kg",
            material_type=MaterialType.OTHER,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="瓷砖面积 * 5",  # 每平米约5kg
            wastage_rate=0.05,
            description="用于瓷砖铺贴",
            usage_purpose="粘结层"
        ))

        self.add_material(MaterialSpec(
            code="SEALANT-SILICONE",
            name="密封胶",
            specification=["300ml/支"],
            unit="支",
            material_type=MaterialType.SEALANT,
            calculation_method=CalculationMethod.CUSTOM_FORMULA,
            custom_formula="缝隙长度 / 5",  # 每支约打5米
            wastage_rate=0.1,
            description="用于缝隙密封",
            usage_purpose="密封"
        ))

    
    def add_material(self, material: MaterialSpec):
        """添加物料
        
        Args:
            material: 物料规格对象
        """
        self.materials[material.code] = material
      
    def search_materials(self, keyword: str = "", 
                        material_type: Optional[MaterialType] = None,
                        usage_purpose: str = "") -> List[MaterialSpec]:
        """搜索物料
        
        Args:
            keyword: 关键词
            material_type: 物料类型
            usage_purpose: 用途
            
        Returns:
            匹配的物料列表
        """
        results = []
        keyword_lower = keyword.lower() if keyword else ""
        
        for material in self.materials.values():
            match_score = 0
            
            # 关键词匹配
            if keyword_lower:
                material_name_lower = material.name.lower()
                
                # 完全匹配
                if keyword_lower == material_name_lower:
                    match_score = 100
                # 包含匹配
                elif keyword_lower in material_name_lower:
                    match_score = 80
                # 关键词匹配
                else:
                    keyword_words = keyword_lower.split()
                    material_words = material_name_lower.split()
                    matched_words = sum(1 for word in keyword_words if word in material_words)
                    if matched_words > 0:
                        match_score = 60 * (matched_words / len(keyword_words))
            
            # 物料类型匹配
            if material_type and material.material_type == material_type:
                match_score += 20
            
            # 用途匹配
            if usage_purpose and usage_purpose.lower() in material.usage_purpose.lower():
                match_score += 10
            
            # 如果有匹配分数，添加到结果中
            if match_score > 0 or (not keyword and not material_type and not usage_purpose):
                results.append(material)
        
        # 按匹配度排序（如果有关键词搜索）
        if keyword:
            results.sort(key=lambda x: self._calculate_search_score(x, keyword_lower), reverse=True)
        
        return results
    
    def _calculate_search_score(self, material: MaterialSpec, keyword: str) -> float:
        """计算搜索匹配分数"""
        material_name = material.name.lower()
        
        # 完全匹配
        if keyword == material_name:
            return 100.0
        
        # 包含匹配
        if keyword in material_name:
            return 80.0
        
        # 反向包含匹配（物料名称包含在搜索关键词中）
        if material_name in keyword:
            return 75.0
        
        # 关键词匹配
        keyword_words = keyword.split()
        material_words = material_name.split()
        matched_words = sum(1 for word in keyword_words if word in material_words)
        
        if matched_words > 0:
            return 60.0 * (matched_words / len(keyword_words))
        
        # 模糊匹配：去除常见修饰词后再匹配
        # 处理"厚"字问题："12.5mm防火板" 应该能匹配 "12.5mm厚防火板"
        keyword_clean = keyword.replace('厚', '').replace('mm', 'mm厚')
        material_clean = material_name.replace('厚', '').replace('mm', 'mm厚')
        
        if keyword_clean in material_clean or material_clean in keyword_clean:
            return 70.0
        
        # 数字+单位+材料类型的匹配
        import re
        keyword_pattern = re.findall(r'\d+(?:\.\d+)?mm|\w+板|\w+砖|\w+龙骨', keyword)
        material_pattern = re.findall(r'\d+(?:\.\d+)?mm|\w+板|\w+砖|\w+龙骨', material_name)
        
        if keyword_pattern and material_pattern:
            common_patterns = set(keyword_pattern) & set(material_pattern)
            if common_patterns:
                return 50.0 * (len(common_patterns) / max(len(keyword_pattern), len(material_pattern)))
        
        return 0.0
    

    
    def get_material(self, material_code: str) -> Optional[MaterialSpec]:
        """根据物料编码获取物料信息
        
        Args:
            material_code: 物料编码
            
        Returns:
            物料规格对象或None
        """
        return self.materials.get(material_code)
    
    def calculate_quantity(self, material_code: str, area: float = 0, 
                          length: float = 0, width: float = 0,perimeter: float = 0,
                          thickness: float = 0, spacing: float = 0, section: str = '地面',
                          **kwargs) -> CalculationResult:
        """计算物料数量
        
        Args:
            material_code: 物料编码
            area: 面积(m²)
            length: 长度(m)
            width: 宽度(m)
            perimeter: 周长(m)
            thickness: 厚度(m)
            spacing: 间距(m)
            **kwargs: 其他参数
            
        Returns:
            计算结果
        """
        material = self.get_material(material_code)
        if not material:
            raise ValueError(f"未找到物料: {material_code}")
        
        # 根据计算方法进行计算
        if material.calculation_method == CalculationMethod.AREA_DIRECT:
            quantity = self._calculate_area_direct(material, area)
            formula = f"{section}面积 {area:.2f}m² × (1 + 损耗率 {material.wastage_rate:.1%}) = {quantity:.2f}{material.unit}"

        elif material.calculation_method == CalculationMethod.AREA_DIRECT_PAINT:
            quantity = self._calculate_area_direct_paint(material, area)
            formula = f"{section}面积 {area:.2f}m² × (1 + 损耗率 {material.wastage_rate:.1%}) = {quantity:.2f}{material.unit}"
            
        elif material.calculation_method == CalculationMethod.AREA_LAYOUT:
            quantity = self._calculate_area_layout(material, area)
            base_quantity = area / material.coverage_area
            formula = f"{section}面积 {area:.2f}m² ÷ 单块面积 {material.coverage_area:.3f}m² = {base_quantity:.2f}块，向上取整并加损耗 = {quantity:.0f}{material.unit}"
            
        elif material.calculation_method == CalculationMethod.LENGTH_SPACING:
            # 优先使用传入的spacing，否则使用材料默认spacing
            actual_spacing = spacing if spacing > 0 else (material.spacing / 1000 if material.spacing else 0.4)
            quantity = self._calculate_length_spacing(material, area, length, width, actual_spacing)
            formula = f"{section}面积 {area:.2f}m² ÷ 间距 {actual_spacing:.2f}m，加损耗 = {quantity:.2f}{material.unit}"
           
            
        elif material.calculation_method == CalculationMethod.PERIMETER_RATIO:
            quantity = self._calculate_perimeter_ratio(material, length, perimeter)
            ratio = material.usage_ratio or 1.0
            # 优先显示周长，其次显示长度
            effective_length = perimeter if perimeter and perimeter > 0 else length
            length_type = "周长" if perimeter and perimeter > 0 else "墙体总长"
            formula = f"2 × {section}{length_type} {effective_length:.2f}m × 使用比例 {ratio:.1f} × (1 + 损耗率 {material.wastage_rate:.1%}) = {quantity:.2f}{material.unit}"
            
        elif material.calculation_method == CalculationMethod.VOLUME_DENSITY:
            quantity = self._calculate_volume_density(material, area, thickness)
            actual_thickness = thickness if thickness > 0 else (material.thickness / 1000 if material.thickness else 0.05)
            volume = area * actual_thickness
            formula = f"{section}面积 {area:.2f}m² × 厚度 {actual_thickness:.3f}m × 密度 {material.density:.1f}kg/m³ = {quantity:.2f}{material.unit}"
            
        elif material.calculation_method == CalculationMethod.CUSTOM_FORMULA:
            quantity = self._calculate_custom_formula(material, area, length, perimeter, **kwargs)
            
            # 生成公式描述
            formula_desc = material.custom_formula or "自定义公式"
            
            # 简单的变量替换用于显示
            display_formula = formula_desc
            
            # 定义变量值用于替换显示
            val_area = f"{area:.2f}"
            val_len = f"{length:.2f}"
            val_peri = f"{perimeter:.2f}"
            
            # 替换常见变量名
            replacements = {
                "铺贴面积": f"铺贴面积({val_area}m²)",
                "防水面积": f"防水面积({val_area}m²)",
                "瓷砖面积": f"瓷砖面积({val_area}m²)",
                "板材面积": f"板材面积({val_area}m²)",
                "天花面积": f"天花面积({val_area}m²)",
                "地龙骨长度": f"地龙骨长度({val_peri}m)",
                "缝隙长度": f"缝隙长度({val_peri}m)",
                "周长": f"周长({val_peri}m)",
                "面积": f"面积({val_area}m²)",
                "长度": f"长度({val_len}m)"
            }
            
            # 使用正则替换以避免嵌套替换问题 (按长度降序排列key以优先匹配长词)
            sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
            pattern = re.compile('|'.join(map(re.escape, sorted_keys)))
            display_formula = pattern.sub(lambda m: replacements[m.group(0)], display_formula)
            
            # 根据单位判断是否取整
            is_integer_unit = material.unit in ["个", "支", "块", "套", "根"]
            if is_integer_unit:
                formula = f"{display_formula} × (1 + 损耗率 {material.wastage_rate:.1%})，向上取整 = {quantity:.0f}{material.unit}"
            else:
                formula = f"{display_formula} × (1 + 损耗率 {material.wastage_rate:.1%}) = {quantity:.2f}{material.unit}"
            
        else:
            # 默认按面积直算
            quantity = self._calculate_area_direct(material, area)
            formula = f"{section}面积 {area:.2f}m² × (1 + 损耗率 {material.wastage_rate:.1%})"
        
        return CalculationResult(
            material_code=material_code,
            material_name=material.name,
            specification=material.specification[0],
            unit=material.unit,
            quantity=round(quantity, 2),
            calculation_formula=formula,
            usage_purpose=f"用于{section}{material.usage_purpose}",
            notes=f"计算方法: {material.calculation_method.value}"
        )
    
    def _calculate_area_direct(self, material: MaterialSpec, area: float) -> float:
        """面积直算"""
        return area * (1 + material.wastage_rate)

    def _calculate_area_direct_paint(self, material: MaterialSpec, area: float) -> float:
        """涂料面积直算"""
        return 2* area * (1 + material.wastage_rate)

    def _calculate_area_layout(self, material: MaterialSpec, area: float) -> float:
        """面积排版计算（板材、瓷砖等）"""
        if not material.coverage_area or material.coverage_area <= 0:
            raise ValueError(f"物料 {material.name} 缺少覆盖面积参数")
        
        # 基础数量
        base_quantity = area / material.coverage_area
        
        # 考虑排版损耗
        quantity_with_wastage = base_quantity * (1 + material.wastage_rate)
        
        # 向上取整（板材、瓷砖等必须是整数）
        return math.ceil(quantity_with_wastage)
    
    def _calculate_length_spacing(self, material: MaterialSpec, area: float, length: float,
                                 width: float, spacing: float) -> float:
        """长度间距计算（龙骨等）"""
        if spacing <= 0:
            raise ValueError(f"物料 {material.name} 缺少间距参数")
        
        quantity = area / spacing
        
        return quantity * (1 + material.wastage_rate)
    
    def _calculate_perimeter_ratio(self, material: MaterialSpec, length: float, perimeter: float = None) -> float:
        """墙体总长比例计算"""
        # 优先使用perimeter参数（轮廓数据），其次使用length参数（传统输入）
        effective_length = perimeter if perimeter and perimeter > 0 else length
        
        if effective_length <= 0:
            raise ValueError(f"物料 {material.name} 需要墙体总长或周长参数")
        
        ratio = material.usage_ratio or 1.0
        return 2 * effective_length * ratio * (1 + material.wastage_rate)
    
    def _calculate_volume_density(self, material: MaterialSpec, area: float, thickness: float) -> float:
        """体积密度计算"""
        if not material.density or material.density <= 0:
            raise ValueError(f"物料 {material.name} 缺少密度参数")
        
        # 使用材料自身厚度或传入厚度
        actual_thickness = thickness if thickness > 0 else (material.thickness / 1000 if material.thickness else 0.05)
        
        volume = area * actual_thickness
        return volume * material.density
    
    def _calculate_custom_formula(self, material: MaterialSpec, area: float, 
                                 length: float, perimeter: float, **kwargs) -> float:
        """自定义公式计算"""
        if not material.custom_formula:
            # 如果没有自定义公式，回退到面积直算
            return self._calculate_area_direct(material, area)
        
        formula = material.custom_formula
        wastage_multiplier = 1 + material.wastage_rate
        
        # 确定使用的变量值
        # 优先使用 perimeter (周长) 如果它大于0，否则使用 length (长度) 作为线性参数
        linear_val = perimeter if perimeter > 0 else length
        
        # 构建变量映射
        variables = {
            "铺贴面积": area,
            "防水面积": area,
            "瓷砖面积": area,
            "板材面积": area,
            "天花面积": area,
            "面积": area,
            "地龙骨长度": linear_val,
            "缝隙长度": linear_val,
            "周长": linear_val,
            "长度": length,
            "宽": kwargs.get('width', 0),
            "高": kwargs.get('height', 0)
        }
        
        try:
            # 解析简单的数学公式
            # 支持格式: "变量 * 数值", "变量 / 数值", "(变量 + 变量) * 数值" 等简单形式
            # 为了安全和简单，这里使用简单的正则匹配处理最常见的几种情况
            
            val = 0.0
            
            # 情况1: 变量 * 数值 (如: "铺贴面积 * 0.02")
            match_mul = re.match(r'^([\u4e00-\u9fa5a-zA-Z0-9]+)\s*\*\s*([\d\.]+)$', formula.strip())
            if match_mul:
                var_name = match_mul.group(1).strip()
                factor = float(match_mul.group(2))
                if var_name in variables:
                    val = variables[var_name] * factor
                    
            # 情况2: 变量 / 数值 (如: "缝隙长度 / 5")
            elif not val:
                match_div = re.match(r'^([\u4e00-\u9fa5a-zA-Z0-9]+)\s*/\s*([\d\.]+)$', formula.strip())
                if match_div:
                    var_name = match_div.group(1).strip()
                    divisor = float(match_div.group(2))
                    if var_name in variables and divisor != 0:
                        val = variables[var_name] / divisor
            
            # 情况3: 保留原有的特定逻辑作为兼容 (如果正则没匹配上)
            if val == 0:
                if "板材面积" in formula and "12" in formula:
                    val = area * 12
                elif "地龙骨长度" in formula and "0.6" in formula:
                    val = linear_val / 0.6
            
            # 如果仍未计算出结果，尝试 eval (仅限受控变量)
            # 注意: eval 有风险，但在受控环境下，且替换变量为数字后，风险可控
            if val == 0:
                # 将变量名替换为数值
                eval_formula = formula
                for var_name, var_val in variables.items():
                    if var_name in eval_formula:
                        eval_formula = eval_formula.replace(var_name, str(var_val))
                
                # 检查是否只包含数字、运算符和小数点
                if re.match(r'^[\d\.\+\-\*\/\(\)\s]+$', eval_formula):
                    try:
                        val = eval(eval_formula)
                    except:
                        pass
            
            # 如果所有尝试都失败，回退默认
            if val == 0 and "面积" in formula:
                 val = area
            
            # 应用损耗率
            final_qty = val * wastage_multiplier
            
            # 根据单位判断是否取整
            if material.unit in ["个", "支", "块", "套", "根"]:
                return math.ceil(final_qty)
            else:
                return final_qty
                
        except Exception as e:
            print(f"Custom formula calculation error for {material.name}: {e}")
            # 公式解析失败，回退到面积直算
            return self._calculate_area_direct(material, area)