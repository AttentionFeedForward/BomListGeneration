#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOM生成模块

负责整合AI输出和项目数据，生成标准化的
装修物料清单，并提供导出功能。
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
from data_processor import ProcessedData


class BOMGenerator:
    """BOM生成器"""
    
    def __init__(self, config_manager):
        """初始化BOM生成器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config = config_manager
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_bom(self, ai_response: Dict[str, Any], 
                    processed_data: ProcessedData) -> Dict[str, Any]:
        """生成完整的BOM清单
        
        Args:
            ai_response: AI生成的响应数据
            processed_data: 处理后的项目数据
            
        Returns:
            完整的BOM清单数据
        """
        try:
            # 标准化AI输出的物料清单
            # 尝试从不同的字段获取物料清单
            items_list = ai_response.get('items', []) or ai_response.get('bom_list', [])
            standardized_items = self._standardize_items(items_list)
            
            # 验证和修正数据
            validated_items = self._validate_and_correct_items(standardized_items, processed_data)
            
            # 生成项目信息
            project_info = self._generate_project_info(processed_data)
            
            # 生成统计信息
            statistics = self._generate_statistics(validated_items, processed_data)
            
            # 生成AI分析
            ai_analysis = self._generate_ai_analysis(validated_items, processed_data)
            
            # 构建完整结果
            bom_result = {
                'project_info': project_info,
                'items': validated_items,
                'statistics': statistics,
                'ai_analysis': ai_analysis,
                'metadata': {
                    'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'ai_model': ai_response.get('metadata', {}).get('model', 'unknown'),
                    'total_items': len(validated_items),
                    'data_source': 'AI Generated + Manual Validation'
                }
            }
            
            # 保存到文件
            self._save_bom_to_file(bom_result)
            
            return bom_result
            
        except Exception as e:
            raise Exception(f"生成BOM清单失败: {str(e)}")
    
    def _standardize_items(self, raw_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """标准化物料清单项目
        
        Args:
            raw_items: 原始物料清单项目
            
        Returns:
            标准化后的物料清单项目
        """
        standardized = []
        
        for i, item in enumerate(raw_items, 1):
            try:
                # 标准化字段名
                standardized_item = {
                    '项次': self._safe_get(item, ['项次', '序号', 'index'], str(i)),
                    '物料编码': self._safe_get(item, ['物料编码', '编码', 'code'], f'MAT-{i:03d}'),
                    '描述': self._safe_get(item, ['描述', '名称', 'description', 'name'], '未知材料'),
                    '规格': self._safe_get(item, ['规格', '型号', 'specification', 'spec'], '标准规格'),
                    '数量': self._parse_quantity(self._safe_get(item, ['数量', 'quantity'], '1')),
                    '单位': self._safe_get(item, ['单位', 'unit'], '个'),
                    '计算公式': self._safe_get(item, ['计算公式', 'formula', 'calculation'], ''),
                    '材料用途': self._safe_get(item, ['材料用途', '用途', 'usage', 'purpose'], ''),
                    '备注': self._safe_get(item, ['备注', '说明', 'remark', 'note'], '')
                }
                
                standardized.append(standardized_item)
                
            except Exception as e:
                print(f"警告: 标准化第{i}项物料时出错: {e}")
                continue
        
        return standardized
    
    def _safe_get(self, item: Dict[str, Any], keys: List[str], default: str = '') -> str:
        """安全获取字典值
        
        Args:
            item: 字典对象
            keys: 可能的键名列表
            default: 默认值
            
        Returns:
            获取到的值或默认值
        """
        for key in keys:
            if key in item and item[key] is not None:
                return str(item[key]).strip()
        return default
    
    def _parse_quantity(self, quantity_str: str) -> float:
        """解析数量字符串
        
        Args:
            quantity_str: 数量字符串
            
        Returns:
            数量数值
        """
        try:
            # 移除非数字字符，保留小数点
            import re
            cleaned = re.sub(r'[^\d.]', '', str(quantity_str))
            return float(cleaned) if cleaned else 1.0
        except:
            return 1.0
    
    def _validate_and_correct_items(self, items: List[Dict[str, Any]], 
                                   processed_data: ProcessedData) -> List[Dict[str, Any]]:
        """验证和修正物料清单项目
        
        Args:
            items: 物料清单项目
            processed_data: 处理后的项目数据
            
        Returns:
            验证修正后的物料清单项目
        """
        validated_items = []
        
        for item in items:
            # 验证必需字段
            if not item.get('描述') or item['描述'] == '未知材料':
                continue
            
            # 修正数量（确保合理性）
            quantity = float(item.get('数量', 1))
            if quantity <= 0:
                quantity = 1.0
            elif quantity > 10000:  # 异常大的数量
                quantity = min(quantity, 1000.0)
            
            item['数量'] = quantity
            
            # 添加计算依据到备注
            if not item.get('备注'):
                item['备注'] = self._generate_remark(item, processed_data)
            
            validated_items.append(item)
        
        return validated_items
    
    def _generate_remark(self, item: Dict[str, Any], 
                        processed_data: ProcessedData) -> str:
        """生成备注信息
        
        Args:
            item: 物料项目
            processed_data: 处理后的项目数据
            
        Returns:
            备注信息
        """
        description = item.get('描述', '').lower()
        
        # 根据材料类型生成不同的备注
        if '石膏板' in description or '板材' in description:
            return f"含{processed_data.metadata['wastage_rate']*100:.0f}%损耗"
        elif '龙骨' in description:
            return "按实际长度计算"
        elif '螺钉' in description or '钉' in description:
            return "固定用"
        elif '涂料' in description or '漆' in description:
            return "二遍成活"
        else:
            return "按设计要求"
    
    def _generate_project_info(self, processed_data: ProcessedData) -> Dict[str, Any]:
        """生成项目信息
        
        Args:
            processed_data: 处理后的项目数据
            
        Returns:
            项目信息字典
        """
        return {
            'project_name': f"装修工程-{processed_data.metadata['room_type']}",
            'dimensions': {
                'length': processed_data.dimensions.length,
                'width': processed_data.dimensions.width,
                'height': processed_data.dimensions.height
            },
            'areas': processed_data.areas,
            'construction_methods': processed_data.construction_details,
            'generation_time': processed_data.metadata['calculation_time'],
            'room_type': processed_data.metadata['room_type'],
            'complexity_level': processed_data.metadata['complexity_level']
        }
    
    def _generate_statistics(self, items: List[Dict[str, Any]], 
                           processed_data: ProcessedData) -> Dict[str, Any]:
        """生成统计信息
        
        Args:
            items: 物料清单项目
            processed_data: 处理后的项目数据
            
        Returns:
            统计信息字典
        """
        # 按材料类型分类统计
        material_types = {
            '基层材料': 0,
            '饰面材料': 0,
            '辅助材料': 0,
            '其他材料': 0
        }
        
        for item in items:
            description = item.get('描述', '').lower()
            if any(keyword in description for keyword in ['龙骨', '板材', '石膏板']):
                material_types['基层材料'] += 1
            elif any(keyword in description for keyword in ['涂料', '瓷砖', '地板']):
                material_types['饰面材料'] += 1
            elif any(keyword in description for keyword in ['螺钉', '胶水', '接缝']):
                material_types['辅助材料'] += 1
            else:
                material_types['其他材料'] += 1
        
        return {
            'total_items': len(items),
            'material_types': material_types,
            'total_area': processed_data.areas['total_area'],
            'material_density': len(items) / processed_data.areas['total_area'] if processed_data.areas['total_area'] > 0 else 0
        }
    
    def _generate_ai_analysis(self, items: List[Dict[str, Any]], 
                             processed_data: ProcessedData) -> str:
        """生成AI分析说明
        
        Args:
            items: 物料清单项目
            processed_data: 处理后的项目数据
            
        Returns:
            分析说明文本
        """
        analysis_parts = []
        
        # 基本信息分析
        analysis_parts.append(f"本项目为{processed_data.metadata['room_type']}，")
        analysis_parts.append(f"总面积{processed_data.areas['total_area']:.1f}m²，")
        analysis_parts.append(f"共需{len(items)}种材料。")
        
        # 复杂度分析
        complexity = processed_data.metadata['complexity_level']
        if complexity == '高':
            analysis_parts.append("构造做法较为复杂，需要专业施工队伍。")
        elif complexity == '中':
            analysis_parts.append("构造做法中等复杂度，施工难度适中。")
        else:
            analysis_parts.append("构造做法相对简单，施工难度较低。")
        
        # 材料特点分析
        main_materials = [item['描述'] for item in items[:3]]  # 前3种主要材料
        analysis_parts.append(f"主要材料包括{', '.join(main_materials)}等。")
        
        # 施工建议
        analysis_parts.append("建议按照设计图纸和规范要求施工，确保材料质量和施工工艺。")
        
        return ' '.join(analysis_parts)
    
    def _save_bom_to_file(self, bom_result: Dict[str, Any]):
        """保存BOM清单到文件
        
        Args:
            bom_result: BOM清单结果
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保存为CSV
            if bom_result['items']:
                df = pd.DataFrame(bom_result['items'])
                csv_path = self.output_dir / f"BOM清单_{timestamp}.csv"
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            
            # 保存为JSON（包含完整信息）
            import json
            json_path = self.output_dir / f"BOM完整数据_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(bom_result, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"警告: 保存BOM文件失败: {e}")
    
    def export_to_excel(self, bom_result: Dict[str, Any], 
                       file_path: Optional[str] = None) -> str:
        """导出BOM清单到Excel文件
        
        Args:
            bom_result: BOM清单结果
            file_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = self.output_dir / f"BOM清单_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # 物料清单工作表
                if bom_result['items']:
                    df_items = pd.DataFrame(bom_result['items'])
                    df_items.to_excel(writer, sheet_name='物料清单', index=False)
                
                # 项目信息工作表
                project_info = bom_result['project_info']
                df_project = pd.DataFrame([
                    ['项目名称', project_info.get('project_name', '')],
                    ['房间长度', f"{project_info['dimensions']['length']} m"],
                    ['房间宽度', f"{project_info['dimensions']['width']} m"],
                    ['房间高度', f"{project_info['dimensions']['height']} m"],
                    ['地面面积', f"{project_info['areas']['floor_area']:.2f} m²"],
                    ['墙体面积', f"{project_info['areas']['wall_area']:.2f} m²"],
                    ['天花面积', f"{project_info['areas']['ceiling_area']:.2f} m²"],
                    ['生成时间', project_info.get('generation_time', '')]
                ], columns=['项目', '值'])
                df_project.to_excel(writer, sheet_name='项目信息', index=False)
            
            return str(file_path)
            
        except Exception as e:
            raise Exception(f"导出Excel文件失败: {str(e)}")