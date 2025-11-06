# simple_logger.py
import logging
import logging.config
import json
import os
from typing import Dict, Any


class SimpleLogger:
    """简单统一的日志工具"""

    def __init__(self, config_file: str = "logging_config.json"):
        self.config_file = config_file
        self._ensure_config_file_exists()
        self._setup_logging()
        self.logger = logging.getLogger("app")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "detailed": {
                    "format": "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
                },
                "simple": {"format": "%(asctime)s - %(levelname)s - %(message)s"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
                "file_debug": {
                    "class": "logging.FileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "logs/debug.log",
                    "encoding": "utf-8",
                },
                "file_info": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": "logs/info.log",
                    "encoding": "utf-8",
                },
                "file_error": {
                    "class": "logging.FileHandler",
                    "level": "WARNING",
                    "formatter": "detailed",
                    "filename": "logs/error.log",
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "app": {
                    "level": "DEBUG",
                    "handlers": ["console", "file_debug", "file_info", "file_error"],
                    "propagate": False,
                }
            },
        }

    def _ensure_config_file_exists(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_file):
            print("📝 创建默认日志配置文件")
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._get_default_config(), f, indent=4, ensure_ascii=False)

        # 确保日志目录存在
        os.makedirs("logs", exist_ok=True)

    def _setup_logging(self):
        """设置日志配置"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            logging.config.dictConfig(config)
            print("✅ 日志配置已加载")
        except Exception as e:
            print(f"❌ 日志配置失败: {e}")
            # 使用基础配置作为后备
            logging.basicConfig(
                level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
            )

    def update_level(self, new_level: str):
        """更新日志级别"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if new_level.upper() not in valid_levels:
            print(f"❌ 无效的日志级别: {new_level}，有效值: {valid_levels}")
            return False

        try:
            # 读取当前配置
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 更新级别
            config["loggers"]["app"]["level"] = new_level.upper()
            for handler in config["handlers"].values():
                if handler["level"] in ["DEBUG", "INFO", "WARNING"]:
                    handler["level"] = new_level.upper()

            # 保存配置
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            # 重新加载配置
            self._setup_logging()

            self.info(f"日志级别已更新为: {new_level.upper()}")
            return True

        except Exception as e:
            print(f"❌ 更新日志级别失败: {e}")
            return False

    def get_current_level(self) -> str:
        """获取当前日志级别"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config["loggers"]["app"]["level"]
        except:
            return "UNKNOWN"


# 全局日志实例
_log_instance = None


def get_logger() -> logging.Logger:
    """获取全局日志实例"""
    global _log_instance
    if _log_instance is None:
        _log_instance = SimpleLogger()
    return _log_instance.logger


def update_level(new_level: str):
    """更新日志级别"""
    if _log_instance is None:
        print("日志实例未初始化")
        return
    return _log_instance.update_level(new_level)


def get_level() -> str:
    """获取当前日志级别"""
    if _log_instance is None:
        print("日志实例未初始化")
        return
    return _log_instance.get_current_level()
