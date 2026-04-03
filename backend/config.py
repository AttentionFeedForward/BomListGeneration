"""
Flask应用配置文件
包含开发、测试、生产环境的配置
"""

import os
from dotenv import load_dotenv

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(os.path.dirname(basedir), ".env"))


class Config:
    """基础配置类"""

    # Flask基础配置
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"

    # 服务器配置
    HOST = os.environ.get("FLASK_HOST") or "0.0.0.0"
    PORT = int(os.environ.get("FLASK_PORT") or 5000)
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

    # 文件上传配置
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(basedir, "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff"}

    # 模块识别配置
    MODULE_DETECTION_CONFIG = {
        "angle_threshold": 2.0,  # 角度阈值（度）
        "enable_scale_filter": True,  # 是否启用比例因子过滤
        "scale_deviation_threshold": 0.05,  # 比例因子过滤的偏差阈值
        "collinear_threshold": 3.0,  # 共线性判断的距离阈值（像素）
        "confidence_threshold": 0.3,  # 置信度阈值
    }

    # OCR配置
    OCR_CONFIG = {"lang": "ch", "use_gpu": False, "use_angle_cls": True, "show_log": False}

    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保上传目录存在
        upload_folder = app.config["UPLOAD_FOLDER"]
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)


class DevelopmentConfig(Config):
    """开发环境配置"""

    DEBUG = True


class TestingConfig(Config):
    """测试环境配置"""

    TESTING = True
    DEBUG = True
    # 测试时使用内存数据库
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境配置"""

    DEBUG = False

    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"


# 配置字典
config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}