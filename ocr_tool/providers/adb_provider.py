# src/providers/adb_provider.py
from ctypes import Union
import subprocess
import cv2
import numpy as np
from typing import Optional, Tuple

from ocr_tool.key_code import KeyCode, get_android_keycode
from ..interfaces import IDeviceProvider
from ..logger import get_logger

logger = get_logger()


class ADBProvider(IDeviceProvider):
    """ADB提供者 - 使用ADB命令"""

    def __init__(self, adb_path: str, device_id: str = None):
        self.adb_path = adb_path
        self.device_id = device_id
        self._screen_size = None

    def _build_cmd(self, command: list) -> list:
        """构建ADB命令"""
        if self.device_id:
            return [self.adb_path, "-s", self.device_id] + command
        else:
            return [self.adb_path] + command

    def is_available(self) -> bool:
        """检查ADB是否可用"""
        try:
            result = subprocess.run(
                self._build_cmd(["get-state"]), capture_output=True, text=True, timeout=5
            )
            return "device" in result.stdout
        except:
            return False

    def capture(self) -> Optional[np.ndarray]:
        """ADB截图"""
        try:
            cmd = self._build_cmd(["exec-out", "screencap", "-p"])
            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                img_array = np.frombuffer(result.stdout, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                if img is not None:
                    self._screen_size = (img.shape[1], img.shape[0])
                    logger.debug(f"ADB截图成功: {img.shape[1]}x{img.shape[0]}")
                    return img

            logger.error("ADB截图失败")
            return None

        except subprocess.TimeoutExpired:
            logger.error("ADB截图超时")
            return None
        except Exception as e:
            logger.error(f"ADB截图异常: {e}")
            return None

    def get_size(self) -> Optional[Tuple[int, int]]:
        """获取屏幕尺寸"""
        if self._screen_size:
            return self._screen_size

        try:
            cmd = self._build_cmd(["shell", "wm", "size"])
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                size_str = result.stdout.strip().split(": ")[1]
                width, height = map(int, size_str.split("x"))
                self._screen_size = (width, height)
                return self._screen_size
        except:
            pass

        return None

    def click(self, x: int, y: int) -> bool:
        """ADB点击"""
        try:
            cmd = self._build_cmd(["shell", "input", "tap", str(x), str(y)])
            result = subprocess.run(cmd, capture_output=True, timeout=5)

            success = result.returncode == 0
            if success:
                logger.debug(f"ADB点击: ({x}, {y})")
            else:
                logger.error(f"ADB点击失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"ADB点击异常: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """ADB滑动"""
        try:
            cmd = self._build_cmd(
                ["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)]
            )
            result = subprocess.run(cmd, capture_output=True, timeout=5)

            success = result.returncode == 0
            if success:
                logger.debug(f"ADB滑动: ({x1},{y1}) -> ({x2},{y2})")
            else:
                logger.error(f"ADB滑动失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"ADB滑动异常: {e}")
            return False

    def input_text(self, text: str) -> bool:
        """ADB输入文本"""
        try:
            # 清理文本中的特殊字符
            cleaned_text = text.replace(" ", "%s").replace("&", "\&")
            cmd = self._build_cmd(["shell", "input", "text", cleaned_text])
            result = subprocess.run(cmd, capture_output=True, timeout=5)

            success = result.returncode == 0
            if success:
                logger.debug(f"ADB文本输入: {text}")
            else:
                logger.error(f"ADB文本输入失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"ADB文本输入异常: {e}")
            return False

    def get_info(self) -> dict:
        """获取ADB设备信息"""
        try:
            # 获取设备型号
            model_cmd = self._build_cmd(["shell", "getprop", "ro.product.model"])
            model_result = subprocess.run(model_cmd, capture_output=True, text=True)
            model = model_result.stdout.strip() if model_result.returncode == 0 else "Unknown"

            size = self.get_size()

            return {
                "type": "adb",
                "device_id": self.device_id,
                "model": model,
                "size": size,
                "adb_path": self.adb_path,
            }
        except Exception as e:
            logger.error(f"获取ADB设备信息异常: {e}")
            return {}

    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        """发送ADB按键事件 - 自动转换为Android键码"""
        try:
            # 转换为Android键码
            android_keycode = get_android_keycode(keycode)
            key_name = keycode.name
            if android_keycode == 0:
                logger.error(f"未知的按键代码: {key_name}")
                return False

            if action == "tap" or action == "press":
                cmd = self._build_cmd(["shell", "input", "keyevent", str(android_keycode)])
            elif action == "down":
                cmd = self._build_cmd(
                    ["shell", "input", "keyevent", str(android_keycode), "--longpress"]
                )
            elif action == "up":
                logger.warning("ADB不支持单独的key up事件，使用tap代替")
                cmd = self._build_cmd(["shell", "input", "keyevent", str(android_keycode)])
            else:
                logger.error(f"不支持的按键动作: {action}")
                return False

            result = subprocess.run(cmd, capture_output=True, timeout=5)
            success = result.returncode == 0

            if success:
                logger.debug(f"ADB按键: {action} {key_name}(android:{android_keycode})")
            else:
                logger.error(f"ADB按键失败: {result.stderr}")

            return success

        except Exception as e:
            logger.error(f"ADB按键异常: {e}")
            return False
