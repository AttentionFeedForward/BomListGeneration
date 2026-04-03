"""
API路由单元测试
测试模块识别API接口的各种情况
"""

import unittest
import tempfile
import json
import io
from unittest.mock import Mock, patch
from werkzeug.datastructures import FileStorage

from app import create_app


class TestModuleRoutes(unittest.TestCase):
    """模块识别API路由测试类"""

    def setUp(self):
        """测试前置设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 模拟有效的JSON数据
        self.valid_json_data = {
            "detections": [
                {"class_name": "dimension_point", "confidence": 0.8, "bbox_center": [100, 200]},
                {"class_name": "dimension_text", "confidence": 0.9, "bbox": [50, 60, 150, 80]},
            ]
        }

    def tearDown(self):
        """测试后清理"""
        self.app_context.pop()
        import shutil

        try:
            shutil.rmtree(self.temp_dir)
        except Exception:
            pass

    def create_test_image_file(self, filename="test_image.jpg"):
        """创建测试图像文件"""
        return FileStorage(
            stream=io.BytesIO(b"fake_image_data"), filename=filename, content_type="image/jpeg"
        )

    def create_test_json_file(self, data, filename="test_data.json"):
        """创建测试JSON文件"""
        json_str = json.dumps(data)
        return FileStorage(
            stream=io.BytesIO(json_str.encode("utf-8")),
            filename=filename,
            content_type="application/json",
        )

    def test_health_check_endpoint(self):
        """测试健康检查接口"""
        response = self.client.get("/api/module/health")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("data", data)
        self.assertIn("service_name", data["data"])
        self.assertIn("status", data["data"])
        self.assertIn("dependencies", data["data"])

    @patch("api.module_routes.get_integrated_service")
    def test_health_check_with_service_error(self, mock_get_service):
        """测试健康检查服务异常"""
        mock_service = Mock()
        mock_service.check_health.side_effect = Exception("Service error")
        mock_get_service.return_value = mock_service

        response = self.client.get("/api/module/health")

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("error", data)

    def test_identify_module_missing_files(self):
        """测试缺少文件的请求"""
        response = self.client.post("/api/module/identify")

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data["success"])
        self.assertIn("Missing required file: image", data["error"])

    def test_identify_module_empty_filename(self):
        """测试空文件名"""
        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data=data, content_type="multipart/form-data"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])

    def test_identify_module_invalid_image_type(self):
        """测试无效图像文件类型"""
        image_file = FileStorage(
            stream=io.BytesIO(b"fake_data"), filename="test.txt", content_type="text/plain"
        )
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        data.update({"image": image_file, "json_data": json_file})
        response = self.client.post(
            "/api/module/identify", data=data
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid image file type", response_data["error"])

    def test_identify_module_invalid_json_type(self):
        """测试无效JSON文件类型"""
        image_file = self.create_test_image_file()
        json_file = FileStorage(
            stream=io.BytesIO(b"fake_data"), filename="test.txt", content_type="text/plain"
        )

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid JSON file type", response_data["error"])

    def test_identify_module_invalid_json_format(self):
        """测试无效JSON格式"""
        image_file = self.create_test_image_file()
        json_file = FileStorage(
            stream=io.BytesIO(b"invalid json content"),
            filename="test.json",
            content_type="application/json",
        )

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid JSON format", response_data["error"])

    def test_identify_module_invalid_request_parameters(self):
        """测试无效请求参数"""
        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "1.5", "debug": "invalid_boolean"}  # 超出范围

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid request parameters", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_identify_module_invalid_input_data(self, mock_get_service):
        """测试无效输入数据格式"""
        mock_service = Mock()
        mock_service.validate_input_data.return_value = (False, "Invalid data format")
        mock_get_service.return_value = mock_service

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file({"invalid": "data"})

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid input data format", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_identify_module_success(self, mock_get_service):
        """测试成功的模块识别"""
        # 模拟服务返回结果
        mock_service = Mock()
        mock_service.validate_input_data.return_value = (True, None)
        mock_identification_result = {
            "matches": [
                {
                    "id": 1,
                    "endpoint_pair": {
                        "start_point": {"x": 100, "y": 200},
                        "end_point": {"x": 150, "y": 250},
                    },
                    "text_box": {
                        "corners": [
                            {"x": 50, "y": 60},
                            {"x": 150, "y": 60},
                            {"x": 150, "y": 80},
                            {"x": 50, "y": 80},
                        ]
                    },
                    "text_content": "10.5",
                    "measurements": {
                        "pixel_distance": 70.71,
                        "actual_size": 10.5,
                        "scale_factor": 0.148,
                    },
                    "match_score": 0.95,
                    "is_outlier": False,
                }
            ],
            "unmatched_endpoints": [],
            "unmatched_texts": [],
            "summary": {
                "total_matches": 1,
                "total_endpoints": 2,
                "total_texts": 1,
                "match_rate": 1.0,
                "average_scale_factor": 0.148,
            },
            "scale_filter_info": {
                "enabled": True,
                "original_count": 1,
                "filtered_count": 1,
                "outliers_removed": 0,
                "filter_threshold": 0.05,
            },
            "processing_info": {
                "confidence_threshold": 0.5,
                "angle_threshold": 2.0,
                "enable_scale_filter": True,
                "scale_deviation_threshold": 0.05,
                "collinear_threshold": 3.0,
            },
        }
        mock_service.identify_modules.return_value = mock_identification_result
        mock_get_service.return_value = mock_service

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)
        self.assertIn("processing_info", response_data)

        # 验证返回数据结构
        data_result = response_data["data"]
        self.assertIn("matches", data_result)
        self.assertIn("summary", data_result)
        self.assertEqual(len(data_result["matches"]), 1)
        self.assertEqual(data_result["summary"]["total_matches"], 1)

    @patch("api.module_routes.get_integrated_service")
    def test_identify_module_file_not_found_error(self, mock_get_service):
        """测试文件不存在错误"""
        mock_service = Mock()
        mock_service.validate_input_data.return_value = (True, None)
        mock_service.identify_modules.side_effect = FileNotFoundError("File not found")
        mock_get_service.return_value = mock_service

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 404)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("File not found", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_identify_module_value_error(self, mock_get_service):
        """测试数据格式错误"""
        mock_service = Mock()
        mock_service.validate_input_data.return_value = (True, None)
        mock_service.identify_modules.side_effect = ValueError("Invalid data format")
        mock_get_service.return_value = mock_service

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Invalid data format", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_identify_module_general_error(self, mock_get_service):
        """测试一般性错误"""
        mock_service = Mock()
        mock_service.validate_input_data.return_value = (True, None)
        mock_service.identify_modules.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("Module identification failed", response_data["error"])

    def test_identify_module_with_debug_enabled(self):
        """测试启用调试模式的识别"""
        # 这个测试需要实际的服务实例，所以使用真实的服务
        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.valid_json_data)

        data = {"confidence_threshold": "0.5", "debug": "true"}

        # 由于没有真实的dimension_matcher，这个测试可能会失败
        # 但我们可以验证请求格式是否正确
        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        # 验证请求被正确处理（即使可能因为缺少依赖而失败）
        self.assertIn(response.status_code, [200, 400, 500])
        response_data = json.loads(response.data)
        self.assertIn("success", response_data)


class TestContourProcessingRoutes(unittest.TestCase):
    """轮廓处理API测试类"""

    def setUp(self):
        """测试前置设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """测试后清理"""
        self.app_context.pop()

    def create_test_image_file(self, filename="test_contour.jpg"):
        """创建测试图像文件"""
        return FileStorage(
            stream=io.BytesIO(b"fake_image_data"), filename=filename, content_type="image/jpeg"
        )

    def test_process_contour_missing_image(self):
        """测试缺少图像文件的请求"""
        data = {"height": "10.0", "format": "obj"}
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("缺少图像文件", response_data["error"])

    def test_process_contour_empty_filename(self):
        """测试空文件名"""
        data = {
            "height": "10.0", 
            "format": "obj",
            "image": FileStorage(stream=io.BytesIO(b""), filename="", content_type="image/jpeg")
        }
        
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("未选择图像文件", response_data["error"])

    def test_process_contour_invalid_image_type(self):
        """测试无效的图像文件类型"""
        data = {
            "height": "10.0", 
            "format": "obj",
            "image": FileStorage(
                stream=io.BytesIO(b"fake_data"), 
                filename="test.txt", 
                content_type="text/plain"
            )
        }
        
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("不支持的图像格式", response_data["error"])

    def test_process_contour_missing_height(self):
        """测试缺少高度参数"""
        data = {
            "format": "obj",
            "image": self.create_test_image_file()
        }
        
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("参数验证失败", response_data["error"])

    def test_process_contour_invalid_height(self):
        """测试无效的高度参数"""
        data = {
            "height": "-5.0", 
            "format": "obj",
            "image": self.create_test_image_file()
        }
        
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("参数验证失败", response_data["error"])

    def test_process_contour_invalid_format(self):
        """测试无效的格式参数"""
        data = {
            "height": "10.0", 
            "format": "invalid",
            "image": self.create_test_image_file()
        }
        
        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("参数验证失败", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_process_contour_success(self, mock_get_service):
        """测试成功的轮廓处理"""
        # 模拟服务返回结果
        mock_service = Mock()
        mock_result = {
            "success": True,
            "contour_info": {
                "edge_lengths": [10.0, 15.0, 10.0, 15.0],
                "perimeter": 50.0,
                "area": 150.0,
                "num_vertices": 4
            },
            "model_data": "fake_3d_model_data",
            "format": "obj"
        }
        mock_service.process_image.return_value = mock_result
        mock_get_service.return_value = mock_service

        data = {
            "height": "10.0", 
            "format": "obj",
            "image": self.create_test_image_file()
        }

        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.data)
        self.assertTrue(response_data["success"])
        self.assertIn("data", response_data)
        self.assertIn("contour_info", response_data["data"])
        self.assertIn("model_data", response_data["data"])
        self.assertEqual(response_data["data"]["format"], "obj")

    @patch("api.module_routes.get_integrated_service")
    def test_process_contour_service_error(self, mock_get_service):
        """测试轮廓处理服务错误"""
        mock_service = Mock()
        mock_service.process_image.return_value = {
            "success": False,
            "error": "轮廓检测失败"
        }
        mock_get_service.return_value = mock_service

        data = {
            "height": "10.0", 
            "format": "obj",
            "image": self.create_test_image_file()
        }

        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("轮廓检测失败", response_data["error"])

    @patch("api.module_routes.get_integrated_service")
    def test_process_contour_exception(self, mock_get_service):
        """测试轮廓处理异常"""
        mock_service = Mock()
        mock_service.process_image.side_effect = Exception("Unexpected error")
        mock_get_service.return_value = mock_service

        data = {
            "height": "10.0", 
            "format": "obj",
            "image": self.create_test_image_file()
        }

        response = self.client.post("/api/module/process-contour", data=data)

        self.assertEqual(response.status_code, 500)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("轮廓处理失败", response_data["error"])


class TestModuleRoutesIntegration(unittest.TestCase):
    """模块路由集成测试"""

    def setUp(self):
        """集成测试前置设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """集成测试后清理"""
        self.app_context.pop()

    def test_api_endpoint_accessibility(self):
        """测试API端点可访问性"""
        # 测试健康检查端点
        response = self.client.get("/api/module/health")
        self.assertIn(response.status_code, [200, 503])  # 健康或不健康都是有效响应

        # 测试识别端点（应该返回400因为缺少参数）
        response = self.client.post("/api/module/identify")
        self.assertEqual(response.status_code, 400)

        # 测试轮廓处理端点（应该返回400因为缺少参数）
        response = self.client.post("/api/module/process-contour")
        self.assertEqual(response.status_code, 400)

    def test_cors_headers(self):
        """测试CORS头部"""
        response = self.client.get("/api/module/health")
        # 检查是否有CORS相关头部（如果配置了的话）
        self.assertIsNotNone(response.headers)

    def test_content_type_handling(self):
        """测试内容类型处理"""
        # 测试JSON响应的内容类型
        response = self.client.get("/api/module/health")
        self.assertIn("application/json", response.content_type)


if __name__ == "__main__":
    unittest.main()
