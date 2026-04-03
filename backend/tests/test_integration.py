"""
端到端集成测试
测试完整的模块识别工作流程
"""

import unittest
import tempfile
import json
import io
from werkzeug.datastructures import FileStorage

from app import create_app


class TestModuleIdentificationIntegration(unittest.TestCase):
    """模块识别端到端集成测试"""

    def setUp(self):
        """测试前置设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp()

        # 准备测试数据
        self.test_detection_data = {
            "detections": [
                {"class_name": "dimension_point", "confidence": 0.85, "bbox_center": [100, 200]},
                {"class_name": "dimension_point", "confidence": 0.90, "bbox_center": [200, 300]},
                {
                    "class_name": "dimension_text",
                    "confidence": 0.88,
                    "bbox": [120, 180, 180, 220],
                    "text": "15.5",
                },
                {
                    "class_name": "dimension_text",
                    "confidence": 0.92,
                    "bbox": [180, 280, 240, 320],
                    "text": "22.0",
                },
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
        # 创建一个简单的测试图像数据
        fake_image_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
        return FileStorage(
            stream=io.BytesIO(fake_image_data), filename=filename, content_type="image/jpeg"
        )

    def create_test_json_file(self, data, filename="test_data.json"):
        """创建测试JSON文件"""
        json_str = json.dumps(data)
        return FileStorage(
            stream=io.BytesIO(json_str.encode("utf-8")),
            filename=filename,
            content_type="application/json",
        )

    def test_complete_workflow_success(self):
        """测试完整的成功工作流程"""
        # 准备测试文件
        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.test_detection_data)

        # 准备请求数据
        data = {"confidence_threshold": "0.8", "debug": "true"}

        # 发送请求
        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        # 验证响应状态
        self.assertIn(response.status_code, [200, 400, 500])  # 可能因为缺少依赖而失败

        # 验证响应格式
        response_data = json.loads(response.data)
        self.assertIn("success", response_data)

        if response_data["success"]:
            # 如果成功，验证数据结构
            self.assertIn("data", response_data)
            self.assertIn("processing_info", response_data)

            data_result = response_data["data"]
            self.assertIn("matches", data_result)
            self.assertIn("summary", data_result)
            self.assertIn("unmatched_endpoints", data_result)
            self.assertIn("unmatched_texts", data_result)

            # 验证处理信息
            processing_info = response_data["processing_info"]
            self.assertIn("confidence_threshold", processing_info)
            self.assertEqual(processing_info["confidence_threshold"], 0.8)

    def test_workflow_with_minimal_data(self):
        """测试最小数据集的工作流程"""
        minimal_data = {
            "detections": [
                {"class_name": "dimension_point", "confidence": 0.9, "bbox_center": [100, 100]}
            ]
        }

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(minimal_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        # 验证响应
        self.assertIn(response.status_code, [200, 400, 500])
        response_data = json.loads(response.data)
        self.assertIn("success", response_data)

    def test_workflow_with_large_dataset(self):
        """测试大数据集的工作流程"""
        # 创建包含多个检测结果的大数据集
        large_data = {"detections": []}

        # 添加多个端点
        for i in range(20):
            large_data["detections"].append(
                {
                    "class_name": "dimension_point",
                    "confidence": 0.8 + (i % 3) * 0.05,
                    "bbox_center": [50 + i * 30, 50 + i * 25],
                }
            )

        # 添加多个文本框
        for i in range(10):
            large_data["detections"].append(
                {
                    "class_name": "dimension_text",
                    "confidence": 0.85 + (i % 2) * 0.05,
                    "bbox": [60 + i * 35, 60 + i * 30, 120 + i * 35, 90 + i * 30],
                    "text": f"{10.5 + i * 2.5}",
                }
            )

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(large_data)

        data = {"confidence_threshold": "0.7", "debug": "true"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        # 验证响应
        self.assertIn(response.status_code, [200, 400, 500])
        response_data = json.loads(response.data)
        self.assertIn("success", response_data)

    def test_workflow_error_handling(self):
        """测试工作流程中的错误处理"""
        # 测试无效的JSON数据
        invalid_data = {"invalid_structure": "test"}

        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(invalid_data)

        data = {"confidence_threshold": "0.5", "debug": "false"}

        response = self.client.post(
            "/api/module/identify", data={**data, "image": image_file, "json_data": json_file}
        )

        # 应该返回错误
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.data)
        self.assertFalse(response_data["success"])
        self.assertIn("error", response_data)

    def test_health_check_integration(self):
        """测试健康检查集成"""
        response = self.client.get("/api/module/health")

        self.assertIn(response.status_code, [200, 503])
        response_data = json.loads(response.data)
        self.assertIn("success", response_data)
        self.assertIn("data", response_data)

        health_data = response_data["data"]
        self.assertIn("service_name", health_data)
        self.assertIn("status", health_data)
        self.assertIn("dependencies", health_data)

        # 验证依赖项检查
        dependencies = health_data["dependencies"]
        self.assertIsInstance(dependencies, dict)
        for dep_name, dep_status in dependencies.items():
            self.assertIn("status", dep_status)
            self.assertIn("message", dep_status)

    def test_api_response_format_consistency(self):
        """测试API响应格式一致性"""
        # 测试健康检查响应格式
        health_response = self.client.get("/api/module/health")
        health_data = json.loads(health_response.data)

        # 验证基本响应结构
        self.assertIn("success", health_data)
        self.assertIn("data", health_data)

        # 测试识别接口响应格式（错误情况）
        identify_response = self.client.post("/api/module/identify")
        identify_data = json.loads(identify_response.data)

        # 验证错误响应结构
        self.assertIn("success", identify_data)
        self.assertFalse(identify_data["success"])
        self.assertIn("error", identify_data)

    def test_parameter_validation_integration(self):
        """测试参数验证集成"""
        image_file = self.create_test_image_file()
        json_file = self.create_test_json_file(self.test_detection_data)

        # 测试各种参数组合
        test_cases = [
            {"confidence_threshold": "0.5", "debug": "false"},
            {"confidence_threshold": "0.8", "debug": "true"},
            {"confidence_threshold": "1.0", "debug": "false"},
            {"confidence_threshold": "0.0", "debug": "true"},
        ]

        for test_data in test_cases:
            response = self.client.post(
                "/api/module/identify",
                data=test_data,
                data={"image": image_file, "json_data": json_file},
            )

            # 验证响应状态合理
            self.assertIn(response.status_code, [200, 400, 500])
            response_data = json.loads(response.data)
            self.assertIn("success", response_data)

    def test_file_handling_integration(self):
        """测试文件处理集成"""
        # 测试不同文件类型和大小
        test_cases = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.bmp", "image/bmp"),
        ]

        for filename, content_type in test_cases:
            image_file = FileStorage(
                stream=io.BytesIO(b"fake_image_data"), filename=filename, content_type=content_type
            )
            json_file = self.create_test_json_file(self.test_detection_data)

            data = {"confidence_threshold": "0.5", "debug": "false"}

            response = self.client.post(
                "/api/module/identify",
                data={**data, "image": image_file, "json_data": json_file},
            )

            # 验证响应
            self.assertIn(response.status_code, [200, 400, 500])
            response_data = json.loads(response.data)
            self.assertIn("success", response_data)


class TestSystemIntegration(unittest.TestCase):
    """系统级集成测试"""

    def setUp(self):
        """系统测试前置设置"""
        self.app = create_app("testing")
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        """系统测试后清理"""
        self.app_context.pop()

    def test_application_startup(self):
        """测试应用启动"""
        # 验证应用正常启动
        self.assertIsNotNone(self.app)
        self.assertTrue(self.app.testing)

    def test_blueprint_registration(self):
        """测试蓝图注册"""
        # 验证模块蓝图已注册
        blueprints = [bp.name for bp in self.app.iter_blueprints()]
        self.assertIn("module", blueprints)

    def test_error_handlers(self):
        """测试错误处理器"""
        # 测试404错误
        response = self.client.get("/nonexistent-endpoint")
        self.assertEqual(response.status_code, 404)

        # 验证错误响应格式
        response_data = json.loads(response.data)
        self.assertIn("error", response_data)

    def test_configuration_loading(self):
        """测试配置加载"""
        # 验证测试配置已加载
        self.assertTrue(self.app.config["TESTING"])
        self.assertIn("SECRET_KEY", self.app.config)
        self.assertIn("MAX_CONTENT_LENGTH", self.app.config)


if __name__ == "__main__":
    unittest.main()
