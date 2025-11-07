# src/interfaces.py
from abc import ABC, abstractmethod
from ctypes import Union
from typing import Optional, Tuple
import numpy as np

from ocr_tool.key_code import KeyCode


class IScreenshotProvider(ABC):
    """截图提供者接口"""

    @abstractmethod
    def capture(self) -> Optional[np.ndarray]:
        """截图"""
        pass

    @abstractmethod
    def get_size(self) -> Optional[Tuple[int, int, int, int]]:
        """获取屏幕/窗口尺寸

        Args:
            Returns:
                Tuple[int, int, int, int]: (width, height, left, top)
        """
        pass


class IInputProvider(ABC):
    """输入提供者接口"""

    @abstractmethod
    def click(self, x: int, y: int) -> bool:
        """点击坐标"""
        pass

    @abstractmethod
    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """滑动"""
        pass

    @abstractmethod
    def input_text(self, text: str) -> bool:
        """输入文本"""
        pass

    @abstractmethod
    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        """按键事件
        Args:
            keycode: 按键代码
            action: 动作类型 - "tap"(点击), "down"(按下), "up"(抬起)
        """
        pass


class IDeviceProvider(IScreenshotProvider, IInputProvider):
    """设备提供者接口（组合接口）"""

    @abstractmethod
    def is_available(self) -> bool:
        """检查是否可用"""
        pass

    @abstractmethod
    def get_info(self) -> dict:
        """获取设备信息"""
        pass
