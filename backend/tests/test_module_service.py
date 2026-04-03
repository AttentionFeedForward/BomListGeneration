"""
模块识别服务单元测试
覆盖核心识别逻辑，包含正常和异常情况处理
"""

import unittest
import tempfile
import json
import os
from unittest.mock import Mock, patch

from services.module_service import ModuleIdentificationService


class TestModuleIdentificationService(unittest.TestCase):
    """模块识别服务测试类"""

    def setUp(self):
        """测试前置设置"""
        self.service = ModuleIdentificationService(
            angle_threshold=2.0,
            enable_scale_filter=True,
            scale_deviation_threshold=0.05,
            collinear_threshold=3.0,
        )

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 模拟有效的JSON数据
        self.valid_json_data = {
            "detections": [
                {"class_name": "dimension_point", "confidence": 0.8, "bbox_center": [100, 200]},
                {"class_name": "dimension_text", "confidence": 0.9, "bbox": [50, 60, 150, 80]},
            ]
        }

        # 模拟无效的JSON数据
        self.invalid_json_data = {"invalid_field": "test"}

    def tearDown(self):
        """测试后清理"""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def create_temp_json_file(self, data):
        """创建临时JSON文件"""
        temp_file = os.path.join(self.temp_dir, "test_data.json")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return temp_file

    def create_temp_image_file(self):
        """创建临时图像文件"""
        temp_file = os.path.join(self.temp_dir, "test_image.jpg")
        # 创建一个空文件模拟图像
        with open(temp_file, "wb") as f:
            f.write(b"fake_image_data")
        return temp_file

    def test_service_initialization(self):
        """测试服务初始化"""
        self.assertEqual(self.service.angle_threshold, 2.0)
        self.assertTrue(self.service.enable_scale_filter)
        self.assertEqual(self.service.scale_deviation_threshold, 0.05)
        self.assertEqual(self.service.collinear_threshold, 3.0)
        self.assertIsNotNone(self.service.matcher)
        self.assertIsNotNone(self.service.logger)

    def test_validate_input_data_valid(self):
        """测试有效输入数据验证"""
        is_valid, error_msg = self.service.validate_input_data(self.valid_json_data)
        self.assertTrue(is_valid)
        self.assertIsNone(error_msg)

    def test_validate_input_data_invalid_structure(self):
        """测试无效数据结构验证"""
        is_valid, error_msg = self.service.validate_input_data(self.invalid_json_data)
        self.assertFalse(is_valid)
        self.assertIn("detections", error_msg)

    def test_validate_input_data_invalid_type(self):
        """测试无效数据类型验证"""
        is_valid, error_msg = self.service.validate_input_data("invalid_string")
        self.assertFalse(is_valid)
        self.assertIn("字典格式", error_msg)

    def test_validate_input_data_missing_fields(self):
        """测试缺少必需字段的验证"""
        invalid_data = {
            "detections": [
                {
                    "class_name": "dimension_point"
                    # 缺少confidence字段
                }
            ]
        }
        is_valid, error_msg = self.service.validate_input_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("confidence", error_msg)

    def test_validate_input_data_invalid_class_name(self):
        """测试无效class_name验证"""
        invalid_data = {"detections": [{"class_name": "invalid_class", "confidence": 0.8}]}
        is_valid, error_msg = self.service.validate_input_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("class_name", error_msg)

    def test_validate_input_data_invalid_confidence(self):
        """测试无效confidence值验证"""
        invalid_data = {
            "detections": [{"class_name": "dimension_point", "confidence": 1.5}]  # 超出范围
        }
        is_valid, error_msg = self.service.validate_input_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("confidence", error_msg)

    def test_validate_input_data_missing_bbox_center(self):
        """测试dimension_point缺少bbox_center验证"""
        invalid_data = {
            "detections": [
                {
                    "class_name": "dimension_point",
                    "confidence": 0.8,
                    # 缺少bbox_center
                }
            ]
        }
        is_valid, error_msg = self.service.validate_input_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("bbox_center", error_msg)

    def test_validate_input_data_missing_bbox(self):
        """测试dimension_text缺少bbox验证"""
        invalid_data = {
            "detections": [
                {
                    "class_name": "dimension_text",
                    "confidence": 0.8,
                    # 缺少bbox
                }
            ]
        }
        is_valid, error_msg = self.service.validate_input_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertIn("bbox", error_msg)

    def test_validate_input_data_nonexistent_image(self):
        """测试不存在的图像文件验证"""
        is_valid, error_msg = self.service.validate_input_data(
            self.valid_json_data, "/nonexistent/path/image.jpg"
        )
        self.assertFalse(is_valid)
        self.assertIn("图像文件不存在", error_msg)

    @patch("services.module_service.DimensionMatcher")
    def test_identify_modules_file_not_found(self, mock_dimension_matcher):
        """测试文件不存在的异常处理"""
        with self.assertRaises(FileNotFoundError):
            self.service.identify_modules(
                json_file_path="/nonexistent/file.json", confidence_threshold=0.5
            )

    @patch("services.module_service.DimensionMatcher")
    def test_identify_modules_success(self, mock_dimension_matcher):
        """测试成功的模块识别流程"""
        # 创建临时文件
        json_file = self.create_temp_json_file(self.valid_json_data)
        image_file = self.create_temp_image_file()

        # 模拟DimensionMatcher的返回结果
        mock_matcher_instance = Mock()
        mock_dimension_matcher.return_value = mock_matcher_instance

        mock_load_result = (
            [(100, 200), (150, 250)],  # scattered_points
            [[[50, 60], [150, 60], [150, 80], [50, 80]]],  # text_boxes
            ["10.5"],  # ocr_texts
        )
        mock_matcher_instance.load_and_process_json.return_value = mock_load_result

        mock_match_result = {
            "matches": [
                {
                    "endpoint_pair": [(100, 200), (150, 250)],
                    "text_box": [[50, 60], [150, 60], [150, 80], [50, 80]],
                    "text_content": "10.5",
                    "pixel_distance": 70.71,
                    "actual_size": 10.5,
                    "scale_factor": 0.148,
                    "match_score": 0.95,
                    "is_outlier": False,
                }
            ],
            "unmatched_endpoints": [],
            "unmatched_texts": [],
            "summary": {
                "total_endpoints": 2,
                "total_texts": 1,
                "match_rate": 1.0,
                "average_scale_factor": 0.148,
            },
            "scale_filter_info": {
                "original_count": 1,
                "filtered_count": 1,
                "outliers_removed": 0,
                "filter_threshold": 0.05,
            },
        }
        mock_matcher_instance.match_dimensions.return_value = mock_match_result

        # 执行识别
        result = self.service.identify_modules(
            json_file_path=json_file, image_path=image_file, confidence_threshold=0.5, debug=False
        )

        # 验证结果
        self.assertIsInstance(result, dict)
        self.assertIn("matches", result)
        self.assertIn("summary", result)
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["summary"]["total_matches"], 1)

    @patch("services.module_service.DimensionMatcher")
    def test_identify_modules_with_debug(self, mock_dimension_matcher):
        """测试带调试信息的模块识别"""
        json_file = self.create_temp_json_file(self.valid_json_data)

        mock_matcher_instance = Mock()
        mock_dimension_matcher.return_value = mock_matcher_instance

        mock_load_result = ([], [], [])
        mock_matcher_instance.load_and_process_json.return_value = mock_load_result

        mock_match_result = {
            "matches": [],
            "unmatched_endpoints": [],
            "unmatched_texts": [],
            "summary": {
                "total_endpoints": 0,
                "total_texts": 0,
                "match_rate": 0.0,
                "average_scale_factor": 0.0,
            },
            "scale_filter_info": {},
        }
        mock_matcher_instance.match_dimensions.return_value = mock_match_result

        result = self.service.identify_modules(json_file_path=json_file, debug=True)

        self.assertIn("debug_info", result)
        self.assertIn("input_data", result["debug_info"])

    def test_check_health_success(self):
        """测试健康检查成功"""
        health_info = self.service.check_health()

        self.assertIsInstance(health_info, dict)
        self.assertIn("service_name", health_info)
        self.assertIn("status", health_info)
        self.assertIn("dependencies", health_info)
        self.assertIn("configuration", health_info)
        self.assertEqual(health_info["service_name"], "ModuleIdentificationService")

    @patch("services.module_service.DimensionMatcher")
    def test_check_health_with_error(self, mock_dimension_matcher):
        """测试健康检查异常情况"""
        # 模拟DimensionMatcher初始化失败
        mock_dimension_matcher.side_effect = Exception("Initialization failed")

        # 重新创建服务实例以触发异常
        with self.assertRaises(Exception):
            ModuleIdentificationService()

    def test_format_identification_result(self):
        """测试结果格式化"""
        # 模拟原始匹配结果
        mock_match_results = {
            "matches": [
                {
                    "endpoint_pair": [(100, 200), (150, 250)],
                    "text_box": [[50, 60], [150, 60], [150, 80], [50, 80]],
                    "text_content": "10.5",
                    "pixel_distance": 70.71,
                    "actual_size": 10.5,
                    "scale_factor": 0.148,
                    "match_score": 0.95,
                }
            ],
            "unmatched_endpoints": [[(200, 300), (250, 350)]],
            "unmatched_texts": [
                {
                    "text_box": [[100, 120], [200, 120], [200, 140], [100, 140]],
                    "text_content": "15.0",
                }
            ],
            "summary": {
                "total_endpoints": 4,
                "total_texts": 2,
                "match_rate": 0.5,
                "average_scale_factor": 0.148,
            },
        }

        result = self.service._format_identification_result(
            match_results=mock_match_results,
            scattered_points=[(100, 200), (150, 250), (200, 300), (250, 350)],
            text_boxes=[
                [[50, 60], [150, 60], [150, 80], [50, 80]],
                [[100, 120], [200, 120], [200, 140], [100, 140]],
            ],
            ocr_texts=["10.5", "15.0"],
        )

        # 验证格式化结果
        self.assertIn("matches", result)
        self.assertIn("unmatched_endpoints", result)
        self.assertIn("unmatched_texts", result)
        self.assertIn("summary", result)
        self.assertIn("processing_info", result)

        # 验证匹配项格式
        self.assertEqual(len(result["matches"]), 1)
        match = result["matches"][0]
        self.assertIn("id", match)
        self.assertIn("endpoint_pair", match)
        self.assertIn("text_box", match)
        self.assertIn("measurements", match)

        # 验证端点格式
        self.assertEqual(len(result["unmatched_endpoints"]), 1)
        endpoint = result["unmatched_endpoints"][0]
        self.assertIn("start_point", endpoint)
        self.assertIn("end_point", endpoint)

        # 验证文本格式
        self.assertEqual(len(result["unmatched_texts"]), 1)
        text = result["unmatched_texts"][0]
        self.assertIn("text_box", text)
        self.assertIn("text_content", text)


class TestModuleServiceIntegration(unittest.TestCase):
    """模块服务集成测试"""

    def setUp(self):
        """集成测试前置设置"""
        self.service = ModuleIdentificationService()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """集成测试后清理"""
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def test_end_to_end_workflow(self):
        """测试端到端工作流程"""
        # 创建测试数据
        test_data = {
            "detections": [
                {"class_name": "dimension_point", "confidence": 0.85, "bbox_center": [100, 200]},
                {"class_name": "dimension_point", "confidence": 0.90, "bbox_center": [200, 200]},
                {"class_name": "dimension_text", "confidence": 0.95, "bbox": [140, 180, 160, 200]},
            ]
        }

        # 创建临时文件
        json_file = os.path.join(self.temp_dir, "test_data.json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # 验证数据格式
        is_valid, error_msg = self.service.validate_input_data(test_data)
        self.assertTrue(is_valid, f"数据验证失败: {error_msg}")

        # 检查健康状态
        health_info = self.service.check_health()
        self.assertIn("status", health_info)


if __name__ == "__main__":
    unittest.main()
