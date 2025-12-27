"""应用配置"""

from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent


# 日志目录
LOG_DIR = PROJECT_ROOT / "logs"

# 日志配置文件
LOG_CONFIG_FILE = PROJECT_ROOT / "logging_config.json"

# 项目配置文件
PYPROJECT_FILE = PROJECT_ROOT.parent / "pyproject.toml"
