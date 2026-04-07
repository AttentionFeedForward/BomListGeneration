import os

# 在导入任何模块之前设置所有必要的环境变量
# os.environ['FLAGS_allocator_strategy'] = 'auto_growth'
# os.environ['FLAGS_fraction_of_gpu_memory_to_use'] = '0.1'
# os.environ['FLAGS_use_mkldnn'] = 'False'
# os.environ['FLAGS_use_mkldnn_bfloat16'] = 'False'
# os.environ['FLAGS_use_mkldnn_int8'] = 'False'
# os.environ['FLAGS_use_onednn'] = '0'
# os.environ['PADDLE_DISABLE_ONEDNN'] = '1'
# os.environ['MKLDNN_VERBOSE'] = '0'
# os.environ['OMP_NUM_THREADS'] = '1'
import numpy as np
from typing import List, Tuple, Dict
import math
import json
import re
import cv2
import easyocr
# from paddleocr import PaddleOCR




class HistogramModeFilter:
    """
    基于直方图众数的异常值过滤器
    用于过滤比例因子中的异常值，提高平均值计算的准确性
    """
    
    def __init__(self, bin_width: float = None, min_mode_ratio: float = 0.15):
        """
        初始化过滤器
        
        Args:
            bin_width: 直方图区间宽度，None时自动计算
            min_mode_ratio: 众数区间最小数据比例
        """
        self.bin_width = bin_width
        self.min_mode_ratio = min_mode_ratio
    
    def _calculate_optimal_bin_width(self, data: List[float]) -> float:
        """
        计算最优区间宽度
        使用改进的自适应方法，专门针对异常值检测优化
        """
        if len(data) < 2:
            return 0.1
        
        # 先用IQR方法粗略过滤异常值
        q75 = np.percentile(data, 75)
        q25 = np.percentile(data, 25)
        iqr = q75 - q25
        
        if iqr > 0:
            # 使用IQR过滤明显的异常值
            lower_fence = q25 - 1.5 * iqr
            upper_fence = q75 + 1.5 * iqr
            clean_data = [x for x in data if lower_fence <= x <= upper_fence]
        else:
            clean_data = data
        
        if len(clean_data) < 2:
            clean_data = data
        
        # 基于"干净"数据计算区间宽度
        clean_std = np.std(clean_data)
        clean_range = max(clean_data) - min(clean_data)
        
        if clean_std == 0:
            return clean_range / 10 if clean_range > 0 else 0.1
        
        # 使用标准差的一定比例作为区间宽度
        # 这样可以确保正常数据不会被分散到太多区间
        bin_width = clean_std / 3  # 约3倍标准差范围内的数据会被分到相邻区间
        
        # 确保区间宽度合理
        min_width = clean_range / 20  # 最多20个区间
        max_width = clean_range / 3   # 最少3个区间
        
        if min_width > 0:
            bin_width = max(min_width, min(bin_width, max_width))
        
        return bin_width if bin_width > 0 else 0.1
    
    def _create_histogram(self, data: List[float], bin_width: float) -> Tuple[List[float], List[int], List[List[float]]]:
        """
        创建直方图
        
        Returns:
            bin_edges: 区间边界
            bin_counts: 每个区间的计数
            bin_values: 每个区间包含的原始数据
        """
        if not data:
            return [], [], []
        
        min_val = min(data)
        max_val = max(data)
        
        # 创建区间边界
        n_bins = math.ceil((max_val - min_val) / bin_width) + 1
        bin_edges = [min_val + i * bin_width for i in range(n_bins + 1)]
        
        # 初始化计数和数据容器
        bin_counts = [0] * n_bins
        bin_values = [[] for _ in range(n_bins)]
        
        # 将数据分配到各个区间
        for value in data:
            # 找到对应的区间索引
            bin_index = min(int((value - min_val) / bin_width), n_bins - 1)
            bin_counts[bin_index] += 1
            bin_values[bin_index].append(value)
        
        return bin_edges, bin_counts, bin_values
    
    def _find_mode_bin(self, bin_counts: List[int], bin_values: List[List[float]], 
                       total_count: int) -> Tuple[int, List[float]]:
        """
        找到众数区间
        
        Returns:
            mode_bin_index: 众数区间索引
            mode_values: 众数区间内的数据
        """
        if not bin_counts:
            return -1, []
        
        # 找到最大频次
        max_count = max(bin_counts)
        
        # 找到所有最大频次的区间
        max_bins = [i for i, count in enumerate(bin_counts) if count == max_count]
        
        # 如果只有一个众数区间，直接返回
        if len(max_bins) == 1:
            mode_bin_index = max_bins[0]
        else:
            # 如果有多个相同频次的区间，选择最接近数据中位数的区间
            all_data = []
            for values in bin_values:
                all_data.extend(values)
            median_val = np.median(all_data)
            
            best_bin = max_bins[0]
            min_distance = float('inf')
            
            for bin_idx in max_bins:
                if bin_values[bin_idx]:
                    bin_center = np.mean(bin_values[bin_idx])
                    distance = abs(bin_center - median_val)
                    if distance < min_distance:
                        min_distance = distance
                        best_bin = bin_idx
            
            mode_bin_index = best_bin
        
        mode_values = bin_values[mode_bin_index]
        
        # 检查众数区间是否满足最小比例要求
        mode_ratio = len(mode_values) / total_count
        if mode_ratio < self.min_mode_ratio:
            print(f"⚠️  警告: 众数区间数据比例 {mode_ratio:.2%} 低于最小要求 {self.min_mode_ratio:.2%}")
        
        return mode_bin_index, mode_values
    
    def filter_outliers(self, data: List[float], deviation_threshold: float = 0.05) -> Dict:
        """
        使用直方图众数方法过滤异常值
        
        Args:
            data: 输入数据列表
            deviation_threshold: 偏差阈值（相对于众数平均值的比例）
            
        Returns:
            包含过滤结果的字典
        """
        if not data:
            return {
                'original_data': [],
                'filtered_data': [],
                'excluded_data': [],
                'mode_values': [],
                'statistics': {
                    'original_count': 0,
                    'filtered_count': 0,
                    'excluded_count': 0,
                    'original_mean': 0,
                    'filtered_mean': 0,
                    'mode_mean': 0
                }
            }
        
        # 如果数据太少，直接返回原始数据
        if len(data) <= 2:
            return {
                'original_data': data,
                'filtered_data': data,
                'excluded_data': [],
                'mode_values': data,
                'statistics': {
                    'original_count': len(data),
                    'filtered_count': len(data),
                    'excluded_count': 0,
                    'original_mean': np.mean(data),
                    'filtered_mean': np.mean(data),
                    'mode_mean': np.mean(data),
                    'mode_std': np.std(data) if len(data) > 1 else 0,
                    'filter_range': (min(data), max(data)),
                    'mode_ratio': 1.0
                },
                'histogram_info': {
                    'bin_width': 0,
                    'n_bins': 0,
                    'mode_bin_index': 0,
                    'mode_bin_count': len(data)
                }
            }
        
        # 计算区间宽度
        bin_width = self.bin_width if self.bin_width else self._calculate_optimal_bin_width(data)
        
        # 创建直方图
        bin_edges, bin_counts, bin_values = self._create_histogram(data, bin_width)
        
        # 找到众数区间
        mode_bin_index, mode_values = self._find_mode_bin(bin_counts, bin_values, len(data))
        
        if not mode_values:
            # 如果没有找到有效的众数区间，返回原始数据
            return {
                'original_data': data,
                'filtered_data': data,
                'excluded_data': [],
                'mode_values': data,
                'statistics': {
                    'original_count': len(data),
                    'filtered_count': len(data),
                    'excluded_count': 0,
                    'original_mean': np.mean(data),
                    'filtered_mean': np.mean(data),
                    'mode_mean': np.mean(data)
                },
                'histogram_info': {
                    'bin_width': bin_width,
                    'n_bins': len(bin_counts),
                    'mode_bin_index': mode_bin_index,
                    'mode_bin_count': 0
                }
            }
        
        # 计算众数区间的平均值
        mode_mean = np.mean(mode_values)
        
        # 改进的过滤逻辑：结合众数区间特征和用户指定的偏差阈值
        mode_std = np.std(mode_values) if len(mode_values) > 1 else 0
        
        # 方法1：基于用户指定的偏差阈值（相对阈值）
        relative_threshold = mode_mean * deviation_threshold
        
        # 方法2：基于众数区间的标准差（绝对阈值）
        if mode_std > 0:
            std_threshold = mode_std * 2.5  # 2.5倍标准差，覆盖约99%的正常数据
        else:
            std_threshold = mode_mean * 0.01  # 如果标准差为0，使用1%作为最小阈值
        
        # 选择较大的阈值，确保不会过度过滤
        threshold = max(relative_threshold, std_threshold)
        
        # 设置合理的最小阈值，避免过度严格
        min_threshold = mode_mean * 0.01  # 最小1%的相对阈值
        threshold = max(threshold, min_threshold)
        
        lower_bound = mode_mean - threshold
        upper_bound = mode_mean + threshold
        
        # 分类数据
        filtered_data = []
        excluded_data = []
        
        for value in data:
            if lower_bound <= value <= upper_bound:
                filtered_data.append(value)
            else:
                excluded_data.append(value)
        
        # 计算统计信息
        statistics = {
            'original_count': len(data),
            'filtered_count': len(filtered_data),
            'excluded_count': len(excluded_data),
            'original_mean': np.mean(data),
            'filtered_mean': np.mean(filtered_data) if filtered_data else 0,
            'mode_mean': mode_mean,
            'mode_std': np.std(mode_values) if len(mode_values) > 1 else 0,
            'filter_range': (lower_bound, upper_bound),
            'mode_ratio': len(mode_values) / len(data)
        }
        
        histogram_info = {
            'bin_width': bin_width,
            'n_bins': len(bin_counts),
            'mode_bin_index': mode_bin_index,
            'mode_bin_count': len(mode_values),
            'bin_edges': bin_edges,
            'bin_counts': bin_counts,
            'bin_values': bin_values
        }
        
        return {
            'original_data': data,
            'filtered_data': filtered_data,
            'excluded_data': excluded_data,
            'mode_values': mode_values,
            'statistics': statistics,
            'histogram_info': histogram_info
        }

class DimensionMatcher:
    def __init__(self, angle_threshold: float = 2.0, enable_scale_filter: bool = True, 
                 scale_deviation_threshold: float = 0.05, collinear_threshold: float = 3.0):
        """
        初始化尺寸匹配器
        
        Args:
            angle_threshold: 角度阈值（度），用于判断线段是否为水平或垂直
            enable_scale_filter: 是否启用比例因子过滤
            scale_deviation_threshold: 比例因子过滤的偏差阈值
            collinear_threshold: 共线性判断的距离阈值（像素），用于判断多个点是否共线
        """
        self.angle_threshold = math.radians(angle_threshold)  # 转换为弧度
        self.enable_scale_filter = enable_scale_filter
        self.scale_deviation_threshold = scale_deviation_threshold
        self.collinear_threshold = collinear_threshold  # 共线性阈值（像素）
        
        # 初始化直方图众数过滤器
        if enable_scale_filter:
            self.scale_filter = HistogramModeFilter()
        
        # OCR实例缓存
        self.ocr_reader = None
    
    def _initialize_ocr(self):
        """
        简单的CPU版本OCR初始化
        
        Returns:
            PaddleOCR实例
        """
        if self.ocr_reader is not None:
            return self.ocr_reader
        
        # 直接使用CPU版本OCR，启用角度分类器
        # self._ocr_instance = PaddleOCR(
        #     use_angle_cls=True, lang="ch", enable_mkldnn=False
        # )

        self.ocr_reader = easyocr.Reader(['ch_sim', 'en']) # 中英文
        return self.ocr_reader
    
    def load_data_from_json(self, json_file_path: str) -> Tuple[List[Tuple[int, int]], List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]]]:
        """
        从JSON文件加载dimension_point和dimension_text数据
        
        Args:
            json_file_path: JSON文件路径
            
        Returns:
            Tuple[scattered_points, text_boxes]
            - scattered_points: List[Tuple[int, int]] - dimension_point的bbox_center
            - text_boxes: List[Tuple[Tuple[int, int], ...]] - dimension_text的bbox四个角点
        """
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        scattered_points = []
        text_boxes = []
        
        # 解析检测结果
        detections = data.get('detections', [])
        
        for detection in detections:
            class_name = detection.get('class_name', '')
            
            if class_name == 'dimension_point':
                # 提取bbox_center作为散落端点
                bbox_center = detection.get('bbox_center', [])
                if len(bbox_center) == 2:
                    scattered_points.append((int(bbox_center[0]), int(bbox_center[1])))
            
            elif class_name == 'dimension_text':
                # 提取bbox作为文本框
                bbox = detection.get('bbox', [])
                if len(bbox) == 4:
                    # bbox格式: [x1, y1, x2, y2] -> 转换为四个角点
                    x1, y1, x2, y2 = bbox
                    text_box = (
                        (int(x1), int(y1)),  # 左上角
                        (int(x2), int(y1)),  # 右上角
                        (int(x2), int(y2)),  # 右下角
                        (int(x1), int(y2))   # 左下角
                    )
                    text_boxes.append(text_box)
        
        return scattered_points, text_boxes
    
    def extract_text_with_ocr(self, image_path: str, text_boxes: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]]) -> List[str]:
        """
        使用OCR识别文本框中的数字，支持竖向文本的旋转识别
        
        Args:
            image_path: 图像文件路径
            text_boxes: 文本框列表
            
        Returns:
            OCR识别结果列表，与text_boxes一一对应
        """
        # 智能GPU/CPU选择
        ocr_reader = self._initialize_ocr()

        if not os.path.exists(image_path):
            print(f"Warning: Image file not found: {image_path}")
            return [""] * len(text_boxes)
        
        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            print(f"Warning: Failed to load image: {image_path}")
            return [""] * len(text_boxes)
        
        ocr_texts = []
        
        for text_box in text_boxes:
            try:
                # 计算文本框的边界矩形
                x_coords = [point[0] for point in text_box]
                y_coords = [point[1] for point in text_box]
                x1, x2 = min(x_coords), max(x_coords)
                y1, y2 = min(y_coords), max(y_coords)
                
                # 确保坐标在图像范围内，使用固定3像素扩展
                h, w = image.shape[:2]
                x1_ = max(0, min(x1 - 6, w-1))
                x2_ = max(0, min(x2 + 6, w-1))
                y1_ = max(0, min(y1 - 3, h-1))
                y2_ = max(0, min(y2 + 3, h-1))
                
                # 裁剪文本区域
                text_region = image[y1_:y2_, x1_:x2_]
                
                # 计算文本框的宽度和高度
                box_width = x2 - x1
                box_height = y2 - y1
                
                # 判断是否为竖向文本框（高度 > 宽度 * 1.1）
                is_vertical_text = box_height > box_width * 1.05
                
                # 对图像进行放大处理以提高小字符识别率（如'和"以及数字7/1的混淆）
                if text_region.shape[0] > 0 and text_region.shape[1] > 0:
                    # 动态调整放大倍数：图像越小，放大倍数越大
                    h, w = text_region.shape[:2]
                    min_dim = min(h, w)
                    if min_dim < 30:
                        scale_factor = 3.0
                    elif min_dim < 60:
                        scale_factor = 2.5
                    else:
                        scale_factor = 2.0
                        
                    text_region = cv2.resize(text_region, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
                
                    # 图像增强处理：二值化 + 腐蚀（加粗笔画）
                    # 这有助于识别笔画较细的数字如 7，并减少背景噪声
                    # 使用自适应阈值，对光照不均或线条深浅不一更鲁棒
                    enhanced_result = None
                    try:
                        if len(text_region.shape) == 3:
                            gray = cv2.cvtColor(text_region, cv2.COLOR_BGR2GRAY)
                        else:
                            gray = text_region
                        
                        # 增加对比度
                        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
                        
                        # 自适应二值化
                        # blockSize=11, C=2 是常用参数，适合提取文字
                        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                     cv2.THRESH_BINARY, 11, 2)
                        
                        # 腐蚀（加粗黑色笔画）
                        # 使用十字核，迭代1次
                        kernel = np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], np.uint8) 
                        eroded = cv2.erode(binary, kernel, iterations=1)
                        
                        # 转回BGR
                        text_region_enhanced = cv2.cvtColor(eroded, cv2.COLOR_GRAY2BGR)
                        
                        # 对增强后的图像进行识别
                        enhanced_result = self._ocr_recognize_region(ocr_reader, text_region_enhanced)
                    # 可以在 raw_text 中添加标记，但为了保持逻辑一致性，这里暂不修改 raw_text
                    
                    except Exception as e:
                        print(f"Warning: Image enhancement failed: {e}")

                # 进行原始识别
                results = []
                original_result = self._ocr_recognize_region(ocr_reader, text_region)
                results.append(original_result)
                
                if enhanced_result:
                    results.append(enhanced_result)
                
                # 如果是竖向文本框，额外进行旋转识别（尝试顺时针和逆时针）
                if is_vertical_text and text_region.size > 0:
                    try:
                        # 顺时针旋转90度 (Top-to-Bottom text)
                        rotated_cw = cv2.rotate(text_region, cv2.ROTATE_90_CLOCKWISE)
                        result_cw = self._ocr_recognize_region(ocr_reader, rotated_cw)
                        results.append(result_cw)
                        
                        # 逆时针旋转90度 (Bottom-to-Top text)
                        rotated_ccw = cv2.rotate(text_region, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        result_ccw = self._ocr_recognize_region(ocr_reader, rotated_ccw)
                        results.append(result_ccw)
                        
                        # 对增强后的图像也尝试旋转识别
                        if enhanced_result:
                            enhanced_cw = cv2.rotate(text_region_enhanced, cv2.ROTATE_90_CLOCKWISE)
                            result_enhanced_cw = self._ocr_recognize_region(ocr_reader, enhanced_cw)
                            results.append(result_enhanced_cw)
                            
                            enhanced_ccw = cv2.rotate(text_region_enhanced, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            result_enhanced_ccw = self._ocr_recognize_region(ocr_reader, enhanced_ccw)
                            results.append(result_enhanced_ccw)
                        
                    except Exception as e:
                        print(f"Warning: Rotation OCR failed for text box {text_box}: {e}")
                
                # 选择最佳结果
                # 优先策略：
                # 1. 优先选择包含英尺英寸符号的结果 (', ")
                # 2. 其次选择置信度高的结果
                best_result = results[0]
                
                def has_dimension_symbols(text):
                    return any(c in text for c in "'\"‘’“”")
                
                # 找出所有包含尺寸符号的结果
                symbol_results = [r for r in results if has_dimension_symbols(r.get('raw_text', ''))]
                
                if symbol_results:
                    # 如果有带符号的结果，从中选置信度最高的
                    best_result = max(symbol_results, key=lambda x: x['avg_confidence'])
                else:
                    # 否则直接选置信度最高的
                    best_result = max(results, key=lambda x: x['avg_confidence'])

                # 非数值识别结果不包含'text'键，这里安全读取并回退为空串
                # 确保返回结果包含 raw_text 字段
                if 'raw_text' not in best_result:
                    best_result['raw_text'] = best_result.get('text', '')
                
                # 返回包含详细信息的字典
                ocr_texts.append(best_result)

            except Exception as e:
                print(f"Warning: OCR failed for text box {text_box}: {e}")
                ocr_texts.append({'text': "", 'type': 'unknown', 'raw_text': "", 'avg_confidence': 0.0})
        
        return ocr_texts            
                        # 比较两次识别的置信度，选择更好的结果
            
    
    def _parse_inch_value(self, text):
        """
        解析英寸字符串，支持整数、小数、分数
        格式如: "10", "10.5", "3/4", "10 3/4", "10-3/4"
        """
        if not text:
            return 0.0
        
        # Clean up
        text = text.strip().replace('"', '').replace("''", "")
        # Replace dots and underscores with spaces, as they are likely noise or separators
        text = text.replace('.', ' ').replace('_', ' ')
        # Strip leading hyphens/spaces again
        text = text.strip(" -")
        
        if not text:
            return 0.0
        
        try:
            # Pattern 1: Integer + Fraction (e.g. "10 3/4", "10-3/4")
            match_mixed = re.match(r'^(\d+)[-\s]+(\d+)/(\d+)$', text)
            if match_mixed:
                integer = float(match_mixed.group(1))
                numerator = float(match_mixed.group(2))
                denominator = float(match_mixed.group(3))
                if denominator != 0:
                    return integer + (numerator / denominator)
                return integer
                
            # Pattern 2: Fraction only (e.g. "3/4")
            match_frac = re.match(r'^(\d+)/(\d+)$', text)
            if match_frac:
                numerator = float(match_frac.group(1))
                denominator = float(match_frac.group(2))
                if denominator != 0:
                    return numerator / denominator
                return 0.0
                
            # Pattern 3: Decimal/Integer (e.g. "10.5", "10")
            return float(text)
        except ValueError:
            return 0.0

    def _ocr_recognize_region(self, ocr_reader, text_region):
        """
        对文本区域进行OCR识别并返回结果和置信度
        
        Args:
            ocr: PaddleOCR实例
            text_region: 文本区域图像
            
        Returns:
            dict: 包含识别文本和平均置信度的字典
        """
        try:
            
            ocr_result = ocr_reader.readtext(text_region)
            
            text_lines = ""
            confidences = []
            
            for line in ocr_result:
                if line:
                    text = str(line[1])  # 文本内容，强制转换为字符串
                    score = line[2]      # 置信度
                    
                    # 修改：放宽过滤条件，特别是针对包含符号的情况
                    # 许多时候 ' 和 " 的置信度较低，如果被过滤会导致 13' 变成 13
                    # 同时保留 / 用于分数解析
                    # 进一步降低阈值以保留更多符号信息，特别是对于尺寸标注中的关键符号
                    if score > 0.3 or (score > 0.01 and any(c in text for c in "'\"‘’“”/-")):
                        # 移除原有的 '/' 替换为 '7' 的逻辑，以支持分数 (如 3/4)
                        text_lines += text
                        confidences.append(score)
            
            # 计算平均置信度
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # 仅保留数值型（整数或小数）的文本
            normalized_text = text_lines.strip()
            
            # 1. 尝试匹配纯数值 (现有逻辑)
            # 注意：如果包含 / 或 ' 等符号，这里会返回 False
            # 注意：如果包含中间的 - (如 30-0)，也会返回 False
            is_numeric = bool(re.fullmatch(r'[+-]?\d+(?:\.\d+)?', normalized_text))
            
            final_text = None
            
            if is_numeric:
                final_text = normalized_text
            else:
                # 2. 尝试匹配英尺-英寸格式 (含分数支持)
                # 归一化符号：处理中文引号和重复单引号
                fi_text = normalized_text.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"').replace("''", '"')
                
                # 正则匹配：优先提取英尺部分，剩余部分作为英寸处理
                # Group 1: 英尺, Group 2: 剩余的英寸字符串(可选)
                # 这种贪婪匹配方式能更好处理 "13' 10 3/4"" 这种复杂格式
                fi_match = re.search(r"(\d+)\s*'\s*(?:[-]?\s*(.*))?$", fi_text)
                
                if fi_match:
                    feet = float(fi_match.group(1))
                    inch_str = fi_match.group(2)
                    
                    # 解析英寸部分 (支持整数、小数、分数)
                    inch = 0.0
                    if inch_str:
                        # 移除末尾可能的引号
                        inch_str = inch_str.strip()
                        if inch_str.endswith('"'):
                            inch_str = inch_str[:-1]
                        inch = self._parse_inch_value(inch_str)
                        
                        # 粘连修复逻辑：如果英寸 >= 12，可能是OCR漏掉了空格导致整数和分数粘连
                        # 例如 "51/2" (25.5) -> "5 1/2" (5.5)
                        # 仅当作为英尺-英寸的英寸部分时（通常<12）才进行此修正
                        if inch >= 12:
                             # 尝试匹配 "数字+分数" 的粘连形式，如 "51/2", "103/4"
                             glue_match = re.match(r'^(\d+)(\d/\d+)$', inch_str)
                             if glue_match:
                                 try:
                                     int_part = float(glue_match.group(1))
                                     frac_val = self._parse_inch_value(glue_match.group(2))
                                     fixed_inch = int_part + frac_val
                                     # 如果修正后的英寸值合理 (<12)，则采用修正值
                                     if fixed_inch < 12:
                                         inch = fixed_inch
                                 except Exception:
                                     pass
                    
                    # 转换公式
                    mm_value = feet * 304.8 + inch * 25.4
                    final_text = f"{mm_value:.1f}" # 保留1位小数
                else:
                    # 如果没匹配到英尺格式，尝试只匹配英寸的情况 (如 10", 3/4")
                    # 只要包含 " 或者是分数格式，都尝试解析
                    inch_only_match = re.search(r"^(.*)\"$", fi_text)
                    if inch_only_match:
                        inch_str = inch_only_match.group(1)
                        inch = self._parse_inch_value(inch_str)
                        # 只有解析出有效值(>0)才认为是合法的尺寸
                        if inch > 0:
                            mm_value = inch * 25.4
                            final_text = f"{mm_value:.1f}"
                    elif '/' in fi_text:
                         # 尝试直接解析纯分数 (如 3/4) 即使没有引号
                         inch = self._parse_inch_value(fi_text)
                         if inch > 0:
                             mm_value = inch * 25.4
                             final_text = f"{mm_value:.1f}"
                    
                    # 3. 尝试匹配隐式英尺-英寸格式 (如 30-0, 30-10 3/4)
                    # 当 ' 和 " 符号丢失但保留了 - 分隔符时
                    if not final_text:
                        implicit_fi_match = re.match(r"^(\d+)\s*[-]\s*([\d\s./]+)$", fi_text)
                        if implicit_fi_match:
                             feet = float(implicit_fi_match.group(1))
                             inch_val = self._parse_inch_value(implicit_fi_match.group(2))
                             mm_value = feet * 304.8 + inch_val * 25.4
                             final_text = f"{mm_value:.1f}"

            # 仅当是数值型或成功转换后的结果才加入文本
            result = {
                'avg_confidence': avg_confidence,
                'confidences': confidences,
                'type': 'unknown',
                'raw_text': normalized_text  # 保留OCR原始识别文本
            }
            if final_text:
                result['text'] = final_text
                result['type'] = 'numeric' if is_numeric else 'feet_inch'
                
            return result
            
        except Exception as e:
            print(f"Warning: OCR recognition failed: {e}")
            return {
                'text': "",
                'type': "unknown",
                'raw_text': "",
                'avg_confidence': 0.0,
                'confidences': []
            }
    
    def load_and_process_json(self, json_file_path: str, image_path: str = None, debug: bool = False) -> Tuple[List[Tuple[int, int]], List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]], List[Dict]]:
        """
        从JSON文件加载数据并进行OCR识别的整合方法
        
        Args:
            json_file_path: JSON文件路径
            image_path: 图像文件路径，如果为None则尝试从JSON中推断
            debug: 是否输出调试信息
            
        Returns:
            Tuple[scattered_points, text_boxes, ocr_texts]
            注意：ocr_texts现在是包含详细信息(text, type, confidence)的字典列表
        """
        if debug:
            print(f"Loading data from JSON: {json_file_path}")
        
        # 加载JSON数据
        scattered_points, text_boxes = self.load_data_from_json(json_file_path)
        
        if debug:
            print(f"Loaded {len(scattered_points)} dimension points and {len(text_boxes)} text boxes")
        
        # 如果没有提供图像路径，尝试从JSON文件推断
        if image_path is None:
            # 尝试从JSON文件中获取图像路径
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                image_path = data.get('image_path', '')
                if not image_path:
                    # 如果JSON中没有图像路径，尝试使用同名的图像文件
                    base_name = os.path.splitext(json_file_path)[0]
                    for ext in ['.png', '.jpg', '.jpeg']:
                        potential_path = base_name + ext
                        if os.path.exists(potential_path):
                            image_path = potential_path
                            break
            except Exception as e:
                if debug:
                    print(f"Warning: Could not infer image path: {e}")
        
        # 进行OCR识别
        ocr_texts = []
        if image_path and os.path.exists(image_path):
            if debug:
                print(f"Performing OCR on image: {image_path}")
            ocr_texts = self.extract_text_with_ocr(image_path, text_boxes)
        else:
            if debug:
                print("Warning: No valid image path found, using empty OCR texts")
            ocr_texts = [{'text': "", 'type': 'unknown', 'raw_text': "", 'avg_confidence': 0.0}] * len(text_boxes)
        
        if debug:
            print(f"OCR completed, extracted {len([t for t in ocr_texts if t.get('text', '')])} non-empty texts")
        
        return scattered_points, text_boxes, ocr_texts
    
    def match_dimensions(self, 
                        endpoints, 
                        text_boxes: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], Tuple[int, int]]],
                        ocr_texts: List[Dict],
                        debug: bool = False) -> Dict:
        """
        匹配标注端点与数字尺寸框
        
        Args:
            endpoints: 散落端点格式: List[Tuple[int, int]] - 每个元素是(x,y)
            text_boxes: 文本框列表，每个元素是((x1,y1), (x2,y2), (x3,y3), (x4,y4)) 四个角点
            ocr_texts: OCR识别结果列表，现在是包含详细信息的字典列表
            debug: 是否输出调试信息
            
        Returns:
            匹配结果字典
        """
        # 从散落端点配对生成线段
        if debug:
            print("从散落端点配对生成线段...")
        processed_endpoints = self._pair_endpoints_to_lines(endpoints, debug)
        
        if debug:
            print(f"生成的线段数量: {len(processed_endpoints)}")
        
        matches = []
        unmatched_endpoints = processed_endpoints.copy()
        unmatched_texts = []
        
        # 计算文本框的中心点
        text_centers = []
        for box in text_boxes:
            center_x = sum(point[0] for point in box) / 4
            center_y = sum(point[1] for point in box) / 4
            text_centers.append((center_x, center_y))
        
        # 为每个文本框寻找最佳匹配的端点对
        used_text_indices = set()
        
        # 首先收集所有可能的匹配候选
        all_candidates = []
        
        for j, text_center in enumerate(text_centers):
            if j in used_text_indices:
                continue

            # 获取文本内容和类型
            current_ocr_result = ocr_texts[j]
            # 兼容处理：如果是字符串则包装成字典，如果是字典则直接使用
            if isinstance(current_ocr_result, str):
                text_content = current_ocr_result
                text_type = 'unknown'
            else:
                text_content = current_ocr_result.get('text', '')
                text_type = current_ocr_result.get('type', 'unknown')

            # 跳过空文本或非数值文本，避免无效匹配与日志噪音
            normalized_text = str(text_content).strip()
            if not normalized_text or not re.fullmatch(r'[+-]?\d+(?:\.\d+)?', normalized_text):
                if debug:
                    print(f"\n跳过非数值文本: '{text_content}' (中心: {text_center})")
                continue

            if debug:
                print(f"\n--- 为文本 '{text_content}' (类型: {text_type}, 中心: {text_center}) 寻找匹配 ---")
                
            best_match_idx = -1
            best_score = float('inf')
            
            for i, (p1, p2) in enumerate(processed_endpoints):
                line_length = self._calculate_distance(p1, p2)
                line_angle = self._calculate_angle(p1, p2)
                line_center = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                
                if debug:
                    print(f"  检查端点{i}: {p1}->{p2}, 长度: {line_length:.2f}, 角度: {math.degrees(line_angle):.2f}°")
                
                # 检查验证条件
                # 传入 text_type 以便在英尺英寸类型时放宽位置限制
                is_valid = self._is_valid_match(p1, p2, text_center, line_angle, text_type)
                if debug:
                    if not is_valid:
                        # 详细检查失败原因
                        if self._calculate_distance(p1, p2) == 0:
                            print(f"    ❌ 验证失败: 线段长度为0")
                        else:
                            is_horizontal = abs(line_angle) < self.angle_threshold or abs(line_angle - math.pi) < self.angle_threshold
                            is_vertical = abs(line_angle - math.pi/2) < self.angle_threshold or abs(line_angle + math.pi/2) < self.angle_threshold
                            if not (is_horizontal or is_vertical):
                                print(f"    ❌ 验证失败: 角度不符合水平/垂直要求 ({math.degrees(line_angle):.2f}°)")
                            elif not self._is_text_on_left_or_top(p1, p2, text_center) and text_type != 'feet_inch':
                                print(f"    ❌ 验证失败: 文本位置不在线段左方或上方")
                    else:
                        print(f"    ✅ 验证通过")
                
                if not is_valid:
                    continue
                
                # 计算匹配分数
                score = self._calculate_match_score(p1, p2, text_center, line_center, 
                                                   line_length, line_angle)
                
                if debug:
                    print(f"    匹配分数: {score:.4f}")
                
                if score < best_score:
                    best_score = score
                    best_match_idx = i
            
            if best_match_idx != -1:
                if debug:
                    print(f"  ✅ 最佳匹配: 端点{best_match_idx}, 分数: {best_score:.4f}")
                all_candidates.append({
                    'text_idx': j,
                    'endpoint_idx': best_match_idx,
                    'score': best_score
                })
            else:
                if debug:
                    print(f"  ❌ 未找到有效匹配")
        
        # 按分数排序，优先匹配分数低的
        all_candidates.sort(key=lambda x: x['score'])
        
        # 执行匹配（每个文本框只能匹配一次）
        matched_pairs = set()
        
        for candidate in all_candidates:
            text_idx = candidate['text_idx']
            endpoint_idx = candidate['endpoint_idx']
            
            if text_idx in used_text_indices:
                continue
                
            p1, p2 = processed_endpoints[endpoint_idx]
            text_center = text_centers[text_idx]
            line_length = self._calculate_distance(p1, p2)
            line_center = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            
            # 计算像素距离和实际尺寸
            pixel_distance = line_length
            try:
                # 兼容处理：ocr_texts可能是字典或字符串
                text_item = ocr_texts[text_idx]
                if isinstance(text_item, dict):
                    actual_size_str = text_item.get('text', '0')
                else:
                    actual_size_str = str(text_item)
                
                actual_size = float(actual_size_str)
                scale_factor = actual_size / pixel_distance if pixel_distance > 0 else 0
            except (ValueError, TypeError):
                actual_size = 0
                scale_factor = 0
            
            matches.append({
                'endpoint_pair': (p1, p2),
                'endpoint_idx': endpoint_idx,
                'text_idx': text_idx,
                'text_box': text_boxes[text_idx],
                'text_content': ocr_texts[text_idx],
                'pixel_distance': pixel_distance,
                'actual_size': actual_size,
                'scale_factor': scale_factor,
                'match_score': candidate['score']
            })
            
            used_text_indices.add(text_idx)
            matched_pairs.add((text_idx, endpoint_idx))
        
        # 第4步执行完成后：同一个线段（endpoint_pair）只能匹配一个文本
        # 若同一端点匹配了多个文本，保留匹配分数最低者，其余取消匹配
        if matches:
            best_by_endpoint = {}
            for m in matches:
                key = m.get('endpoint_idx') if 'endpoint_idx' in m else m['endpoint_pair']
                prev = best_by_endpoint.get(key)
                if prev is None or m['match_score'] < prev['match_score']:
                    best_by_endpoint[key] = m
            # 覆盖为筛选后的唯一匹配集合
            matches = list(best_by_endpoint.values())

        # 额外过滤：检查文本框中心与线段中心的偏差
        # 如果x,y任一坐标像素差的绝对值超过50，则取消当前匹配
        if matches:
            filtered_matches_by_center = []
            for m in matches:
                # Calculate text center
                box = m['text_box']
                center_x = sum(p[0] for p in box) / len(box)
                center_y = sum(p[1] for p in box) / len(box)
                
                # Calculate line center
                p1, p2 = m['endpoint_pair']
                line_center_x = (p1[0] + p2[0]) / 2
                line_center_y = (p1[1] + p2[1]) / 2
                
                dx = abs(center_x - line_center_x)
                dy = abs(center_y - line_center_y)
                
                if dx <= 40 and dy <= 40:
                    filtered_matches_by_center.append(m)
                elif debug:
                    print(f"  Filtering match due to center deviation: dx={dx:.1f}, dy={dy:.1f} > 40")
                    # print(f"  Text: {m.get('text_content', '')}, Line: {m['endpoint_pair']}")
            
            matches = filtered_matches_by_center

        # 重新计算已使用的文本索引与端点索引
        used_text_indices = set(m.get('text_idx') for m in matches if m.get('text_idx') is not None)
        matched_endpoint_indices = set(m.get('endpoint_idx') for m in matches if m.get('endpoint_idx') is not None)

        # 更新未匹配的端点（只保留完全未匹配的端点）
        unmatched_endpoints = [processed_endpoints[i] for i in range(len(processed_endpoints)) 
                               if i not in matched_endpoint_indices]

        # 找出未匹配的文本框（包括被取消匹配的文本）
        unmatched_texts = []
        for j in range(len(text_boxes)):
            if j not in used_text_indices:
                unmatched_texts.append({
                    'text_box': text_boxes[j],
                    'text_content': ocr_texts[j]
                })
        
        # 计算平均像素比例，使用直方图众数过滤器过滤异常值
        valid_matches = [match for match in matches if match['scale_factor'] > 0]
        
        if valid_matches and self.enable_scale_filter and len(valid_matches) > 2:
            # 提取比例因子进行过滤
            scale_factors = [match['scale_factor'] for match in valid_matches]
            
            if debug:
                print(f"\n--- 比例因子过滤 ---")
                print(f"原始比例因子: {scale_factors}")
            
            # 使用直方图众数过滤器
            filter_result = self.scale_filter.filter_outliers(
                scale_factors, 
                deviation_threshold=self.scale_deviation_threshold
            )
            
            filtered_scale_factors = filter_result['filtered_data']
            excluded_scale_factors = filter_result['excluded_data']
            
            if debug:
                print(f"过滤后比例因子: {filtered_scale_factors}")
                print(f"被排除的异常值: {excluded_scale_factors}")
                print(f"过滤统计: {filter_result['statistics']}")
            
            # 计算过滤后的平均值
            avg_scale_factor = np.mean(filtered_scale_factors) if filtered_scale_factors else 0
            
            # 标记被过滤的匹配项
            filtered_indices = set()
            for i, match in enumerate(valid_matches):
                if match['scale_factor'] in excluded_scale_factors:
                    matches[matches.index(match)]['is_outlier'] = True
                    filtered_indices.add(i)
                else:
                    matches[matches.index(match)]['is_outlier'] = False
            
            # 添加过滤信息到返回结果
            filter_info = {
                'enabled': True,
                'original_count': len(scale_factors),
                'filtered_count': len(filtered_scale_factors),
                'excluded_count': len(excluded_scale_factors),
                'original_mean': filter_result['statistics']['original_mean'],
                'filtered_mean': filter_result['statistics']['filtered_mean'],
                'mode_mean': filter_result['statistics']['mode_mean'],
                'excluded_values': excluded_scale_factors
            }
        else:
            # 不使用过滤器或数据太少
            avg_scale_factor = np.mean([match['scale_factor'] for match in valid_matches]) if valid_matches else 0
            
            # 标记所有匹配项为非异常值
            for match in matches:
                if match['scale_factor'] > 0:
                    match['is_outlier'] = False
            
            filter_info = {
                'enabled': False,
                'reason': 'disabled' if not self.enable_scale_filter else 'insufficient_data',
                'original_count': len(valid_matches),
                'filtered_count': len(valid_matches),
                'excluded_count': 0,
                'original_mean': avg_scale_factor,
                'filtered_mean': avg_scale_factor,
                'excluded_values': []
            }
        
        return {
            'matches': matches,
            'unmatched_endpoints': unmatched_endpoints,
            'unmatched_texts': unmatched_texts,
            'summary': {
                'total_matches': len(matches),
                'total_endpoints': len(processed_endpoints),
                'total_texts': len(text_boxes),
                'match_rate': len(matches) / len(text_boxes) if len(text_boxes) > 0 else 0,
                'average_scale_factor': avg_scale_factor
            },
            'scale_filter_info': filter_info
        }
    
    def _calculate_distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """计算两点之间的欧氏距离"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    def _calculate_angle(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """计算线段的倾斜角度（弧度）"""
        if p2[0] - p1[0] == 0:
            return math.pi / 2  # 垂直
        return math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    
    def _point_to_line_distance(self, point: Tuple[float, float], 
                               line_start: Tuple[float, float], 
                               line_end: Tuple[float, float]) -> float:
        """计算点到线段的距离"""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # 线段长度的平方
        l2 = (x2 - x1)**2 + (y2 - y1)**2
        
        if l2 == 0:
            return self._calculate_distance(point, line_start)
        
        # 计算投影比例
        t = max(0, min(1, ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / l2))
        
        # 计算投影点
        projection_x = x1 + t * (x2 - x1)
        projection_y = y1 + t * (y2 - y1)
        
        return self._calculate_distance(point, (projection_x, projection_y))
    
    def _point_to_line_distance_for_collinear(self, point: Tuple[int, int], 
                                             line_point1: Tuple[int, int], 
                                             line_point2: Tuple[int, int]) -> float:
        """
        计算点到无限直线的距离（用于共线性检测）
        使用点到直线距离公式：|ax + by + c| / sqrt(a² + b²)
        
        Args:
            point: 待检测的点
            line_point1: 直线上的第一个点
            line_point2: 直线上的第二个点
            
        Returns:
            点到直线的距离
        """
        x, y = point
        x1, y1 = line_point1
        x2, y2 = line_point2
        
        # 如果两个点重合，返回点到点的距离
        if x1 == x2 and y1 == y2:
            return self._calculate_distance(point, line_point1)
        
        # 直线方程 ax + by + c = 0 的系数
        a = y2 - y1
        b = x1 - x2
        c = x2 * y1 - x1 * y2
        
        # 点到直线距离公式
        distance = abs(a * x + b * y + c) / math.sqrt(a * a + b * b)
        
        return distance
    
    def _are_points_collinear(self, points: List[Tuple[int, int]]) -> bool:
        """
        检测多个点是否共线
        
        Args:
            points: 点列表，至少需要3个点
            
        Returns:
            如果所有点都共线返回True，否则返回False
        """
        if len(points) < 3:
            return True  # 少于3个点总是共线的
        
        # 使用前两个点确定基准直线
        base_point1 = points[0]
        base_point2 = points[1]
        
        # 如果前两个点重合，寻找第一个不重合的点作为基准
        for i in range(2, len(points)):
            if self._calculate_distance(base_point1, points[i]) > 0:
                base_point2 = points[i]
                break
        else:
            # 所有点都重合
            return True
        
        # 检查其余所有点到基准直线的距离
        for point in points[2:]:
            if point == base_point1 or point == base_point2:
                continue  # 跳过基准点
            
            distance = self._point_to_line_distance_for_collinear(point, base_point1, base_point2)
            if distance > self.collinear_threshold:
                return False
        
        return True
    
    def _group_collinear_points(self, points: List[Tuple[int, int]], debug: bool = False) -> List[List[Tuple[int, int]]]:
        """
        将点按照共线性进行分组（基于方向的改进算法）
        
        Args:
            points: 所有端点列表
            debug: 是否输出调试信息
            
        Returns:
            共线点组列表，每个组包含共线的点
        """
        if debug:
            print(f"\n=== 共线点分组开始（基于方向算法）===")
            print(f"输入点数量: {len(points)}")
            print(f"输入点列表: {points}")
        
        if len(points) < 2:
            return [points] if points else []
        
        # 第一步：按方向预分类
        horizontal_candidates, vertical_candidates = self._classify_points_by_direction(points, debug)
        
        all_groups = []
        
        # 第二步：处理水平线候选点
        if horizontal_candidates:
            if debug:
                print(f"\n  处理水平线候选点: {horizontal_candidates}")
            horizontal_groups = self._cluster_by_coordinate(horizontal_candidates, 'y', debug=debug)
            
            # 验证每个水平组的角度一致性
            for group in horizontal_groups:
                if len(group) >= 2:
                    # 检查组内点是否真的形成水平线
                    p1, p2 = group[0], group[1]
                    line_angle = self._calculate_angle(p1, p2)
                    # 使用1度阈值进行角度验证
                    is_horizontal = (abs(line_angle) < self.angle_threshold or 
                                   abs(line_angle - math.pi) < self.angle_threshold)
                    
                    if is_horizontal:
                        all_groups.append(group)
                        if debug:
                            print(f"    ✅ 水平组验证通过: {group} (角度: {math.degrees(line_angle):.2f}°)")
                    else:
                        if debug:
                            print(f"    ❌ 水平组验证失败: {group} (角度: {math.degrees(line_angle):.2f}°)")
        
        # 第三步：处理垂直线候选点
        if vertical_candidates:
            if debug:
                print(f"\n  处理垂直线候选点: {vertical_candidates}")
            vertical_groups = self._cluster_by_coordinate(vertical_candidates, 'x', debug=debug)
            
            # 验证每个垂直组的角度一致性
            for group in vertical_groups:
                if len(group) >= 2:
                    # 检查组内点是否真的形成垂直线
                    p1, p2 = group[0], group[1]
                    line_angle = self._calculate_angle(p1, p2)
                    # 使用1度阈值进行角度验证
                    angle_tolerance = math.radians(1.0)  # 1度阈值
                    is_vertical = (abs(line_angle - math.pi/2) < angle_tolerance or 
                                 abs(line_angle + math.pi/2) < angle_tolerance)
                    
                    if is_vertical:
                        all_groups.append(group)
                        if debug:
                            print(f"    ✅ 垂直组验证通过: {group} (角度: {math.degrees(line_angle):.2f}°)")
                    else:
                        if debug:
                            print(f"    ❌ 垂直组验证失败: {group} (角度: {math.degrees(line_angle):.2f}°)")
        
        if debug:
            print(f"\n分组结果: 共 {len(all_groups)} 个组")
            for i, group in enumerate(all_groups):
                print(f"  组 {i+1}: {group} (共{len(group)}个点)")
                if len(group) >= 2:
                    p1, p2 = group[0], group[1]
                    angle = math.degrees(self._calculate_angle(p1, p2))
                    y_coords = [p[1] for p in group]
                    x_coords = [p[0] for p in group]
                    print(f"    角度: {angle:.2f}°, y范围: {min(y_coords)}-{max(y_coords)}, x范围: {min(x_coords)}-{max(x_coords)}")
            print(f"=== 共线点分组结束 ===\n")
        
        return all_groups
    
    def _sort_points_on_line(self, points: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        对共线的点按照在直线上的位置进行排序
        
        Args:
            points: 共线的点列表
            
        Returns:
            排序后的点列表
        """
        if len(points) <= 2:
            return points
        
        # 选择第一个点作为基准点
        base_point = points[0]
        
        # 计算每个点相对于基准点的距离和方向
        point_distances = []
        for point in points:
            # 计算向量
            dx = point[0] - base_point[0]
            dy = point[1] - base_point[1]
            
            # 计算距离（带符号，用于确定方向）
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 确定方向：如果主要是水平线，用x坐标差；如果主要是垂直线，用y坐标差
            if abs(dx) >= abs(dy):  # 主要是水平方向
                signed_distance = distance if dx >= 0 else -distance
            else:  # 主要是垂直方向
                signed_distance = distance if dy >= 0 else -distance
            
            point_distances.append((signed_distance, point))
        
        # 按照带符号距离排序
        point_distances.sort(key=lambda x: x[0])
        
        # 返回排序后的点
        return [point for _, point in point_distances]
    
    def _cluster_by_coordinate(self, points: List[Tuple[int, int]], coordinate: str, 
                              threshold: float = None, debug: bool = False) -> List[List[Tuple[int, int]]]:
        """
        按指定坐标轴对点进行聚类分组
        
        Args:
            points: 点列表
            coordinate: 'x' 或 'y'，指定按哪个坐标轴聚类
            threshold: 聚类阈值，默认使用collinear_threshold
            debug: 是否输出调试信息
            
        Returns:
            聚类后的点组列表
        """
        if not points:
            return []
        
        if threshold is None:
            threshold = self.collinear_threshold
        
        coord_index = 0 if coordinate == 'x' else 1
        
        if debug:
            print(f"    按{coordinate}坐标聚类，阈值: {threshold}")
        
        # 按指定坐标排序
        sorted_points = sorted(points, key=lambda p: p[coord_index])
        
        clusters = []
        current_cluster = [sorted_points[0]]
        current_coord = sorted_points[0][coord_index]
        
        for point in sorted_points[1:]:
            point_coord = point[coord_index]
            
            # 如果坐标差值在阈值内，加入当前聚类
            if abs(point_coord - current_coord) <= threshold:
                current_cluster.append(point)
            else:
                # 否则开始新的聚类
                if len(current_cluster) >= 2:  # 只保留至少2个点的聚类
                    clusters.append(current_cluster)
                    if debug:
                        coord_values = [p[coord_index] for p in current_cluster]
                        print(f"      创建{coordinate}聚类: {current_cluster} ({coordinate}值: {coord_values})")
                
                current_cluster = [point]
                current_coord = point_coord
        
        # 处理最后一个聚类
        if len(current_cluster) >= 2:
            clusters.append(current_cluster)
            if debug:
                coord_values = [p[coord_index] for p in current_cluster]
                print(f"      创建{coordinate}聚类: {current_cluster} ({coordinate}值: {coord_values})")
        
        return clusters
    
    def _classify_points_by_direction(self, points: List[Tuple[int, int]], debug: bool = False) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        """
        将点按主要方向进行预分类（允许交叉点同时属于两个方向）
        
        Args:
            points: 所有端点列表
            debug: 是否输出调试信息
            
        Returns:
            (horizontal_candidates, vertical_candidates) 元组
        """
        if debug:
            print(f"  === 方向预分类开始 ===")
            print(f"  输入点数量: {len(points)}")
        
        if len(points) < 2:
            return points, []
        
        # 计算所有点的坐标范围
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        if debug:
            print(f"  坐标范围: x={x_range}, y={y_range}")
        
        horizontal_candidates = []
        vertical_candidates = []
        
        # 使用更智能的分类策略，允许交叉点同时属于两个方向
        for point in points:
            x, y = point
            
            # 计算该点与其他点形成水平线和垂直线的可能性
            horizontal_score = 0
            vertical_score = 0
            
            for other_point in points:
                if other_point == point:
                    continue
                
                other_x, other_y = other_point
                
                # 计算与其他点的坐标差异
                x_diff = abs(x - other_x)
                y_diff = abs(y - other_y)
                
                # 如果y坐标相近，增加水平线得分
                if y_diff <= self.collinear_threshold:
                    horizontal_score += 1
                
                # 如果x坐标相近，增加垂直线得分
                if x_diff <= self.collinear_threshold:
                    vertical_score += 1
            
            # 新的分类策略：允许交叉点同时属于两个方向
            # 设置最小得分阈值，只有得分达到阈值才加入候选
            min_score_threshold = 1  # 至少要有1个相近的点
            
            if horizontal_score >= min_score_threshold:
                horizontal_candidates.append(point)
                
            if vertical_score >= min_score_threshold:
                vertical_candidates.append(point)
            
            # 调试输出
            if debug:
                directions = []
                if horizontal_score >= min_score_threshold:
                    directions.append("水平")
                if vertical_score >= min_score_threshold:
                    directions.append("垂直")
                
                if directions:
                    direction_str = "+".join(directions)
                    print(f"    {point} -> {direction_str}候选 (得分: H={horizontal_score}, V={vertical_score})")
                else:
                    print(f"    {point} -> 孤立点 (得分: H={horizontal_score}, V={vertical_score})")
        
        if debug:
            print(f"  分类结果: 水平候选{len(horizontal_candidates)}个, 垂直候选{len(vertical_candidates)}个")
            print(f"  === 方向预分类结束 ===")
        
        return horizontal_candidates, vertical_candidates
    
    def _is_text_on_left_or_top(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                                text_center: Tuple[float, float]) -> bool:
        """
        检查文本框中心是否在线段的左方或上方
        
        对于水平线段：文本应该在线上方
        对于垂直线段：文本应该在线段左方
        """
        line_angle = self._calculate_angle(p1, p2)
        
        # 计算点到直线的有向距离
        # 直线方程: (y2-y1)x - (x2-x1)y + (x2-x1)y1 - (y2-y1)x1 = 0
        x1, y1 = p1
        x2, y2 = p2
        x, y = text_center
        
        # 直线的一般式方程: Ax + By + C = 0
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        
        # 有向距离
        signed_distance = (A * x + B * y + C) / math.sqrt(A*A + B*B) if (A*A + B*B) > 0 else 0
        
        # 判断线段类型
        is_horizontal = abs(line_angle) < self.angle_threshold or abs(line_angle - math.pi) < self.angle_threshold
        is_vertical = abs(line_angle - math.pi/2) < self.angle_threshold or abs(line_angle + math.pi/2) < self.angle_threshold
        
        if is_horizontal:
            # 水平线段：文本应该在上方（有向距离为正）
            return signed_distance > 0
        elif is_vertical:
            # 垂直线段：文本应该在左方（有向距离为负）
            return signed_distance < 0
        else:
            # 斜线段：根据角度判断，文本应该在线的"外侧"
            # 这里简化处理，要求文本在线的左上方区域
            return signed_distance > 0
    
    def _is_text_above_horizontal_line(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                                     text_center: Tuple[float, float]) -> bool:
        """
        检查文本框中心是否在水平线段的上方
        """
        # 对于水平线段，比较y坐标即可
        line_y = (p1[1] + p2[1]) / 2  # 线段的y坐标（水平线段两端点y坐标应该相近）
        text_y = text_center[1]
        
        # 在图像坐标系中，y坐标越小越靠上
        return text_y < line_y
    
    def _is_text_left_of_vertical_line(self, p1: Tuple[int, int], p2: Tuple[int, int], 
                                     text_center: Tuple[float, float]) -> bool:
        """
        检查文本框中心是否在垂直线段的左方
        """
        # 对于垂直线段，比较x坐标即可
        line_x = (p1[0] + p2[0]) / 2  # 线段的x坐标（垂直线段两端点x坐标应该相近）
        text_x = text_center[0]
        
        # x坐标越小越靠左
        return text_x < line_x
    
    def _is_valid_match(self, p1: Tuple[int, int], p2: Tuple[int, int],
                       text_center: Tuple[float, float], line_angle: float, text_type: str = 'unknown') -> bool:
        """检查是否有效的匹配"""
        if self._calculate_distance(p1, p2) == 0:
            return False
        
        # 检查角度约束：线段与水平/垂直方向的夹角不超过阈值
        is_horizontal = abs(line_angle) < self.angle_threshold or abs(line_angle - math.pi) < self.angle_threshold
        is_vertical = abs(line_angle - math.pi/2) < self.angle_threshold or abs(line_angle + math.pi/2) < self.angle_threshold
        
        if not (is_horizontal or is_vertical):
            return False
            
        # 所有的尺寸类型都取消文本位置的方向限制，直接返回True
        return True
    
    def _calculate_match_score(self, p1: Tuple[int, int], p2: Tuple[int, int],
                             text_center: Tuple[float, float], line_center: Tuple[float, float],
                             line_length: float, line_angle: float) -> float:
        """
        计算匹配分数，分数越低匹配越好
        
        考虑因素：
        1. 文本框中心到线段中点的距离
        2. 文本框中心到线段的垂直距离
        3. 文本框中心在线段上的投影位置（应该靠近中点）
        """
        # 到线段中点的距离（归一化）
        center_distance = self._calculate_distance(text_center, line_center) / (line_length + 1e-6)
        
        # 到线段的垂直距离（归一化）
        perpendicular_distance = self._point_to_line_distance(text_center, p1, p2) / (line_length + 1e-6)
        
        # 投影位置评分（理想情况是在中点）
        projection_ratio = self._get_projection_ratio(text_center, p1, p2)
        position_score = abs(projection_ratio - 0.5)  # 距离中点的偏差
        
        # 综合评分（权重可调整）
        score = (center_distance * 0.3 + 
                perpendicular_distance * 0.4 + 
                position_score * 0.3)
        
        return score
    
    def _get_projection_ratio(self, point: Tuple[float, float], 
                            line_start: Tuple[float, float], 
                            line_end: Tuple[float, float]) -> float:
        """计算点在线段上的投影位置比例（0在起点，1在终点）"""
        x, y = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return 0.5
        
        # 计算投影长度
        projection = ((x - x1) * dx + (y - y1) * dy) / (dx**2 + dy**2)
        
        return max(0, min(1, projection))
    
    def _pair_endpoints_to_lines(self, points: List[Tuple[int, int]], debug: bool = False) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        从散落的端点中配对生成有效的线段
        使用基于共线性的改进算法，避免跳过中间点
        
        Args:
            points: 散落的端点列表 [(x1,y1), (x2,y2), ...]
            debug: 是否输出调试信息
            
        Returns:
            有效线段列表 [((x1,y1), (x2,y2)), ...]
        """
        if debug:
            print(f"\n=== 端点配对开始（基于共线性算法）===")
            print(f"输入端点数量: {len(points)}")
            print(f"端点列表: {points}")
            print(f"共线性阈值: {self.collinear_threshold} 像素")
        
        valid_lines = []
        
        # 第一步：将点按共线性分组
        collinear_groups = self._group_collinear_points(points, debug)
        
        if debug:
            print(f"\n共线性分组结果: {len(collinear_groups)} 个组")
        
        # 第二步：处理每个共线组
        for group_idx, group in enumerate(collinear_groups):
            if debug:
                print(f"\n处理组 {group_idx + 1}: {group}")
            
            if len(group) < 2:
                if debug:
                    print(f"  跳过：组内点数不足 ({len(group)} < 2)")
                continue
            
            # 对组内点进行排序
            sorted_points = self._sort_points_on_line(group)
            if debug:
                print(f"  排序后的点: {sorted_points}")
            
            # 由于点已经通过共线性分组验证，直接生成线段
            
            # 生成相邻点之间的线段
            for i in range(len(sorted_points) - 1):
                p1 = sorted_points[i]
                p2 = sorted_points[i + 1]
                
                # 计算线段长度（排除重复点）
                line_length = self._calculate_distance(p1, p2)
                if line_length == 0:
                    if debug:
                        print(f"    跳过重复点: {p1} == {p2}")
                    continue
                
                valid_lines.append((p1, p2))
                if debug:
                    print(f"    ✅ 生成线段: {p1} -> {p2}, 长度: {line_length:.2f}")
        
        # 第三步：处理未分组的点（孤立点）
        # 找出所有未被分组的点
        grouped_points = set()
        for group in collinear_groups:
            grouped_points.update(group)
        
        isolated_points = [p for p in points if p not in grouped_points]
        
        if debug and isolated_points:
            print(f"\n处理孤立点: {isolated_points}")
        
        # 对孤立点使用原始的两两配对方法
        for i in range(len(isolated_points)):
            for j in range(i + 1, len(isolated_points)):
                p1 = isolated_points[i]
                p2 = isolated_points[j]
                
                # 计算线段长度（排除重复点）
                line_length = self._calculate_distance(p1, p2)
                if line_length == 0:
                    if debug:
                        print(f"  跳过重复点: {p1} == {p2}")
                    continue
                
                # 直接添加孤立点形成的线段（不再进行角度验证）
                valid_lines.append((p1, p2))
                if debug:
                    print(f"  ✅ 孤立点线段: {p1} -> {p2}, 长度: {line_length:.2f}")
        
        if debug:
            print(f"\n配对结果: 从 {len(points)} 个端点生成了 {len(valid_lines)} 条有效线段")
            print(f"其中共线组生成: {len(valid_lines) - len([line for line in valid_lines if line[0] in isolated_points or line[1] in isolated_points])} 条")
            print(f"孤立点生成: {len([line for line in valid_lines if line[0] in isolated_points or line[1] in isolated_points])} 条")
            print(f"=== 端点配对结束 ===\n")
        
        return valid_lines

# 使用示例
def example_usage():
    """演示两种使用方式：手动数据和JSON数据加载"""
    
    # 创建匹配器
    matcher = DimensionMatcher()
    
    # 方式1: 从JSON文件加载数据（推荐）
    print("=== 方式1: 从JSON文件加载数据 ===")
    json_file_path = r"D:\AI_project\BomListGeneration\extract_info\corner_text_modeldetection\layout_results\357_optimized.json"
    
    if os.path.exists(json_file_path):
        try:
            # 使用整合方法加载数据并进行OCR
            scattered_points, text_boxes, ocr_texts = matcher.load_and_process_json(
                json_file_path, 
                debug=True
            )
            
            print(f"\n从JSON加载的数据:")
            print(f"  散落端点数量: {len(scattered_points)}")
            print(f"  文本框数量: {len(text_boxes)}")
            print(f"  OCR文本数量: {len(ocr_texts)}")
            
            if scattered_points and text_boxes:
                # 执行匹配
                results = matcher.match_dimensions(scattered_points, text_boxes, ocr_texts, debug=True)
                
                # 输出结果
                print("\n匹配结果:")
                for i, match in enumerate(results['matches']):
                    print(f"匹配 {i+1}:")
                    print(f"  端点: {match['endpoint_pair']}")
                    print(f"  文本: {match['text_content']}")
                    print(f"  像素距离: {match['pixel_distance']:.2f}")
                    print(f"  实际尺寸: {match['actual_size']}")
                    print(f"  比例因子: {match['scale_factor']:.4f}")
                    print()
                
                print(f"总结: {results['summary']}")
            else:
                print("Warning: 没有找到有效的数据进行匹配")
                
        except Exception as e:
            print(f"从JSON加载数据时出错: {e}")
            print("将使用手动示例数据...")
    else:
        print(f"JSON文件不存在: {json_file_path}")
        print("将使用手动示例数据...")
    

if __name__ == "__main__":

    # 运行示例
    example_usage()