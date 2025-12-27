# handlers.py
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler


class TimestampRotatingFileHandler(RotatingFileHandler):
    """
    自定义 RotatingFileHandler：
    - 旋转时重命名为 filename_YYYY-MM-DD_HH-MM-SS.log
    - 自动清理超过 backupCount 的旧备份文件（按时间排序）
    """

    def doRollover(self):
        if self.stream:
            self.stream.close()
            self.stream = None

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        if os.path.exists(self.baseFilename):
            backup_name = f"{self.baseFilename[:-4]}_{timestamp}.log"
            os.replace(self.baseFilename, backup_name)

        # 清理旧备份
        dir_name = os.path.dirname(self.baseFilename)
        if not os.path.isdir(dir_name):
            return

        base_name = os.path.basename(self.baseFilename[:-4])  # 如 "debug"

        backups = [f for f in os.listdir(dir_name) if f.startswith(base_name + "_") and f.endswith(".log")]
        backups.sort(reverse=True)  # 最新在前

        for old in backups[self.backupCount :]:
            os.remove(os.path.join(dir_name, old))

        if not self.delay:
            self.stream = self._open()
