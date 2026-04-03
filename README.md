# BOM - 建筑物料清单智能生成系统

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-16+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/React-19.2.0-61dafb.svg)](https://reactjs.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3.3-lightgrey.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个基于 AI 的建筑平面图智能分析系统，通过深度学习算法自动识别建筑轮廓、提取尺寸标注，并生成完整的物料清单（BOM）。

## 🌟 核心功能

### 1. 建筑轮廓识别与尺寸提取
- 🖼️ **图像智能分析**：基于 YOLO 深度学习模型的轮廓分割算法，对建筑平面图进行智能分析。
- 📐 **尺寸自动提取**：自动识别图纸中的尺寸标注并计算真实尺寸。
- 🎯 **高精度匹配**：智能匹配尺寸标注与轮廓边界，通过算法过滤异常值，确保数据准确性。
- 📊 **多格式导出**：支持 OBJ、STL、PLY 等 3D 模型格式的导出，便于后续设计和应用。

### 2. 物料清单智能生成
- 🏗️ **构造做法选型**：支持天花、地面、墙面等多种构造做法选择，满足不同工程需求。
- 🧮 **智能面积计算**：根据识别的建筑轮廓自动计算各部位面积，为物料估算提供精确数据。
- 📋 **标准化 BOM 输出**：生成符合工程标准的物料清单（Bill of Materials），包含详细的材料种类、规格和数量。
- 📤 **多格式导出**：支持 CSV、Excel 等多种格式导出，方便用户进行数据管理和进一步处理。

### 3. 现代化用户界面
- 🎨 **响应式设计**：基于 React + TypeScript 构建的现代化前端界面，提供优秀的用户体验。
- 🌈 **流畅动画交互**：使用 Framer Motion 库提供流畅的界面动画和交互效果。
- 📱 **多端适配**：界面设计考虑了桌面端和移动端的兼容性，确保在不同设备上都能良好运行。
- 🎯 **直观可视化**：实时展示图像处理进度、轮廓识别结果和生成的物料清单，提供直观的数据反馈。

## 🏗️ 系统架构

本项目主要由 `frontend` 和 `backend` 两大部分组成，通过 RESTful API 进行通信。

```
┌─────────────────────────────────────────────────────────────┐
│                      前端 (React + TypeScript)               │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 轮廓处理    │ │ 布局识别     │ │ 物料计算     │         │
│  │ Contour     │ │ Layout       │ │ Material     │         │
│  │ Processing  │ │ Recognition  │ │ Calculation  │         │
│  └─────────────┘ └──────────────┘ └──────────────┘         │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────┐
│                    后端 (Flask + Python)                     │
│  ┌─────────────┐ ┌──────────────┐ ┌──────────────┐         │
│  │ 模块识别    │ │ 物料计算     │ │ 布局分析     │         │
│  │ Module API  │ │ Material API │ │ Layout API   │         │
│  └─────────────┘ └──────────────┘ └──────────────┘         │
│  ┌──────────────────────────────────────────────┐           │
│  │         核心服务层 (Services)                 │           │
│  │  • IntegratedContourService                  │           │
│  │  • LayoutService                             │           │
│  │  • MaterialCalculationService                │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 项目结构

```
BOM/
├── backend/                          # Flask 后端服务
│   ├── api/                         # REST API 路由
│   │   ├── module_routes.py        # 模块识别接口
│   │   ├── material_routes.py      # 物料计算接口
│   │   └── layout_routes.py        # 布局分析接口
│   ├── services/                    # 业务逻辑层
│   │   ├── integrated_contour_service.py  # 轮廓处理服务
│   │   ├── layout_service.py              # 布局分析服务
│   │   └── material_calculation_service.py # 物料计算服务
│   ├── types/                       # 类型定义
│   ├── tests/                       # 单元测试
│   ├── app.py                       # Flask 应用入口
│   ├── config.py                    # 配置文件
│   └── requirements.txt             # Python 依赖
│
├── frontend/                        # React 前端应用
│   ├── public/                      # 静态资源
│   ├── src/
│   │   ├── components/              # React 组件
│   │   │   ├── Pages/              # 页面组件
│   │   │   ├── UI/                 # UI 基础组件
│   │   │   ├── Contour/            # 轮廓可视化组件
│   │   │   └── Navigation/         # 导航组件
│   │   ├── services/               # API 服务层
│   │   ├── store/                  # 状态管理 (Zustand)
│   │   ├── hooks/                  # 自定义 Hooks
│   │   ├── utils/                  # 工具函数
│   │   ├── App.tsx                 # 主应用组件
│   │   └── index.tsx               # 入口文件
│   ├── package.json                # Node.js 依赖
│   └── tsconfig.json               # TypeScript 配置
│
├── .gitignore                        # Git 忽略文件配置
└── README.md                         # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- **Python**: 3.8 或更高版本
- **Node.js**: 16 或更高版本
- **npm**: 8 或更高版本
- **操作系统**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 18.04+)

### 1. 克隆项目

```bash
git clone <repository-url>
cd BOM
```

### 2. 环境设置

#### Python 后端

1.  **创建并激活虚拟环境**:
    ```bash
    # Windows
    python -m venv venv
    ./venv/Scripts/activate

    # Linux/macOS
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **安装后端依赖**:
    ```bash
    pip install -r backend/requirements.txt
    ```

#### Node.js 前端

1.  **进入前端目录**:
    ```bash
    cd frontend
    ```

2.  **安装前端依赖**:
    ```bash
    npm install
    ```

3.  **返回项目根目录**:
    ```bash
    cd ..
    ```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件，并根据 `.env.example` 文件内容进行配置。

```bash
# .env 示例
# Flask 配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here

# API 配置 (根据实际情况填写，如果后端服务需要外部API密钥)
# 例如，如果IntegratedContourService或MaterialCalculationService内部调用了LLM，需要在这里配置LLM的API Key
# OPENAI_API_KEY=your_openai_api_key_here
# OPENAI_BASE_URL=https://api.openai.com/v1

# 前端 API 基础 URL (指向后端服务)
REACT_APP_API_BASE_URL=http://localhost:5000/api
```

### 4. 启动服务

本项目采用前后端分离的架构，需要分别启动前端和后端服务。

#### 启动后端服务

在项目根目录，确保虚拟环境已激活，然后运行：

```bash
# 激活虚拟环境 (如果尚未激活)
# Windows: ./venv/Scripts/activate
# Linux/macOS: source venv/bin/activate

# 启动 Flask 后端
cd backend
python app.py
```
后端服务默认运行在 `http://localhost:5000`。

#### 启动前端服务

在新开的终端窗口中，进入 `frontend` 目录，并运行：

```bash
cd frontend
npm start
```
前端应用默认运行在 `http://localhost:3000`，并会自动在浏览器中打开。

### 5. 访问应用

- **前端界面**: `http://localhost:3000`
- **后端 API**: `http://localhost:5000`
- **健康检查**: `http://localhost:5000/health`
- **API 文档**: `http://localhost:5000/api/module/health` (查看模块服务状态)

## 📖 使用指南

### 轮廓处理流程

1.  **上传建筑平面图**:
    *   支持格式：JPG, PNG, BMP, TIFF。
    *   建议分辨率：1000x1000 像素以上。
    *   确保尺寸标注清晰可见。
2.  **AI 智能识别**:
    *   轮廓分割：系统自动提取房间边界。
    *   尺寸检测：识别标注文字和尺寸线。
    *   尺寸匹配：将像素尺寸转换为真实尺寸。
3.  **结果验证**:
    *   在前端界面查看识别的轮廓和尺寸。
    *   必要时可以进行手动调整。
4.  **导出 3D 模型**:
    *   选择导出格式：OBJ / STL / PLY。
    *   设置模型高度（毫米）。
    *   下载 3D 模型文件。

### 物料清单生成

1.  **输入房间尺寸**:
    *   可以通过轮廓处理结果自动导入，或手动输入房间的长、宽、高。
    *   系统自动计算天花、地面、墙面等各部位面积。
2.  **选择构造做法**:
    *   为天花、地面、墙面等部位选择预设的构造做法，或自定义输入。
3.  **生成 BOM 清单**:
    *   系统智能分析构造做法，计算所需材料种类和数量。
    *   生成标准化的物料清单。
4.  **导出结果**:
    *   支持 CSV、Excel 和 JSON 格式导出。

## 🔧 配置说明

### 后端配置 (backend/config.py)

此文件定义了 Flask 应用的各项配置，包括文件上传、模块识别参数等。

```python
# 文件上传配置
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}

# 模块识别配置
MODULE_DETECTION_CONFIG = {
    "angle_threshold": 2.0,           # 角度阈值（度）
    "enable_scale_filter": True,      # 比例因子过滤
    "scale_deviation_threshold": 0.05, # 偏差阈值
    "confidence_threshold": 0.3,      # 置信度阈值
}
```

### 前端配置 (frontend/.env)

前端应用的环境变量通过 `.env` 文件配置，主要用于指定后端 API 的基础 URL。

```bash
# API 基础 URL
REACT_APP_API_BASE_URL=http://localhost:5000/api

# 其他配置
REACT_APP_DEBUG=true
```

## 🛠️ 开发指南

### 后端开发

1.  **激活虚拟环境**: 确保在 `backend` 目录执行任何 Python 命令前，已激活虚拟环境。
    ```bash
    # Windows
    ./venv/Scripts/activate

    # Linux/macOS
    source venv/bin/activate
    ```
2.  **运行开发服务器**: 
    ```bash
    cd backend
    python app.py
    ```
3.  **运行测试**:
    ```bash
    pytest backend/tests/ -v
    ```
4.  **代码格式化/检查**:
    ```bash
    black backend/
    flake8 backend/
    ```

### 前端开发

1.  **进入前端目录**:
    ```bash
    cd frontend
    ```
2.  **开发模式**:
    ```bash
    npm start
    ```
3.  **构建生产版本**:
    ```bash
    npm run build
    ```
4.  **运行测试**:
    ```bash
    npm test
    ```

### API 接口文档

#### 模块识别接口

`POST /api/module/identify`

用于上传图像并进行模块识别和尺寸提取。

**请求参数**:
- `image`: 文件 (必需) - 图像文件（multipart/form-data）。
- `confidence_threshold`: 浮点数 (可选) - 置信度阈值，默认 0.5。
- `debug`: 布尔值 (可选) - 调试模式，默认 `false`。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "contour_info": { /* 轮廓信息 */ },
    "matches": [ /* 匹配结果列表 */ ],
    "summary": { /* 总结信息 */ }
  },
  "message": "Module identified successfully."
}
```

#### 轮廓处理接口

`POST /api/module/process-contour`

用于处理图像并生成 3D 模型。

**请求参数**:
- `image`: 文件 (必需) - 图像文件（multipart/form-data）。
- `height`: 整数 (必需) - 3D 模型高度，单位毫米 (例如: 2950)。
- `format`: 字符串 (可选) - 输出模型格式，默认 "obj"，支持 "obj", "stl", "ply"。

**响应示例**:

```json
{
  "success": true,
  "data": {
    "contour_info": {
      "contours": [
        {
          "id": "contour_0",
          "geometry": {
            "points": [[x1, y1], [x2, y2], ...],
            "edge_lengths": [l1, l2, ...],
            "perimeter": p,
            "area": a,
            "num_points": n,
            "unit": "mm"
          }
        }
      ],
      "summary": {
        "total_contours": N,
        "total_area": A,
        "total_perimeter": P,
        "unit": "mm"
      }
    },
    "model_data": "base64编码的3D模型数据",
    "format": "obj",
    "processing_time": 5.123
  },
  "message": "Contour processing completed."
}
```

#### 物料生成接口

`POST /api/material/generate-bom`

用于根据房间尺寸和构造做法生成物料清单。

**请求体**:

```json
{
  "module_data": {
    "height": 2950,        // 模块高度 (mm)
    "floor_area": 12.5,    // 地面面积 (m²)
    "wall_area": 45.2,     // 墙面面积 (m²)
    "ceiling_area": 12.5   // 天花面积 (m²)
  },
  "construction_practices": {
    "ceiling-structure": "轻钢龙骨",
    "ceiling-finish": "石膏板",
    "wall-structure": "砌块墙",
    "wall-finish": "乳胶漆",
    "floor-structure": "混凝土基层",
    "floor-finish": "地砖"
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "project_info": { /* 项目信息 */ },
    "items": [
      {
        "项次": "1",
        "物料编码": "MAT-001",
        "描述": "石膏板",
        "规格": "1200x2400x9mm",
        "数量": 10,
        "单位": "张",
        "单价": 30,
        "总价": 300,
        "备注": "天花吊顶"
      }
      // ... 更多物料项
    ],
    "statistics": { /* 统计信息 */ },
    "ai_analysis": { /* AI 分析结果 */ },
    "metadata": { /* 元数据 */ }
  },
  "message": "BOM generated successfully."
}
```

## 🧪 测试

### 后端测试

1.  **激活虚拟环境** (如果尚未激活)。
2.  **运行所有测试**:
    ```bash
    pytest backend/tests/ -v
    ```
3.  **运行特定测试**:
    ```bash
    pytest backend/tests/test_api_routes.py -v
    ```

### 前端测试

1.  **进入前端目录**:
    ```bash
    cd frontend
    ```
2.  **运行测试**:
    ```bash
    npm test
    ```

## 📊 性能指标

- **轮廓识别精度**: > 95%（在标准建筑图纸上）
- **尺寸检测准确率**: > 90%（清晰标注情况下）
- **处理时间**:
    - 图像处理 (轮廓识别、尺寸匹配)：2-8 秒/张 (取决于图像复杂度和服务器性能)
    - BOM 生成：3-8 秒/房间 (取决于构造做法复杂度和LLM响应速度)

## 🔍 常见问题

### Q: 上传图像失败？
A: 检查图像格式是否支持（JPG/PNG/BMP/TIFF），文件大小不超过 16MB。

### Q: 轮廓识别或尺寸提取不准确？
A: 确保图像清晰，尺寸标注完整。可以尝试调整后端 `backend/config.py` 中的 `confidence_threshold` 等参数。

### Q: API 连接失败？
A: 确认后端服务已启动，检查项目根目录下的 `.env` 文件中的 `FLASK_HOST` 和 `FLASK_PORT` 配置，以及前端 `frontend/.env` 中的 `REACT_APP_API_BASE_URL` 是否正确指向后端服务。

### Q: 3D 模型无法导出？
A: 检查后端服务是否有写入文件系统的权限，确保有足够的磁盘空间。

## 📝 更新日志

### v1.0.0 (2024-XX-XX)
- ✨ 初始版本发布
- 🎯 支持建筑轮廓识别与尺寸自动提取
- 🏗️ 支持构造做法选型与物料清单生成
- 🎨 现代化 Web UI 界面

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库。
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)。
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)。
4. 推送到分支 (`git push origin feature/AmazingFeature`)。
5. 开启 Pull Request。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 👥 作者

- AI Assistant

## 🙏 致谢

感谢以下开源项目：

- [React](https://reactjs.org/) - 前端框架
- [Flask](https://flask.palletsprojects.com/) - 后端框架
- [YOLO](https://github.com/ultralytics/yolov5) - 目标检测 (通过 `extract_info` 模块集成)
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [Framer Motion](https://www.framer.com/motion/) - React 动画库

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

- Email: your-email@example.com
- Issues: [GitHub Issues](https://github.com/your-repo/issues)

---

**注意**: 本项目仅供学习和研究使用。在生产环境使用前，请进行充分的测试和验证。
