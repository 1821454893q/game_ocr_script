# core.py
import json
import logging
import logging.config
import os
from datetime import datetime
from typing import Dict, Any, Optional

import toml

from .handlers import TimestampRotatingFileHandler  # 如果分文件的话

# 如果单文件，直接把 TimestampRotatingFileHandler 放在上面


logging.TimestampRotatingFileHandler = TimestampRotatingFileHandler


class ExactLevelFilter(logging.Filter):
    """只允许精确匹配的日志级别通过"""

    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level


class SimpleLogger:
    """
    通用日志工具，支持：
    - 分级目录日志（debug/info/warn/error）
    - 按大小旋转 + 时间戳备份文件名
    - 自动创建默认配置
    - 项目隔离（不同项目不同日志目录、不同 logger 名称）
    """

    def __init__(
        self,
        project_name: str = "app",
        log_dir: str = "logs",
        config_file: Optional[str] = None,
        pyproject_file: Optional[str] = None,
        initial_level: str = "DEBUG",
    ):
        """
        参数：
            project_name: 项目名称，用于日志前缀和 logger 名称隔离
            log_dir: 日志根目录（绝对或相对路径）
            config_file: 配置文件路径，为 None 时自动生成在 log_dir/logging_config.json
            pyproject_file: 可选，用于自动读取项目名和版本（pyproject.toml）
            initial_level: 初始日志级别
        """
        self.project_name = project_name
        self.log_dir = os.path.abspath(log_dir)
        self.config_file = config_file or os.path.join(self.log_dir, "logging_config.json")
        self.pyproject_file = pyproject_file

        self._ensure_log_dirs()
        self._ensure_config_file_exists(initial_level)
        self._setup_logging()

        # 使用项目名隔离 logger，避免多项目冲突
        self.logger = logging.getLogger(f"simple_logger.{project_name}")

        if self.get_current_level() == "DEBUG":
            print(f"✅ [{project_name}] 日志初始化完成，配置路径: {self.config_file}")

    def _get_app_prefix(self) -> str:
        """尝试从 pyproject.toml 读取 name[version]，否则返回 project_name"""
        if not self.pyproject_file or not os.path.exists(self.pyproject_file):
            return self.project_name

        try:
            with open(self.pyproject_file, "r", encoding="utf-8") as f:
                data = toml.load(f)
            name = data.get("project", {}).get("name", self.project_name)
            version = data.get("project", {}).get("version", "")
            return f"{name} [{version}]" if version else name
        except Exception:
            return self.project_name

    def _ensure_log_dirs(self):
        dirs = ["debug", "info", "warn", "error"]
        for d in dirs:
            os.makedirs(os.path.join(self.log_dir, d), exist_ok=True)

    def _get_default_config(self, level: str = "DEBUG") -> Dict[str, Any]:
        prefix = self._get_app_prefix()

        debug_file = os.path.join(self.log_dir, "debug", "debug.log")
        info_file = os.path.join(self.log_dir, "info", "info.log")
        warn_file = os.path.join(self.log_dir, "warn", "warn.log")
        error_file = os.path.join(self.log_dir, "error", "error.log")

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": f"{prefix} - %(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"}
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file_debug": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "default",
                    "filename": debug_file,
                    "maxBytes": 10 * 1024 * 1024,  # 10MB
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_info": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "filename": info_file,
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_warn": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "WARNING",
                    "formatter": "default",
                    "filename": warn_file,
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_error": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "default",
                    "filename": error_file,
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                f"simple_logger.{self.project_name}": {
                    "level": level.upper(),
                    "handlers": ["console", "file_debug", "file_info", "file_warn", "file_error"],
                    "propagate": False,
                }
            },
        }

    def _ensure_config_file_exists(self, initial_level: str):
        if not os.path.exists(self.config_file):
            print(f"📝 创建默认日志配置文件: {self.config_file}")
            default_config = self._get_default_config(initial_level)
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)

    def _setup_logging(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 重新加载前缀（万一 pyproject 更新了）
            prefix = self._get_app_prefix()
            config["formatters"]["default"]["format"] = config["formatters"]["default"]["format"].split(" - ", 1)[-1]
            config["formatters"]["default"]["format"] = f"{prefix} - {config['formatters']['default']['format']}"

            logging.config.dictConfig(config)

            # 为每个文件 handler 添加精确级别过滤器
            logger_name = f"simple_logger.{self.project_name}"
            for handler in logging.getLogger(logger_name).handlers:
                if isinstance(handler, TimestampRotatingFileHandler):
                    if "debug.log" in handler.baseFilename:
                        handler.addFilter(ExactLevelFilter(logging.DEBUG))
                    elif "info.log" in handler.baseFilename:
                        handler.addFilter(ExactLevelFilter(logging.INFO))
                    elif "warn.log" in handler.baseFilename:
                        handler.addFilter(ExactLevelFilter(logging.WARNING))
                    elif "error.log" in handler.baseFilename:
                        handler.addFilter(ExactLevelFilter(logging.ERROR))

        except Exception as e:
            print(f"❌ 日志配置加载失败: {e}")
            logging.basicConfig(
                level=logging.INFO,
                format=f"{self._get_app_prefix()} - %(asctime)s - %(levelname)s - %(message)s",
            )

    def update_level(self, new_level: str) -> bool:
        new_level = new_level.upper()
        valid = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if new_level not in valid:
            print(f"❌ 无效级别: {new_level}，可选: {valid}")
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            logger_key = f"simple_logger.{self.project_name}"
            if logger_key in config["loggers"]:
                config["loggers"][logger_key]["level"] = new_level

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._setup_logging()
            print(f"✅ [{self.project_name}] 日志级别更新为: {new_level}")
            return True
        except Exception as e:
            print(f"❌ 更新失败: {e}")
            return False

    def get_current_level(self) -> str:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config["loggers"][f"simple_logger.{self.project_name}"]["level"]
        except Exception:
            return "UNKNOWN"


# 推荐的工厂函数（放在 __init__.py 中方便导入）
def create_logger(
    project_name: str = "app",
    log_dir: str = "logs",
    config_file: Optional[str] = None,
    pyproject_file: Optional[str] = None,
    initial_level: str = "DEBUG",
) -> logging.Logger:
    """
    快速创建 logger 的工厂函数
    """
    return SimpleLogger(
        project_name=project_name,
        log_dir=log_dir,
        config_file=config_file,
        pyproject_file=pyproject_file,
        initial_level=initial_level,
    ).logger
