import random
import time

import win32api
import win32con
import win32gui

from gas.logger import get_logger

logger = get_logger()


###### Keyboard ######
class KeyMouseUtil:

    @classmethod
    def tap_key(self, hwnd, key: str | int, seconds: float = 0.0):
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
        self.__sleep(seconds)
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)

    @classmethod
    def key_down(self, hwnd, key: int | str, seconds: float = 0.0):
        win32gui.PostMessage(hwnd, win32con.WM_KEYDOWN, key, 0)
        self.__sleep(seconds)

    @classmethod
    def key_up(self, hwnd, key: int | str, seconds: float = 0.0):
        win32gui.PostMessage(hwnd, win32con.WM_KEYUP, key, 0)
        self.__sleep(seconds)

    ###### Mouse ######

    @classmethod
    def click(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        self.__sleep(seconds)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)

    @classmethod
    def mouse_left_down(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
        self.__sleep(seconds)

    @classmethod
    def mouse_left_up(self, hwnd, x: int, y: int, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)
        self.__sleep(seconds)

    @classmethod
    def right_click(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, l_param)
        self.__sleep(seconds)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, l_param)

    @classmethod
    def mouse_right_down(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONDOWN, win32con.MK_RBUTTON, l_param)
        self.__sleep(seconds)

    @classmethod
    def mouse_right_up(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_RBUTTONUP, 0, l_param)
        self.__sleep(seconds)

    @classmethod
    def middle_click(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_MBUTTON, l_param)
        self.__sleep(seconds)
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONUP, win32con.MK_MBUTTON, l_param)

    @classmethod
    def mouse_middle_down(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONDOWN, win32con.MK_RBUTTON, l_param)
        self.__sleep(seconds)

    @classmethod
    def mouse_middle_up(self, hwnd, x: int | float = 0, y: int | float = 0, seconds: float = 0.0):
        x = int(x)
        y = int(y)
        l_param = win32api.MAKELONG(x, y)
        win32gui.PostMessage(hwnd, win32con.WM_MBUTTONUP, 0, l_param)
        self.__sleep(seconds)

    @classmethod
    def mouse_move(self, hwnd, x: int | float, y: int | float, seconds: float = 0.0):
        KeyMouseUtil.window_activate(hwnd)
        lParam = win32api.MAKELONG(x, y)
        win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
        self.__sleep(seconds)

    @classmethod
    def mouse_action(
        cls, hwnd, x: int | float, y: int | float, action_type: str = "move", seconds: float = 0.0
    ) -> bool:
        """
        统一的鼠标动作方法

        Args:
            hwnd: 窗口句柄
            x: x坐标
            y: y坐标
            action_type: 动作类型
                - "move": 仅移动鼠标
                - "tap": 点击
                - "down": 按下左键
                - "up": 松开左键
                - "drag": 拖拽（需要保持左键按下状态移动）
            seconds: 延迟时间
        """
        try:
            x = int(x)
            y = int(y)
            l_param = win32api.MAKELONG(x, y)

            if action_type == "move":
                # 普通移动
                win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, 0, l_param)

            elif action_type == "tap":
                # 点击
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)
                cls.__sleep(0.05)
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)

            elif action_type == "down":
                # 按下左键
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param)

            elif action_type == "up":
                # 松开左键
                win32gui.PostMessage(hwnd, win32con.WM_LBUTTONUP, 0, l_param)

            elif action_type == "drag":
                # 拖拽（移动时保持左键按下）
                win32gui.SendMessage(hwnd, win32con.WM_MOUSEMOVE, win32con.MK_LBUTTON, l_param)

            cls.__sleep(seconds)
            return True

        except Exception as e:
            print(f"鼠标动作失败 ({action_type}): {e}")
            return False

    @classmethod
    def scroll_mouse(
        self, hwnd, count: int, x: int | float = 0, y: int | float = 0, seconds: float = 0.0
    ):
        """
        鼠标滚轮滚动

        :param seconds:
        :param hwnd: 目标窗口句柄
        :param count: 一次滚动多少个单位（正数=向上滚，负数=向下滚）
        :param x: 鼠标 X 坐标
        :param y: 鼠标 Y 坐标
        """
        w_param = win32api.MAKELONG(0, win32con.WHEEL_DELTA * count)
        l_param = win32api.MAKELONG(x, y)  # 鼠标位置，相对于窗口
        win32gui.PostMessage(hwnd, win32con.WM_MOUSEWHEEL, w_param, l_param)
        self.__sleep(seconds)

    ###### Other ######

    @classmethod
    def window_activate(self, hwnd, seconds: float = 0.0):
        win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
        self.__sleep(seconds)

    @classmethod
    def __sleep(self, seconds: float):
        if seconds == 0.0:
            return
        if seconds > 0.0:
            time.sleep(seconds)
        else:  # < 0.0
            seconds = round(random.uniform(0.04, 0.06), 4)
            time.sleep(seconds)

    @classmethod
    def tap_esc(self, hwnd):
        self.tap_key(hwnd, win32con.VK_ESCAPE)

    @classmethod
    def tap_space(self, hwnd):
        self.tap_key(hwnd, win32con.VK_SPACE)

    @classmethod
    def tap_enter(self, hwnd):
        self.tap_key(hwnd, win32con.VK_RETURN)

    @classmethod
    def get_key_state(self, vk_code):
        return win32api.GetAsyncKeyState(vk_code) < 0

    @classmethod
    def get_mouse_position(self):
        x, y = win32api.GetCursorPos()
        return x, y

    @classmethod
    def set_mouse_position(self, hwnd, x: int, y: int):
        win32api.SetCursorPos((x, y))

    @classmethod
    def input_char(self, hwnd, char, seconds: float = 0.0):
        """发送文本，一次一个字符"""
        win32gui.PostMessage(hwnd, win32con.WM_CHAR, ord(char), 0)
        self.__sleep(seconds)

    @classmethod
    def input_text(self, hwnd, text: str, seconds: float = 0.0):
        """发送文本，字符串"""
        if len(text) == 0:
            return
        for char in text:
            self.input_char(hwnd, char, 0.03)
        self.__sleep(seconds)