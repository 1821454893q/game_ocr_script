# src/window_capture.py
import math
import random
import pygetwindow as gw
import win32gui
import win32ui
import win32con
import win32api
import ctypes
from ctypes import windll, wintypes
from typing import Optional, Tuple, List, Union
import cv2
import numpy as np
import time

from gas.interfaces.interfaces import IDeviceProvider
from gas.cons.key_code import KeyCode, get_windows_keycode
from gas.util.keymouse_util import KeyMouseUtil
from gas.util.hwnd_util import get_hwnd_by_class_and_title
from gas.util.screenshot_util import screenshot, screenshot_bitblt

from gas.logger import get_logger
from gas.util.wrap_util import timeit

logger = get_logger()


class WinProvider(IDeviceProvider):
    """Windows窗口管理工具 - 包含截图和后台操作"""

    def __init__(
        self, window_title: str = None, class_name: str = None, capture_mode: int = 1, activate_windows: bool = False
    ):
        self.window_title = window_title
        self.class_name = class_name
        self._hwnd = None
        self._window = None
        self._capture_mode = capture_mode
        self.activate_windows = activate_windows

        if window_title:
            self._find_and_set_hwnd(window_title, class_name)

    def _find_and_set_hwnd(self, window_title: str, class_name: str) -> bool:
        """查找并设置目标窗口"""
        try:
            hwndList = get_hwnd_by_class_and_title(class_name, window_title)

            if len(hwndList) == 0:
                logger.error(f"❎ 查未找到窗口: {window_title} 类名：{class_name}")
                return False

            self._hwnd = hwndList[0]
            self.window_title = win32gui.GetWindowText(self._hwnd)
            self.class_name = win32gui.GetClassName(self._hwnd)

            logger.info(
                f"✅ 找到窗口 数量:{len(hwndList)} 标题: {self.window_title} 类名：{self.class_name} (HWND: {self._hwnd})"
            )
            return True

        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return False

    def get_size(self) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口尺寸和位置

        Returns:
            Tuple[int, int, int, int]: (width, height, left, top)
        """
        if not self.is_available():
            return None

        try:
            left, top, right, bottom = win32gui.GetWindowRect(self._hwnd)
            width = right - left
            height = bottom - top

            logger.debug(f"窗口尺寸: {width}x{height}, 位置: ({left}, {top})")
            return width, height, left, top

        except Exception as e:
            logger.error(f"获取窗口尺寸失败: {e}")
            return None

    # ==================== 窗口管理功能 ====================

    def set_window(self, window_title: str) -> bool:
        """设置目标窗口"""
        return self._find_and_set_hwnd(window_title)

    def get_window_info(self) -> Optional[dict]:
        """获取窗口信息"""
        if not self._hwnd:
            return None

        try:
            x, y, w, h = win32gui.GetWindowRect(self)

            info = {
                "title": self.window_title,
                "calssName": self.class_name,
                "hwnd": self._hwnd,
                "position": (x, y),
                "size": (w, h),
            }
            return info
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None

    # ==================== 截图功能 ====================

    @timeit
    def capture(self) -> Optional[np.ndarray]:
        """截图当前窗口"""
        if not self._hwnd:
            logger.error("未设置目标窗口，请先调用 set_window()")
            return None

        try:
            if self._capture_mode == 1:
                scr = screenshot_bitblt(self._hwnd)
            elif self._capture_mode == 2:
                scr = screenshot(self._hwnd)

            if screenshot is not None:
                logger.debug(f"截图成功，尺寸: {scr.shape}")
            else:
                logger.error("截图失败")

            return scr

        except Exception as e:
            logger.error(f"截图异常: {e}")
            return None

    # ==================== 后台鼠标操作 ====================
    def move_mouse(self, x: int, y: int) -> bool:
        """移动鼠标"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
            # 激活窗口
            if self.activate_windows:
                KeyMouseUtil.window_activate(self._hwnd)
            KeyMouseUtil.mouse_move(x, y)
            logger.debug(f"后台移动鼠标到: ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"后台移动鼠标失败: {e}")
            return False

    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        """发送按键事件 - 自动转换为Windows键码"""
        try:
            if not self.is_available():
                return False
            # 激活窗口
            if self.activate_windows:
                KeyMouseUtil.window_activate(self._hwnd)
            # 转换为Windows键码
            win_keycode = get_windows_keycode(keycode)
            key_name = keycode.name
            if win_keycode == 0:
                logger.error(f"未知的按键代码: {key_name}")
                return False

            if action == "tap" or action == "press":
                # 按下并释放
                KeyMouseUtil.tap_key(self._hwnd, win_keycode)
            elif action == "down":
                # 按下
                KeyMouseUtil.key_down(self._hwnd, win_keycode)
            elif action == "up":
                # 释放
                KeyMouseUtil.key_up(self._hwnd, win_keycode)
            else:
                logger.error(f"不支持的按键动作: {action}")
                return False
            logger.debug(f"窗口按键: {action} {key_name}(win:{win_keycode})")
            return True
        except Exception as e:
            logger.error(f"窗口按键异常: {e}")
            return False

    def click(self, x: int, y: int, action: str = "tap") -> bool:
        # 激活窗口
        if self.activate_windows:
            KeyMouseUtil.window_activate(self._hwnd)

        if action == "tap":
            return KeyMouseUtil.click(self._hwnd, x, y) is None

        if action == "down":
            return KeyMouseUtil.mouse_left_down(self._hwnd, x, y) is None

        if action == "up":
            return KeyMouseUtil.mouse_left_up(self._hwnd, x, y) is None

    def swipe(self, x1: int, y1: int, x2: int, y2: int, is_drga: bool = True, duration: float = 0.5) -> bool:
        """
        统一的滑动方法

        Args:
            x1, y1: 起始坐标
            x2, y2: 结束坐标
            is_drga: 是否拖拽（True=带按下状态的滑动，False=仅移动）
            duration: 总持续时间
        """
        try:
            # 激活窗口
            if self.activate_windows:
                KeyMouseUtil.window_activate(self._hwnd)

            # 移动到起点
            KeyMouseUtil.mouse_action(self._hwnd, x1, y1, "move", 0.03)

            if is_drga:
                # 拖拽模式：按下左键
                KeyMouseUtil.mouse_action(self._hwnd, x1, y1, "down", 0.05)

            # 计算移动路径
            distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            num_points = max(3, int(distance / 10))

            # 移动过程
            for i in range(num_points):
                t = i / (num_points - 1)
                # 线性插值 + 随机波动
                x = x1 + (x2 - x1) * t + random.randint(-3, 3)
                y = y1 + (y2 - y1) * t + random.randint(-3, 3)

                # 根据模式选择移动类型
                action_type = "drag" if is_drga else "move"
                KeyMouseUtil.mouse_action(self._hwnd, int(x), int(y), action_type, 0)

                # 控制移动速度
                time.sleep(duration / num_points * random.uniform(0.9, 1.1))

            # 确保到达终点
            action_type = "drag" if is_drga else "move"
            KeyMouseUtil.mouse_action(self._hwnd, x2, y2, action_type, 0.05)

            if is_drga:
                # 拖拽模式：松开左键
                KeyMouseUtil.mouse_action(self._hwnd, x2, y2, "up", 0.05)

            return True

        except Exception as e:
            print(f"滑动失败: {e}")
            # 异常时确保松开左键
            if is_drga:
                try:
                    KeyMouseUtil.mouse_action(self._hwnd, x2, y2, "up", 0)
                except:
                    pass
            return False

    def mouse_action(self, x: int, y: int, action: str = "move", delay: float = 0.01) -> bool:
        """
        低级鼠标操作 - 直接调用 KeyMouseUtil
        """
        try:
            if not self._hwnd:
                logger.error("未设置目标窗口")
                return False

            if self.activate_windows:
                KeyMouseUtil.window_activate(self._hwnd)

            KeyMouseUtil.mouse_action(self._hwnd, x, y, action, delay)
            logger.debug(f"鼠标操作: {action} at ({x}, {y}) delay={delay}")
            return True

        except Exception as e:
            logger.error(f"鼠标操作失败 {action} ({x},{y}): {e}")
            return False

    def input_text(self, text: str) -> bool:
        """输入文本"""
        pass

    def is_available(self) -> bool:
        return True

    def get_info(self) -> dict:
        """获取设备信息"""
        pass
