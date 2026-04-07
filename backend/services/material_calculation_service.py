"""
材料计算服务
处理材料BOM生成的核心业务逻辑
"""
import sys
import os
import json
import re
from typing import Dict, Any, List, Optional
from decimal import Decimal


OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL=os.getenv("OPENAI_BASE_URL")

try:
    # 添加modules目录到Python路径
    backend_path = os.path.dirname(os.path.dirname(__file__))
    project_path = os.path.dirname(backend_path)
    modules_path = os.path.join(project_path, 'modules')
    sys.path.insert(0, modules_path)
    
    # 直接导入模块文件
    import config_manager
    import data_processor
    import material_database
    import material_calculator
    import bom_generator
    import mep_engine
    
    # 获取需要的类
    ConfigManager = config_manager.ConfigManager
    DataProcessor = data_processor.DataProcessor
    ProcessedData = data_processor.ProcessedData
    MaterialDatabase = material_database.MaterialDatabase
    MaterialCalculator = material_calculator.MaterialCalculator
    BOMGenerator = bom_generator.BOMGenerator
    
    # 导入LLM相关类（用于物料识别）
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    
except ImportError as e:
    print(f"Error importing modules: {e}")
    raise


class MaterialCalculationService:
    """材料计算服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.config_manager = ConfigManager()
        self.data_processor = DataProcessor(self.config_manager)
        self.material_database = MaterialDatabase()
        self.material_calculator = MaterialCalculator(self.material_database)
        self.bom_generator = BOMGenerator(self.config_manager)
        
        # 初始化配置管理器和API配置
        self.config = ConfigManager()
        self.api_config = self.config.get_api_config()
        
        # 初始化LLM用于物料识别
        self.llm = self._initialize_llm()

        # 加载机电物料经验指标
        self.bs_data = self._load_bs_data()

    def _load_bs_data(self) -> Dict[str, Any]:
        """加载BS.json数据"""
        try:
            bs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'BS.json')
            if os.path.exists(bs_path):
                with open(bs_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Warning: BS.json not found at {bs_path}")
                return {}
        except Exception as e:
            print(f"Error loading BS.json: {e}")
            return {}

    # openai_api_key=self.api_config['api_key'],openai_api_base=self.api_config['base_url'],model_name=self.api_config['model'],temperature=self.api_config['temperature'],max_tokens=self.api_config['max_tokens']
         
    def _initialize_llm(self):
        """初始化语言模型
        
        Returns:
            语言模型实例
        """
        try:
            return ChatOpenAI(
                model="qwen3_32b_public",
                openai_api_key=OPENAI_API_KEY,
                openai_api_base=OPENAI_BASE_URL,
                streaming=True,
                extra_body={"enable_thinking": False},
                temperature=0.3,
                max_tokens=2000
            )

        except Exception as e:
            raise Exception(f"无法初始化ChatOpenAI: {e}")
    
    def generate_material_bom(self, module_data: Dict[str, Any], construction_practices: Dict[str, str], project_type: str = '住宅', room_type: str = '标准房间') -> Dict[str, Any]:
        """
        生成材料BOM
        
        Args:
            module_data: 模块数据 {height: float(mm), floor_area: float(m²), wall_area: float(m²), ceiling_area: float(m²)}
            construction_practices: 构造做法选择 {category-layerType: option}
            project_type: 项目类型 (住宅/公寓/酒店)
            room_type: 房间类型 (客厅/卧室/厨房/卫生间/其余)
        
        Returns:
            Dict: BOM生成结果，只包含物料名称、物料规格、用量
        """
        try:
            # 1. 数据预处理和格式转换
            print("--- 步骤 1: 开始数据预处理和格式转换 ---")
            processed_data = self._convert_frontend_data_to_processed_data(module_data, construction_practices)
            # 更新metadata中的room_type
            processed_data.metadata['room_type'] = room_type
            
            print("--- 步骤 1: 数据预处理完成，详情如下 ---")
            try:
                print(json.dumps(self._debug_processed_data(processed_data), ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"[调试] 处理数据序列化失败: {e}; 原对象: {processed_data}")
            
            # 2. 使用LLM识别物料清单（按天地墙分类）
            print("--- 步骤 2: 开始使用LLM识别物料清单 ---")
            material_dict = self._identify_materials(processed_data)
            print(f"--- 步骤 2: 物料识别完成, 结果: {material_dict} ---")
            
            # 3. 在数据库中查找物料信息
            print("--- 步骤 3: 开始在数据库中查找物料信息 ---")
            found_materials = self._lookup_materials(material_dict, processed_data)
            print(f"--- 步骤 3: 物料查找完成, 找到 {len(found_materials)} 个物料 ---")
            
            # 4. 计算装修物料用量
            print("--- 步骤 4: 开始计算装修物料用量 ---")
            calculated_materials = self._calculate_materials(found_materials, processed_data)
            print(f"--- 步骤 4: 装修物料用量计算完成, 计算了 {len(calculated_materials)} 个物料 ---")

            # 4.1 计算机电物料用量 (新增)
            print("--- 步骤 4.1: 开始计算机电物料用量 ---")
            mep_materials = self._calculate_mep_materials(processed_data, project_type, room_type)
            calculated_materials.extend(mep_materials)
            print(f"--- 步骤 4.1: 机电物料计算完成, 新增 {len(mep_materials)} 个物料 ---")
            
            # 4 补充：处理未找到的物料并整合完整的BOM清单
            print("--- 步骤 4（补充）: 整理全部识别物料并查找缺失项 ---")
            # 将分类物料字典转换为扁平列表，并建立物料到分类的映射
            all_material_names: List[str] = []
            name_to_category: Dict[str, str] = {}
            for category, materials in material_dict.items():
                base_category = category.replace('_materials', '')  # ceiling_materials -> ceiling
                for m in materials:
                    all_material_names.append(m)
                    name_to_category[m] = base_category
            found_names = {item.get('search_name', getattr(item.get('material'), 'name', '')) for item in found_materials}
            missing_materials = [n for n in all_material_names if n and n not in found_names]
            print(f"--- 步骤 4（补充）: 未在数据库找到的物料 {len(missing_materials)} 项: {missing_materials} ---")
            
            ai_items_simple: List[Dict[str, Any]] = []
            if missing_materials:
                print("--- 步骤 4（补充）: 调用LLM为缺失物料生成BOM项 ---")
                try:
                    ai_items_simple = self._generate_missing_materials_simple(missing_materials, processed_data, name_to_category)
                    print(f"--- 步骤 4（补充）: LLM补充生成 {len(ai_items_simple)} 项 ---")
                except Exception as e:
                    print(f"--- 步骤 4（补充）: LLM补充生成失败，错误: {e}，跳过缺失项补充 ---")
            
            # 5. 格式化输出结果（只返回物料名称、规格、用量）
            print("--- 步骤 5: 开始格式化输出结果 ---")
            bom_result = self._format_simple_bom_output(calculated_materials)
            # 合并AI补充物料到输出
            if ai_items_simple:
                try:
                    bom_result['materials'].extend(ai_items_simple)
                    bom_result['summary']['total_items'] = len(bom_result['materials'])
                    # 标注生成方式为混合
                    bom_result['summary']['generation_method'] = 'service_calculation+ai_complement'
                except Exception as e:
                    print(f"--- 步骤 5: 合并AI补充物料失败: {e} ---")
            print("--- 步骤 5: 格式化输出完成 ---")
            
            return {
                'success': True,
                'data': bom_result,
                'message': 'BOM生成成功'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'BOM生成失败'
            }

    def generate_mep_bom_from_floorplan(self, floorplan_data: Dict[str, Any], project_type: str = '住宅') -> Dict[str, Any]:
        try:
            result = mep_engine.generate(floorplan_data, project_type)
            return {
                'success': True,
                'data': result,
                'message': 'MEP生成成功'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'MEP生成失败'
            }
    
    def _convert_frontend_data_to_processed_data(self, module_data: Dict[str, Any], construction_practices: Dict[str, str]) -> ProcessedData:
        """
        将前端数据转换为ProcessedData格式
        
        Args:
            module_data: 前端模块数据
            construction_practices: 构造做法选择
            
        Returns:
            ProcessedData: 转换后的数据
        """
        # # 从前端 module_data 中读取参数
        height_m = float(module_data.get('height', 0)) / 1000.0
        floor_area = float(module_data.get('floor_area', 0))
        wall_area = float(module_data.get('wall_area', 0))
        ceiling_area = float(module_data.get('ceiling_area', 0))
        perimeter = float(module_data.get('perimeter', 0))
        
        # 估算房间尺寸：假设矩形，根据周长与面积联合求解长宽
        # 若两者都可用：设 s = L + W = perimeter / 2, L * W = floor_area
        # 求根：L = (s + sqrt(s^2 - 4A))/2, W = (s - sqrt(s^2 - 4A))/2
        # 若数据不一致（判别式为负）或仅有其中一个，则退化为正方形或仅面积推断
        length = width = 0.0
        if floor_area > 0 and perimeter > 0:
            s = perimeter / 2.0
            discriminant = s * s - 4.0 * floor_area
            if discriminant >= 0:
                root = discriminant ** 0.5
                length = (s + root) / 2.0
                width = (s - root) / 2.0
                # 数值稳定性：避免出现负值
                if length < 0 or width < 0:
                    length = width = s / 2.0
            else:
                # 不一致数据，退化为以周长为依据的正方形
                length = width = s / 2.0
        elif floor_area > 0:
            length = width = floor_area ** 0.5
        elif perimeter > 0:
            length = width = perimeter / 4.0
        
        # 解析构造做法
        ceiling_base = construction_practices.get('ceiling-baseLayer', '无')
        ceiling_surface = construction_practices.get('ceiling-surfaceLayer', '无')
        wall_base = construction_practices.get('wall-baseLayer', '无')
        wall_surface = construction_practices.get('wall-surfaceLayer', '无')
        floor_base = construction_practices.get('floor-baseLayer', '无')
        floor_surface = construction_practices.get('floor-surfaceLayer', '无')
        
        # 创建ProcessedData对象（模拟原有数据结构）
        processed_data = ProcessedData(
            dimensions=type('Dimensions', (), {
                'length': length,
                'width': width,
                'height': height_m
            })(),
            contour_data=type('ContourData', (), {
                'floor_area': floor_area,
                'wall_area': wall_area,
                'ceiling_area': ceiling_area,
                'perimeter': perimeter
            })(),
            construction_methods=type('ConstructionMethods', (), {
                'ceiling': type('Layer', (), {
                    'base_layer': ceiling_base,
                    'surface_layer': ceiling_surface
                })(),
                'wall': type('Layer', (), {
                    'base_layer': wall_base,
                    'surface_layer': wall_surface
                })(),
                'floor': type('Layer', (), {
                    'base_layer': floor_base,
                    'surface_layer': floor_surface
                })()
            })(),
            metadata={'room_type': '标准房间'}
        )
        
        return processed_data

    def _debug_processed_data(self, data: ProcessedData) -> Dict[str, Any]:
        """
        将ProcessedData转换为可读的字典结构，便于调试打印
        """
        try:
            return {
                'dimensions': {
                    'length': getattr(data.dimensions, 'length', None),
                    'width': getattr(data.dimensions, 'width', None),
                    'height': getattr(data.dimensions, 'height', None),
                },
                'contour_data': {
                    'floor_area': getattr(data.contour_data, 'floor_area', None),
                    'wall_area': getattr(data.contour_data, 'wall_area', None),
                    'ceiling_area': getattr(data.contour_data, 'ceiling_area', None),
                },
                'construction_methods': {
                    'ceiling': {
                        'base_layer': getattr(getattr(data.construction_methods, 'ceiling', object()), 'base_layer', None),
                        'surface_layer': getattr(getattr(data.construction_methods, 'ceiling', object()), 'surface_layer', None),
                    },
                    'wall': {
                        'base_layer': getattr(getattr(data.construction_methods, 'wall', object()), 'base_layer', None),
                        'surface_layer': getattr(getattr(data.construction_methods, 'wall', object()), 'surface_layer', None),
                    },
                    'floor': {
                        'base_layer': getattr(getattr(data.construction_methods, 'floor', object()), 'base_layer', None),
                        'surface_layer': getattr(getattr(data.construction_methods, 'floor', object()), 'surface_layer', None),
                    },
                },
                'metadata': getattr(data, 'metadata', {})
            }
        except Exception as e:
            return {'error': f'序列化ProcessedData失败: {str(e)}'}
    
    def _identify_materials(self, processed_data: ProcessedData) -> Dict[str, List[str]]:
        """
        使用LLM识别构造做法需要的物料清单（重写langchain_service中的identify_materials方法）
        保持算法逻辑不变，只适配参数
        
        Args:
            processed_data: 处理后的项目数据
            
        Returns:
            按天地墙分类的物料字典
        """
        try:
            if not self.llm:
                # 如果LLM不可用，返回空字典
                return {"ceiling_materials": [], "wall_materials": [], "floor_materials": []}
            
            # 构建物料识别提示词（复用langchain_service的逻辑）
            messages = self._build_material_identification_prompt(processed_data)
            
            # 调用AI识别
            response = self.llm.invoke(messages)
            
            # 解析响应
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # 解析物料列表（复用langchain_service的逻辑）
            material_dict = self._parse_material_list(response_text)
            
            return material_dict
            
        except Exception as e:
            print(f"物料识别失败: {e}")
            return {"ceiling_materials": [], "wall_materials": [], "floor_materials": []}
    
    def _build_material_identification_prompt(self, data: ProcessedData) -> List:
        """
        构建物料识别提示词（复用langchain_service的逻辑）
        
        Args:
            data: 处理后的数据
            
        Returns:
            提示词消息列表
        """
        system_prompt = """你是一名专业的建筑工程造价师和材料专家。请根据提供的房间信息和构造做法，按天地墙分类识别出所需的装修物料清单。"""
        
        # 格式化数据（按天地墙分类）
        formatted_data = f"""
项目信息：
- 房间尺寸：长{data.dimensions.length}m × 宽{data.dimensions.width}m × 高{data.dimensions.height}m
- 房间类型：{data.metadata['room_type']}

天花构造：
- 基层：{data.construction_methods.ceiling.base_layer}
- 饰面层：{data.construction_methods.ceiling.surface_layer}

墙体构造：
- 基层：{data.construction_methods.wall.base_layer}
- 饰面层：{data.construction_methods.wall.surface_layer}

地面构造：
- 基层：{data.construction_methods.floor.base_layer}
- 饰面层：{data.construction_methods.floor.surface_layer}
"""    
        human_prompt = formatted_data + """
你是一名专业的建筑工程造价师和材料专家。请根据上面提供的房间信息和构造做法，分别识别天花基层、天花饰面层、墙体基层、墙体饰面层、地面基层、地面饰面层所需的装修物料清单。
按以下JSON格式返回结果：
{
  "ceiling_materials": ["物料1", "物料2", ...],
  "wall_materials": ["物料1", "物料2", ...],
  "floor_materials": ["物料1", "物料2", ...]
}
天花基层和天花饰面层识别到的物料填入ceiling_materials对应的列表中；墙体基层和墙体饰面层识别到的物料填入wall_materials对应的列表中；地面基层和地面饰面层识别到的物料填入floor_materials对应的列表中

要求：

1. 物料名称要包含规格尺寸信息（比如50系列、75系列、10mm等）；
2. 如果物料名称前面没有规格尺寸信息，直接输出物料名称；
3. 物料名称要规范、准确；
4. 如果某部位构造做法输入是"无"，对应分类返回空列表；
5. 如果输入是"自定义"，请结合下方示例和建筑常识合理拆解。
 
Few-shot 示例库，下方给了一些常见的天花、墙体、地面的基层和是面层做法所包含物料清单：

天花构造基层:50系列轻钢龙骨+双层9.5mm石膏板体系
包含物料:50系列竖向龙骨,50系列天地龙骨,50系列穿心龙骨,9.5mm石膏板,自攻螺丝,膨胀螺栓,密封胶

天花构构造基层：铝扣板龙骨体系
包含物料:吊杆,膨胀螺栓,天花主龙骨,天花次龙骨

墙体构造基层:75系列轻钢龙骨+80kg/m³岩棉+双层10mm水泥纤维板+防水涂料
包含物料:75系列竖向龙骨,75系列天地龙骨,75系列穿心龙骨,80kg/m³岩棉,10mm水泥纤维板,自攻螺丝,膨胀螺栓,密封胶,防水涂料

墙体构造基层：ALC墙板
包含物料:ALC墙板,专用粘结剂,U型卡件,密封胶,耐碱网格布,抗震钢筋

墙体构造基层：一体化集成墙板
包含物料:集成墙板,专用龙骨,卡件,收边条,密封胶

墙体构造饰面层：无机防霉涂料
包含物料:腻子,无机防霉涂料

墙体构造饰面层：墙砖
包含物料:墙砖,瓷砖粘结剂

地面构造基层:防水涂料+水泥砂浆
包含物料:防水涂料,水泥砂浆

地面构造饰面层：地砖
包含物料：地砖,瓷砖粘结剂

"""
        
        # 直接构建消息列表，避免模板格式化问题
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        return messages
    
    def _parse_material_list(self, text: str) -> Dict[str, List[str]]:
        """
        解析AI返回的物料列表（复用langchain_service的逻辑）
        
        Args:
            text: AI返回的文本
            
        Returns:
            解析后的物料字典
        """
        try:
            # 尝试直接解析JSON
            if '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_str = text[json_start:json_end]
                
                # 清理可能的格式问题
                json_str = re.sub(r'[\n\r\t]', '', json_str)
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)
                
                material_dict = json.loads(json_str)
                
                # 确保所有必需的键存在
                result = {
                    "ceiling_materials": material_dict.get("ceiling_materials", []),
                    "wall_materials": material_dict.get("wall_materials", []),
                    "floor_materials": material_dict.get("floor_materials", [])
                }
                
                return result
            
        except Exception as e:
            print(f"JSON解析失败: {e}")
        
        # 如果JSON解析失败，尝试文本解析
        return self._parse_material_list_from_text(text)
    
    def _calculate_mep_materials(self, processed_data: ProcessedData, project_type: str, room_type: str) -> List[Dict[str, Any]]:
        """
        根据BS.json计算机电物料用量
        
        Args:
            processed_data: 处理后的数据
            project_type: 项目类型 (住宅/公寓/酒店)
            room_type: 房间类型 (客厅/卧室/厨房/卫生间/其余)
            
        Returns:
            机电物料BOM列表
        """
        results = []
        if not self.bs_data:
            return results

        # 上下文变量，用于存储中间计算结果（如管长、底盒数）供后续依赖项使用
        floor_area = 0.0
        if processed_data and processed_data.contour_data and processed_data.contour_data.floor_area is not None:
            try:
                floor_area = float(processed_data.contour_data.floor_area)
            except (ValueError, TypeError):
                floor_area = 0.0

        context = {
            'floor_area': floor_area,
            'electrical_pipe_len': 0.0,  # 电工管长度
            'weak_electric_pipe_len': 0.0, # 弱电管长度
            'fresh_air_pipe_len': 0.0,   # 新风管长度
            'box_count': 0,              # 接线盒/底盒总数
            'kitchen_count': 1 if room_type == '厨房' else 0 # 是否为厨房
        }

        # 映射房间类型到BS.json的key
        # BS.json keys: "客厅", "卧室", "厨房", "其余" (住宅/公寓); "卫生间" (implied in items like 排风扇)
        # 简单映射逻辑
        bs_room_key = room_type
        if room_type not in ["客厅", "卧室", "厨房", "卫生间"]:
            bs_room_key = "其余"

        # 定义分类映射 (JSON key -> BOM category)
        category_map = {
            'electrical_system': 'electrical',
            'plumbing_system': 'plumbing',
            'hvac_system': 'hvac',
            'fire_system': 'fire'
        }

        # 遍历主要系统
        for sys_key, sys_data in self.bs_data.items():
            category = category_map.get(sys_key, sys_key)
            
            # 扁平化遍历所有子项
            items_to_process = []
            if isinstance(sys_data, dict):
                for sub_key, sub_data in sys_data.items():
                    # 判断是否是具体的物料项（包含unit或换算说明）还是子分类
                    if 'unit' in sub_data or '换算说明' in sub_data or isinstance(sub_data.get('住宅'), (int, float, dict)):
                        items_to_process.append((sub_key, sub_data))
                    else:
                        # 二级嵌套 (如 electrical_system -> strong_electric -> item)
                        for item_name, item_data in sub_data.items():
                             items_to_process.append((item_name, item_data))

            # 第一遍遍历：计算独立项
            for item_name, item_data in items_to_process:
                qty = 0.0
                unit = item_data.get('unit', '')
                spec = item_data.get('规格', '')
                code = item_data.get('code', '') # 获取BS.json中定义的物料编码
                formula_str = ""
                
                # 跳过依赖项（换算说明），稍后处理
                if '换算说明' in item_data:
                    continue

                # 获取指标值
                indicator = item_data.get(project_type)
                if indicator is None:
                    continue

                # 解析指标值
                val = 0.0
                if isinstance(indicator, (int, float)):
                    val = float(indicator)
                elif isinstance(indicator, dict):
                    # 查找匹配的房间类型，找不到则用"其余"，再找不到用默认值
                    val = float(indicator.get(bs_room_key, indicator.get("其余", 0)))
                
                # 根据单位计算用量
                if 'm/㎡' in unit or '个/㎡' in unit:
                    qty = val * context['floor_area']
                    formula_str = f"指标 {val} × 面积 {context['floor_area']:.2f}㎡"
                elif '个/房' in unit:
                    qty = val
                    formula_str = f"按房标准配置: {val}"
                elif '个/户' in unit:
                    # 策略：仅在客厅计算户级物料，或者酒店模式下每房计算
                    if project_type == '酒店':
                        qty = val
                        formula_str = f"酒店模式每房配置: {val}"
                    elif bs_room_key == '客厅':
                         qty = val
                         formula_str = f"户级物料(仅客厅计算): {val}"
                    else:
                        qty = 0
                        formula_str = f"户级物料(非客厅不计算)"
                elif '个/厨房数' in unit:
                    qty = val * context['kitchen_count']
                    formula_str = f"指标 {val} × 厨房数 {context['kitchen_count']}"
                elif '个/100㎡' in unit:
                    qty = val * (context['floor_area'] / 100.0)
                    formula_str = f"指标 {val} × (面积 {context['floor_area']:.2f}㎡ / 100)"
                
                if qty > 0:
                    # 更新上下文
                    if '电工管' in item_name and '弯头' not in item_name and '直通' not in item_name:
                        context['electrical_pipe_len'] += qty
                    if '弱电管' in item_name and '弯头' not in item_name and '直通' not in item_name:
                        context['weak_electric_pipe_len'] += qty
                    if '新风风管' in item_name:
                        context['fresh_air_pipe_len'] += qty
                    
                    # 用户修改：底盒数量不再由开关插座累加，而是直接读取BS.json中"底盒"项的计算结果
                    # "杯梳"等依赖项将根据此数量计算
                    if item_name == '底盒':
                         context['box_count'] += qty

                    results.append({
                        'name': item_name, 
                        'specification': spec,
                        'quantity': round(qty, 2),
                        'unit': unit.split('/')[0] if '/' in unit else unit, # 简化单位显示
                        'category': category,
                        'layer_type': '机电安装', # 统一标记
                        'material_code': code,
                        'calculation_formula': f"{formula_str} = {round(qty, 2)}"
                    })

            # 第二遍遍历：计算依赖项 (换算说明)
            for item_name, item_data in items_to_process:
                if '换算说明' not in item_data:
                    continue
                
                qty = 0.0
                unit = item_data.get('unit', '')
                spec = item_data.get('规格', '')
                code = item_data.get('code', '') # 获取BS.json中定义的物料编码
                formula_desc = item_data.get('换算说明', '')
                formula_str = ""
                
                # 解析公式逻辑
                L = 0.0
                divisor = 1.0
                
                if '电工管' in item_name:
                    L = context['electrical_pipe_len']
                    if '弯头' in item_name: divisor = 5.0
                    elif '直通' in item_name: divisor = 3.0
                elif '弱电管' in item_name:
                    L = context['weak_electric_pipe_len']
                    if '弯头' in item_name: divisor = 5.0
                    elif '直通' in item_name: divisor = 3.0
                elif '风管' in item_name:
                    L = context['fresh_air_pipe_len']
                    if '弯头' in item_name: divisor = 5.0
                
                if L > 0:
                    qty = round(L / divisor)
                    formula_str = f"{formula_desc} (基数L={L:.2f}m)"
                    
                if qty > 0:
                    results.append({
                        'name': item_name,
                        'specification': spec,
                        'quantity': qty,
                        'unit': unit,
                        'category': category,
                        'layer_type': '机电安装',
                        'material_code': code,
                        'calculation_formula': formula_str
                    })

            # 第三遍遍历：计算依赖项 (个/底盒) - 如杯梳
            for item_name, item_data in items_to_process:
                unit = item_data.get('unit', '')
                if '个/底盒' in unit:
                     # Logic similar to first pass to get indicator
                    indicator = item_data.get(project_type)
                    if indicator is None: continue
                    
                    val = 0.0
                    if isinstance(indicator, (int, float)):
                        val = float(indicator)
                    elif isinstance(indicator, dict):
                        val = float(indicator.get(bs_room_key, indicator.get("其余", 0)))
                    
                    qty = val * context['box_count']
                    formula_str = f"指标 {val} × 底盒数 {context['box_count']}"
                    
                    code = item_data.get('code', '') # 获取BS.json中定义的物料编码

                    if qty > 0:
                         results.append({
                            'name': item_name,
                            'specification': item_data.get('规格', ''),
                            'quantity': round(qty,0),
                            'unit': '个',
                            'category': category,
                            'layer_type': '机电安装',
                            'material_code': code,
                            'calculation_formula': f"{formula_str} = {round(qty, 2)}"
                        })
        
        return results


    
    def _lookup_materials(self, material_dict: Dict[str, List[str]], processed_data: ProcessedData) -> List[Dict[str, Any]]:
        """
        在数据库中查找物料信息（复用langchain_service的逻辑）
        
        Args:
            material_dict: 按分类的物料字典
            processed_data: 处理后的数据
            
        Returns:
            找到的物料列表
        """
        found_materials = []
        
        for category, materials in material_dict.items():
            for material_name in materials:
                # 在数据库中搜索物料
                search_results = self.material_database.search_materials(
                    keyword=material_name,
                    material_type=None,
                    usage_purpose=""
                )
                
                if search_results:
                    # 选择最佳匹配的材料规格
                    best_material = self._select_material_spec(search_results, processed_data)
                    if best_material:
                        found_materials.append({
                            'material': best_material,
                            'category': category.replace('_materials', ''),  # ceiling_materials -> ceiling
                            'search_name': material_name
                        })
        
        return found_materials
    
    def _select_material_spec(self, materials: List, processed_data: ProcessedData):
        """
        选择最适合的材料规格（复用langchain_service的逻辑）
        
        Args:
            materials: 搜索到的材料列表
            processed_data: 处理后的数据
            
        Returns:
            选择的材料规格
        """
        if not materials:
            return None
        
        # 简单选择第一个匹配的材料
        # 在实际应用中，这里可以根据项目特点选择最合适的规格
        return materials[0]
    
    def _calculate_materials(self, found_materials: List[Dict[str, Any]], processed_data: ProcessedData) -> List[Dict[str, Any]]:
        """
        计算物料用量（复用langchain_service的逻辑）
        
        Args:
            found_materials: 找到的物料列表
            processed_data: 处理后的数据
            
        Returns:
            计算结果列表
        """
        calculated_materials = []
        
        for material_info in found_materials:
            material = material_info['material']
            category = material_info['category']
            
            # 根据类别确定计算面积
            if category == 'ceiling':
                area = processed_data.contour_data.ceiling_area
            elif category == 'wall':
                area = processed_data.contour_data.wall_area
            elif category == 'floor':
                area = processed_data.contour_data.floor_area
            else:
                area = 0
            
            # 计算周长（用于某些材料）
            perimeter = getattr(processed_data.contour_data, 'perimeter', 0)
            length = getattr(processed_data.dimensions, 'length', 0)
            
            # 使用MaterialCalculator计算用量
            try:
                calculation_result = self.material_calculator.calculate_material_quantity(
                    material_code=material.code,
                    area=area,
                    length=length,
                    perimeter=perimeter,
                    section=category
                )
                
                if calculation_result:
                    calculated_materials.append({
                        'material': material,
                        'calculation': calculation_result,
                        'category': category,
                        'area_used': area
                    })
                    
            except Exception as e:
                print(f"材料计算失败 {material.name}: {e}")
                continue
        
        return calculated_materials
    
    def _format_simple_bom_output(self, calculated_materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        格式化输出结果，返回包含物料清单的完整数据结构
        
        Args:
            calculated_materials: 计算结果列表
            
        Returns:
            包含物料清单的完整数据结构
        """
        bom_items = []
        categories = set()
        
        for item in calculated_materials:
            # 初始化变量
            name = ''
            spec = ''
            qty = 0
            unit = ''
            notes = ''
            mat_code = ''
            calc_formula = ''
            
            # 情况1：来自装修物料计算（包含material和calculation对象）
            if 'material' in item and 'calculation' in item:
                material = item['material']
                calculation = item['calculation']
                
                # 提取物料规格信息，确保是字符串格式
                spec = getattr(material, 'specification', '') or getattr(material, 'spec', '') or ''
                if isinstance(spec, list):
                    spec = ', '.join(spec) if spec else ''
                elif not isinstance(spec, str):
                    spec = str(spec) if spec else ''
                
                name = getattr(material, 'name', '')
                qty = getattr(calculation, 'quantity', 0)
                unit = getattr(calculation, 'unit', '')
                notes = getattr(material, 'notes', '') or ''
                mat_code = getattr(calculation, 'material_code', getattr(material, 'code', ''))
                calc_formula = getattr(calculation, 'calculation_formula', '')
            
            # 情况2：来自机电物料计算（扁平字典结构）
            else:
                name = item.get('name', '')
                spec = item.get('specification', '')
                qty = item.get('quantity', 0)
                unit = item.get('unit', '')
                notes = item.get('notes', '')
                mat_code = item.get('material_code', '')
                calc_formula = item.get('calculation_formula', '')

            # 收集类别信息
            category = item.get('category', '')
            if category:
                categories.add(category)
            
            bom_item = {
                'name': name,
                'specification': spec,
                'quantity': qty,
                'unit': unit,
                'category': category,
                'layer_type': item.get('layer_type', ''),
                'notes': notes,
                # 新增：物料编码与计算公式，匹配前端映射
                'material_code': mat_code,
                'calculation_formula': calc_formula
            }
            
            bom_items.append(bom_item)
        
        # 返回完整的数据结构，包含前端期望的所有字段
        return {
            'materials': bom_items,
            'summary': {
                'total_items': len(bom_items),
                'categories': sorted(list(categories)),
                'generation_method': 'service_calculation'
            }
        }
    
    def _generate_missing_materials_simple(self, missing_materials: List[str], processed_data: ProcessedData, name_to_category: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        使用LLM为未找到的物料生成简化的BOM项（仅包含前端需要的字段）
        """
        if not missing_materials:
            return []
        if not self.llm:
            print("[缺失物料补充] LLM未初始化，跳过补充")
            return []
        
        # 构建提示词
        messages = self._build_missing_materials_prompt(missing_materials, processed_data)
        
        # 调用LLM
        response = self.llm.invoke(messages)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # 解析为简化条目
        return self._parse_ai_generated_materials_simple(response_text, name_to_category)
    
    def _build_missing_materials_prompt(self, missing_materials: List[str], processed_data: ProcessedData):
        """构建缺失物料的AI提示词，输出按“物料编码|描述|规格|单位|数量|计算公式|材料用途|备注”一行一个"""
        materials_str = '、'.join(missing_materials)
        system_prompt = "你是一名专业的建筑工程造价师。请为以下未在物料库中找到的物料生成详细的BOM清单项。"
        human_prompt = f"""
项目信息：
- 房间尺寸：长{processed_data.dimensions.length}m × 宽{processed_data.dimensions.width}m × 高{processed_data.dimensions.height}m
- 地面面积：{processed_data.contour_data.floor_area:.2f}m²
- 天花面积：{processed_data.contour_data.ceiling_area:.2f}m²
- 墙体面积：{processed_data.contour_data.wall_area:.2f}m²

未找到的物料：{materials_str}

请为每个物料生成BOM清单项，格式如下：
物料编码|描述|规格|单位|数量|计算公式|材料用途|备注

要求：
1. 规格要包含关键参数（如系列、厚度等）；
2. 数量计算要合理，考虑损耗；
3. 每行一个物料，用换行分隔；
"""
        return [SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)]
    
    def _parse_ai_generated_materials_simple(self, response_text: str, name_to_category: Dict[str, str]) -> List[Dict[str, Any]]:
        """解析AI生成的物料清单为前端简化结构"""
        items: List[Dict[str, Any]] = []
        lines = (response_text or '').strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or '|' not in line:
                continue
            try:
                parts = [p.strip() for p in line.split('|')]
                # 物料编码|描述|规格|单位|数量|计算公式|材料用途|备注
                mat_code = parts[0] if len(parts) > 0 else ''
                desc = parts[1] if len(parts) > 1 else ''
                spec = parts[2] if len(parts) > 2 else ''
                unit = parts[3] if len(parts) > 3 else ''
                qty_raw = parts[4] if len(parts) > 4 else '0'
                calc_formula = parts[5] if len(parts) > 5 else ''
                usage = parts[6] if len(parts) > 6 else ''
                notes_text = parts[7] if len(parts) > 7 else ''
                
                # 尝试解析为数值
                try:
                    quantity = float(str(qty_raw).replace(',', '').strip())
                except Exception:
                    quantity = 0.0
                
                # 根据名称推断分类
                category = name_to_category.get(desc, '')
                
                items.append({
                    'name': desc,
                    'specification': spec,
                    'quantity': quantity,
                    'unit': unit,
                    'category': category,
                    'layer_type': '',
                    'notes': notes_text or 'AI补充生成',
                    'material_code': mat_code,
                    'calculation_formula': calc_formula,
                    'usage': usage
                })
            except Exception as e:
                print(f"[解析缺失物料] 行解析失败: {line}, 错误: {e}")
                continue
        return items
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            Dict: 服务状态信息
        """
        try:
            # 检查各个组件状态
            material_count = len(self.material_database.search_materials())
            llm_status = self.llm is not None
            
            return {
                'success': True,
                'data': {
                    'service_name': 'MaterialCalculationService',
                    'status': 'running',
                    'material_database_count': material_count,
                    'llm_available': llm_status,
                    'components': {
                        'config_manager': 'initialized',
                        'data_processor': 'initialized',
                        'material_database': 'initialized',
                        'material_calculator': 'initialized',
                        'bom_generator': 'initialized'
                    }
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': '服务状态检查失败'
            }
