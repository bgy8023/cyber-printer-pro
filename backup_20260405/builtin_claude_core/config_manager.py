
import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from .logger import logger


class ConfigManager:
    """
    配置管理器
    支持 YAML/JSON 配置文件，统一管理所有设置
    """
    def __init__(self, config_dir: str = "configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "app_config.yaml"
        self.config: Dict[str, Any] = {}
        self._load_config()
        logger.info("✅ ConfigManager 初始化完成")

    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f) or {}
                logger.info(f"📂 配置文件已加载：{self.config_file}")
            except Exception as e:
                logger.error(f"❌ 配置文件加载失败：{str(e)}")
                self.config = self._get_default_config()
        else:
            self.config = self._get_default_config()
            self._save_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "generation": {
                "default_words": 7500,
                "min_words": 1000,
                "max_words": 20000,
                "max_retry": 5,
                "timeout": 300,
                "auto_supplement": True,
                "supplement_threshold": 0.95
            },
            "agents": {
                "outline_agent": {"enabled": True, "timeout": 60},
                "writer_agent": {"enabled": True, "timeout": 240},
                "review_agent": {"enabled": True, "timeout": 120},
                "polish_agent": {"enabled": True, "timeout": 180}
            },
            "undercover_mode": {
                "enabled": True,
                "strictness": "high"  # low, medium, high
            },
            "memory": {
                "max_history_chapters": 10,
                "compression_enabled": True,
                "auto_update": True
            },
            "daemon": {
                "enabled": False,
                "gen_hour": 3,
                "process_lock": True,
                "max_failures": 3
            },
            "templates": {
                "default": "番茄爆款",
                "available": ["番茄爆款", "玄幻修仙", "都市神医", "科幻末世"]
            }
        }

    def _save_config(self):
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True, default_flow_style=False)
            logger.info(f"💾 配置文件已保存：{self.config_file}")
        except Exception as e:
            logger.error(f"❌ 配置文件保存失败：{str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项，支持点号分隔的路径"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """设置配置项，支持点号分隔的路径"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self._save_config()
        logger.info(f"📝 配置已更新：{key} = {value}")

    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        self._deep_update(self.config, updates)
        self._save_config()
        logger.info(f"📝 配置已批量更新")

    def _deep_update(self, base_dict: dict, update_dict: dict):
        """深度更新字典"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def reset_to_default(self):
        """重置为默认配置"""
        self.config = self._get_default_config()
        self._save_config()
        logger.info("🔄 配置已重置为默认值")

    def export_to_json(self, filepath: str):
        """导出配置为 JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"📤 配置已导出：{filepath}")
        except Exception as e:
            logger.error(f"❌ 配置导出失败：{str(e)}")

    def import_from_json(self, filepath: str):
        """从 JSON 导入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            self.update(imported_config)
            logger.info(f"📥 配置已导入：{filepath}")
        except Exception as e:
            logger.error(f"❌ 配置导入失败：{str(e)}")
