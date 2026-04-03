"""
Flask后端主应用文件
提供模块识别功能的RESTful API服务
"""

import os
import sys
from flask import Flask
from flask_cors import CORS
from config import Config, config

# 添加项目根目录到Python路径，以便导入dimension_matcher模块
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def create_app(config_name=None):
    """
    Flask应用工厂函数

    Args:
        config_name: 配置名称，默认为None（使用默认配置）

    Returns:
        Flask应用实例
    """
    app = Flask(__name__)
    
    # 根据配置名称选择配置类
    if config_name and config_name in config:
        app.config.from_object(config[config_name])
    else:
        app.config.from_object(Config)

    # 启用CORS支持，允许前端跨域访问
    CORS(
        app,
        supports_credentials=True,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:3000",
                    "http://localhost:3001",
                    "http://127.0.0.1:3000",
                    "http://10.1.24.95:3000"
                ],
                "methods": ["GET", "POST", "OPTIONS"],
                "headers": ["Content-Type", "Authorization", "X-Request-Time"],
                "max_age": 600,
            }
        },
    )

    # 注册蓝图
    from api.module_routes import module_bp
    from api.material_routes import material_bp
    from api.layout_routes import layout_bp

    app.register_blueprint(module_bp)
    app.register_blueprint(material_bp)
    app.register_blueprint(layout_bp)

    # 健康检查路由
    @app.route("/health")
    def health_check():
        """健康检查接口"""
        return {"status": "healthy", "message": "BOM Backend API is running"}

    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        """404错误处理"""
        return {"error": "Not found", "message": "The requested resource was not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """500错误处理"""
        return {"error": "Internal server error", "message": "An internal error occurred"}, 500

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host=app.config.get("HOST", "0.0.0.0"),
        port=app.config.get("PORT", 5000),
        debug=app.config.get("DEBUG", True),
        use_reloader=False,
    )
