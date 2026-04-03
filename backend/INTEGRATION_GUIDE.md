# 整合轮廓处理服务集成指南

## 概述

整合轮廓处理服务 (`IntegratedContourService`) 是一个完整的图像处理管道，集成了轮廓检测、尺寸标注识别和3D模型生成功能。

## 主要功能

### 1. 轮廓检测
- 使用YOLO分割模型或OpenCV进行轮廓提取
- 支持多种图像格式（PNG、JPG、JPEG、BMP）
- 自动过滤小轮廓和噪声

### 2. 尺寸标注识别
- 检测图像中的尺寸标注
- 计算像素到真实尺寸的比例因子
- 支持置信度阈值调整

### 3. 3D模型生成
- 支持OBJ、STL、PLY格式导出
- 可配置模型高度
- 自动生成模型数据

## API接口

### 健康检查
```
GET /api/module/health
```

响应示例：
```json
{
  "success": true,
  "data": {
    "service_name": "IntegratedContourService",
    "status": "healthy",
    "dependencies": {
      "contour_generator": "available",
      "dimension_detection": "available",
      "dimension_matcher": "available",
      "output_directory": "available"
    },
    "configuration": {
      "output_dir": "outputs",
      "confidence_threshold": 0.5
    },
    "packages": {
      "opencv": "available",
      "numpy": "available",
      "pathlib": "available"
    }
  }
}
```

### 模块识别
```
POST /api/module/identify
```

请求参数：
- `image`: 图像文件（必需）
- `confidence_threshold`: 置信度阈值（可选，默认0.5）
- `debug`: 调试模式（可选，默认false）

### 轮廓处理
```
POST /api/module/process-contour
```

请求参数：
- `image`: 图像文件（必需）
- `height`: 3D模型高度，单位毫米（必需，> 0）
- `format`: 输出格式（可选，默认"obj"，支持obj/stl/ply）

响应示例：
```json
{
  "success": true,
  "data": {
    "contour_info": {
      "edge_lengths": [边长数组],
      "perimeter": 周长,
      "area": 面积,
      "num_vertices": 顶点数
    },
    "model_data": "3D模型数据",
    "format": "obj"
  }
}
```

## 配置说明

### 环境变量
- `CONTOUR_MODEL_PATH`: 轮廓检测模型路径
- `DIMENSION_MODEL_PATH`: 尺寸检测模型路径
- `OUTPUT_DIR`: 输出目录路径

### 依赖项
- Python 3.8+
- OpenCV
- NumPy
- Flask
- Marshmallow
- PaddleOCR（可选）
- YOLO模型（可选）

## 错误处理

### 常见错误码
- `400`: 参数验证失败、文件格式错误
- `404`: 文件不存在
- `500`: 服务内部错误

### 错误响应格式
```json
{
  "success": false,
  "error": "错误描述",
  "details": "详细错误信息"
}
```

## 测试

运行完整测试套件：
```bash
python -m pytest tests/test_api_routes.py -v
```

运行特定测试：
```bash
# 健康检查测试
python -m pytest tests/test_api_routes.py::TestModuleRoutes::test_health_check_endpoint -v

# 轮廓处理测试
python -m pytest tests/test_api_routes.py::TestContourProcessingRoutes -v
```

## 部署注意事项

1. **模型文件**: 确保YOLO模型文件路径正确配置
2. **输出目录**: 确保输出目录有写入权限
3. **内存使用**: 大图像处理可能需要较多内存
4. **依赖安装**: 某些依赖项（如PaddleOCR）可能需要额外配置

## 性能优化

1. **模型缓存**: 模型在首次使用时加载并缓存
2. **简化模式**: 当YOLO模型不可用时，自动降级到OpenCV处理
3. **内存管理**: 及时清理临时文件和中间结果

## 故障排除

### 常见问题

1. **模型加载失败**
   - 检查模型文件路径
   - 确认模型文件完整性
   - 查看日志中的详细错误信息

2. **图像处理失败**
   - 检查图像文件格式
   - 确认图像文件未损坏
   - 调整置信度阈值

3. **内存不足**
   - 减小输入图像尺寸
   - 增加系统内存
   - 优化处理参数

### 日志查看
服务使用Python标准日志模块，可通过配置日志级别查看详细信息：

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## 更新历史

- v1.0.0: 初始版本，集成轮廓检测和3D模型生成
- v1.1.0: 添加健康检查接口和完整的API测试套件
- v1.2.0: 修复参数验证问题，优化错误处理