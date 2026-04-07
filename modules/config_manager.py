#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块

负责加载和管理系统配置，包括YAML配置文件和环境变量。
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径 (不再默认使用 config.yaml)
        """
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / config_file if config_file else None
        self._config = {}
        
        # 加载环境变量
        self._load_env()
        
        # 如果提供了配置文件，则加载
        if self.config_file:
            self._load_config()
    
    def _load_env(self):
        """加载环境变量"""
        env_file = self.project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
    
    def _load_config(self):
        """加载YAML配置文件"""
        if self.config_file and self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except Exception as e:
                # 仅在明确提供了配置文件且加载失败时打印警告
                print(f"警告: 无法加载配置文件 {self.config_file}: {e}")
                self._config = {}
        
        # 用环境变量覆盖配置
        self._override_with_env()
    
    def _override_with_env(self):
        """用环境变量覆盖配置"""
        # API配置
        if os.getenv('OPENAI_API_KEY'):
            self._set_nested('api.openai_api_key', os.getenv('OPENAI_API_KEY'))
        
        if os.getenv('OPENAI_BASE_URL'):
            self._set_nested('api.base_url', os.getenv('OPENAI_BASE_URL'))
        
        # 系统配置
        if os.getenv('APP_DEBUG'):
            self._set_nested('system.debug', os.getenv('APP_DEBUG').lower() == 'true')
        
        if os.getenv('LOG_LEVEL'):
            self._set_nested('system.log_level', os.getenv('LOG_LEVEL'))
    
    def _set_nested(self, key: str, value: Any):
        """设置嵌套配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        config = self._config
        
        try:
            for k in keys:
                config = config[k]
            return config
        except (KeyError, TypeError):
            return default
    
    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置
        
        Returns:
            API配置字典
        """
        return {
            'api_key': self.get('api.openai_api_key'),
            'base_url': self.get('api.base_url'),
            'model': self.get('api.model', 'gpt-3.5-turbo'),
            'temperature': self.get('api.temperature', 0.2),
            'max_tokens': self.get('api.max_tokens', 2000)
        }
    
    def get_paths(self) -> Dict[str, Path]:
        """获取文件路径配置
        
        Returns:
            路径配置字典
        """
        return {
            'construction_methods': self.project_root / self.get('paths.construction_methods', '构造做法.json'),
            'output_template': self.project_root / self.get('paths.output_template', '输出结果.txt'),
            'logs': self.project_root / self.get('paths.logs', 'logs')
        }
    
    def is_debug(self) -> bool:
        """是否为调试模式
        
        Returns:
            是否为调试模式
        """
        return self.get('system.debug', False)
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """验证配置
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需的API配置 (这些可以通过环境变量获取，所以如果都没有则报错)
        if not self.get('api.openai_api_key'):
            # 只有当环境变量中也没有时才报错
            if not os.getenv('OPENAI_API_KEY'):
                errors.append("缺少OpenAI API密钥")
        
        return len(errors) == 0, errors