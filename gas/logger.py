# simple_logger.py
import logging
import logging.config
import json
import os
from datetime import datetime
from typing import Dict, Any

import toml
from gas.settings import LOG_CONFIG_FILE, PYPROJECT_FILE

from logging.handlers import RotatingFileHandler


class TimestampRotatingFileHandler(RotatingFileHandler):
    """
    自定义 RotatingFileHandler：
    旋转时，将旧日志文件重命名为 filename_YYYY-MM-DD_HH-MM-SS.log
    并自动清理超过 backupCount 的旧文件（按时间排序删除最旧的）
    """

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        # 当前时间戳（到秒）
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # 备份当前文件为带时间戳的文件
        if os.path.exists(self.baseFilename):
            backup_name = f"{self.baseFilename[:-4]}_{timestamp}.log"  # 去掉 .log 后缀再加
            os.replace(self.baseFilename, backup_name)

        # 清理旧备份文件，只保留最近 backupCount 个
        dir_name = os.path.dirname(self.baseFilename)
        base_name = os.path.basename(self.baseFilename[:-4])  # 如 "debug"

        backups = [f for f in os.listdir(dir_name) if f.startswith(base_name + "_") and f.endswith(".log")]
        # 按文件名中的时间戳排序（时间戳格式固定，可直接字符串排序）
        backups.sort(reverse=True)  # 最新的在前

        # 删除多余的旧文件
        for old in backups[self.backupCount :]:
            os.remove(os.path.join(dir_name, old))

        if not self.delay:
            self.stream = self._open()


logging.TimestampRotatingFileHandler = TimestampRotatingFileHandler


class SimpleLogger:
    """简单统一的日志工具（分级目录 + 按大小旋转 + 时间戳备份文件）"""

    def __init__(self, config_file: str = "", pyproject_file: str = ""):
        self.config_file = config_file or str(LOG_CONFIG_FILE)
        self.pyproject_file = pyproject_file or str(PYPROJECT_FILE)

        self._ensure_config_file_exists()
        self._setup_logging()
        self.logger = logging.getLogger("app")
        if self.get_current_level() == "DEBUG":
            print(f"✅ 日志配置已加载  path:{self.config_file}")

    def get_app(self) -> str:
        try:
            with open(self.pyproject_file, "r", encoding="utf-8") as f:
                data = toml.load(f)
            name = data.get("project", {}).get("name", "gas")
            version = data.get("project", {}).get("version", "")
            return f"{name} [{version}]" if version else name
        except Exception:
            return "gas"

    def _ensure_log_dirs(self):
        dirs = ["logs/debug", "logs/info", "logs/warn", "logs/error"]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

    def _get_default_config(self) -> Dict[str, Any]:
        self._ensure_log_dirs()

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"}
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
                    "filename": "logs/debug/debug.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_info": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "filename": "logs/info/info.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_warn": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "WARNING",
                    "formatter": "default",
                    "filename": "logs/warn/warn.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
                "file_error": {
                    "class": "logging.TimestampRotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "default",
                    "filename": "logs/error/error.log",
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
            },
            "loggers": {
                "app": {
                    "level": "DEBUG",
                    "handlers": [
                        "console",
                        "file_debug",
                        "file_info",
                        "file_warn",
                        "file_error",
                    ],
                    "propagate": False,
                }
            },
        }

    def _ensure_config_file_exists(self):
        if not os.path.exists(self.config_file):
            print(f"📝 创建默认日志配置文件 path:{self.config_file}")
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._get_default_config(), f, indent=4, ensure_ascii=False)
        self._ensure_log_dirs()

    def _setup_logging(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            app_prefix = self.get_app()
            config["formatters"]["default"]["format"] = f"{app_prefix} - {config['formatters']['default']['format']}"

            # 先应用配置（创建所有 handler）
            logging.config.dictConfig(config)

            for handler in logging.getLogger("app").handlers:
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
            print(f"❌ 日志配置失败: {e}")
            logging.basicConfig(
                level=logging.INFO,
                format=f"{self.get_app()} - %(asctime)s - %(levelname)s - %(message)s",
            )

    def update_level(self, new_level: str):
        new_level = new_level.upper()
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if new_level not in valid_levels:
            print(f"❌ 无效的日志级别: {new_level}，有效值: {list(valid_levels)}")
            return False

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            if "app" in config["loggers"]:
                config["loggers"]["app"]["level"] = new_level

            for handler_name, handler_cfg in config["handlers"].items():
                if handler_name.startswith("file_") and "level" in handler_cfg:
                    if new_level == "DEBUG" or (new_level == "INFO" and handler_cfg["level"] == "DEBUG"):
                        handler_cfg["level"] = new_level

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self._setup_logging()
            print(f"✅ 日志级别已更新为: {new_level}")
            return True
        except Exception as e:
            print(f"❌ 更新日志级别失败: {e}")
            return False

    def get_current_level(self) -> str:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config["loggers"]["app"]["level"]
        except Exception:
            return "UNKNOWN"


# 全局实例
_log_instance: SimpleLogger | None = None


def get_logger() -> logging.Logger:
    global _log_instance
    if _log_instance is None:
        _log_instance = SimpleLogger()
    return _log_instance.logger


def update_level(new_level: str):
    global _log_instance
    if _log_instance is None:
        print("❌ 日志实例未初始化")
        return False
    return _log_instance.update_level(new_level)


def get_level() -> str | None:
    global _log_instance
    if _log_instance is None:
        print("❌ 日志实例未初始化")
        return None
    return _log_instance.get_current_level()


class ExactLevelFilter(logging.Filter):
    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record):
        return record.levelno == self.level
