# src/window_capture.py
import pygetwindow as gw
import win32gui
import win32ui
import win32con
import win32api
import ctypes
from ctypes import wintypes
from typing import Optional, Tuple, List, Union
import cv2
import numpy as np
import time

from ocr_tool.interfaces import IDeviceProvider
from ocr_tool.key_code import KeyCode, get_windows_keycode

from ..logger import get_logger

logger = get_logger()


class WinProvider(IDeviceProvider):
    """Windows窗口管理工具 - 包含截图和后台操作"""

    def __init__(self, window_title: str = None, class_name: str = None):
        self.window_title = window_title
        self.class_name = class_name
        self._hwnd = None
        self._window = None

        if window_title:
            self._find_and_set_hwnd(window_title, class_name)

    def _find_and_set_hwnd(self, window_title: str, class_name: str) -> bool:
        """查找并设置目标窗口"""
        try:
            windows = []

            def enum_proc(hwnd, extra):
                # 处理子窗口
                _process_window(hwnd)
                return True

            def _process_window(hwnd):
                """处理单个窗口的通用逻辑"""
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    # 放宽条件，即使标题为空也记录（很多子窗口没有标题）
                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        # 获取窗口类名，便于区分不同类型的窗口
                        cn = win32gui.GetClassName(hwnd)

                        # 判断是否为子窗口
                        parent_hwnd = win32gui.GetParent(hwnd)
                        is_child = parent_hwnd != 0

                        if title == window_title:
                            if class_name == "":
                                windows.append(
                                    {
                                        "hwnd": hwnd,
                                        "title": title,
                                        "position": (rect[0], rect[1]),
                                        "size": (rect[2] - rect[0], rect[3] - rect[1]),
                                        "class_name": cn,
                                        "is_child": is_child,
                                        "parent_hwnd": parent_hwnd if is_child else None,
                                    }
                                )
                            elif class_name == cn:
                                windows.append(
                                    {
                                        "hwnd": hwnd,
                                        "title": title,
                                        "position": (rect[0], rect[1]),
                                        "size": (rect[2] - rect[0], rect[3] - rect[1]),
                                        "class_name": cn,
                                        "is_child": is_child,
                                        "parent_hwnd": parent_hwnd if is_child else None,
                                    }
                                )

                        # 如果当前窗口有子窗口，递归枚举所有子窗口
                        if not is_child:  # 只从顶级窗口开始枚举子窗口，避免重复
                            win32gui.EnumChildWindows(hwnd, enum_proc, None)

                    except Exception as e:
                        logger.debug(f"处理窗口 {hwnd} 时出错: {e}")

            win32gui.EnumWindows(enum_proc, None)

            if len(windows) == 0:
                logger.error(f"❎ 查未找到窗口: {window_title} 类名：{class_name}")
                return False

            self._hwnd = windows[0]["hwnd"]
            self.window_title = windows[0]["title"]
            self.class_name = windows[0]["class_name"]

            logger.info(
                f"✅ 找到窗口 数量:{len(windows)} 标题: {self.window_title} 类名：{self.class_name} (HWND: {self._hwnd})"
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
        if not self._window:
            return None

        try:
            info = {
                "title": self._window.title,
                "hwnd": self._hwnd,
                "position": (self._window.left, self._window.top),
                "size": (self._window.width, self._window.height),
                "is_minimized": self._window.isMinimized,
                "is_maximized": self._window.isMaximized,
            }
            return info
        except Exception as e:
            logger.error(f"获取窗口信息失败: {e}")
            return None

    def activate_window(self) -> bool:
        """激活窗口（前置）"""
        if not self._window:
            logger.error("未设置目标窗口")
            return False

        try:
            if self._window.isMinimized:
                self._window.restore()

            self._window.activate()
            logger.debug("窗口已激活")
            return True

        except Exception as e:
            logger.error(f"激活窗口失败: {e}")
            return False

    def move_window(self, x: int, y: int) -> bool:
        """移动窗口"""
        if not self._window:
            logger.error("未设置目标窗口")
            return False

        try:
            self._window.moveTo(x, y)
            logger.debug(f"窗口已移动到: ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"移动窗口失败: {e}")
            return False

    def resize_window(self, width: int, height: int) -> bool:
        """调整窗口大小"""
        if not self._window:
            logger.error("未设置目标窗口")
            return False

        try:
            self._window.resizeTo(width, height)
            logger.debug(f"窗口大小已调整为: {width}x{height}")
            return True

        except Exception as e:
            logger.error(f"调整窗口大小失败: {e}")
            return False

    # ==================== 截图功能 ====================

    def capture(self) -> Optional[np.ndarray]:
        """截图当前窗口"""
        if not self._hwnd:
            logger.error("未设置目标窗口，请先调用 set_window()")
            return None

        try:
            screenshot = self.capture_bitblt(self._hwnd)
            if screenshot is not None:
                logger.debug(f"截图成功，尺寸: {screenshot.shape}")
            else:
                logger.error("截图失败")

            return screenshot

        except Exception as e:
            logger.error(f"截图异常: {e}")
            return None

    def capture_with_printwindow(self) -> Optional[np.ndarray]:
        """使用PrintWindow截图（更好的兼容性）"""
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return None

        try:
            # 获取窗口尺寸
            left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)
            width = right - left
            height = bottom - top

            # 获取窗口DC
            window_dc = win32gui.GetWindowDC(self.hwnd)
            if not window_dc:
                return None

            try:
                # 创建兼容DC
                dc_obj = win32ui.CreateDCFromHandle(window_dc)
                compatible_dc = dc_obj.CreateCompatibleDC()

                # 创建位图
                bitmap = win32ui.CreateBitmap()
                bitmap.CreateCompatibleBitmap(dc_obj, width, height)
                compatible_dc.SelectObject(bitmap)

                # 使用PrintWindow（关键区别）
                # PW_RENDERFULLCONTENT = 0x00000002 (Windows 8+)
                result = win32gui.PrintWindow(self.hwnd, compatible_dc.GetSafeHdc(), 0)
                # 或者尝试: result = win32gui.PrintWindow(self.hwnd, compatible_dc.GetSafeHdc(), 2)

                if not result:
                    print("PrintWindow失败，回退到BitBlt")
                    compatible_dc.BitBlt((0, 0), (width, height), dc_obj, (0, 0), win32con.SRCCOPY)

                # 转换为numpy数组
                bitmap_bits = bitmap.GetBitmapBits(True)
                img = np.frombuffer(bitmap_bits, dtype=np.uint8)
                img.shape = (height, width, 4)

                # 转换为BGR
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                return img_bgr

            finally:
                win32gui.ReleaseDC(self.hwnd, window_dc)

        except Exception as e:
            print(f"PrintWindow截图失败: {e}")
            return None

    def capture_bitblt(self, hwnd) -> Optional[np.ndarray]:
        """使用BitBlt进行截图（主要方法）"""
        try:
            # 获取窗口矩形（包括边框和标题栏）
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                logger.error("窗口大小无效")
                return None

            # 创建设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # 使用BitBlt拷贝屏幕内容
            result = saveDC.BitBlt(
                (0, 0),  # 目标位置
                (width, height),  # 大小
                mfcDC,  # 源设备上下文
                (0, 0),  # 源位置
                win32con.SRCCOPY,  # 操作类型
            )

            # 如果BitBlt成功（返回None表示成功）
            if result is None:
                # 获取位图数据
                bmpstr = saveBitMap.GetBitmapBits(True)

                # 转换为numpy数组
                img = np.frombuffer(bmpstr, dtype="uint8")
                img.shape = (height, width, 4)  # BGRA格式

                # 转换为BGR（OpenCV格式）
                img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

                logger.debug(f"BitBlt截图成功: {width}x{height}")
                return img_bgr
            else:
                logger.warning("BitBlt操作失败")
                return None

        except Exception as e:
            logger.error(f"BitBlt截图失败: {e}")
            return None
        finally:
            # 清理资源
            try:
                if "saveBitMap" in locals():
                    win32gui.DeleteObject(saveBitMap.GetHandle())
                if "saveDC" in locals():
                    saveDC.DeleteDC()
                if "mfcDC" in locals():
                    mfcDC.DeleteDC()
                if "hwndDC" in locals():
                    win32gui.ReleaseDC(hwnd, hwndDC)
            except:
                pass

    # ==================== 后台鼠标操作 ====================

    def _screen_to_client(self, screen_x: int, screen_y: int) -> Tuple[int, int]:
        """屏幕坐标转换为窗口客户区坐标"""
        if not self._hwnd:
            return screen_x, screen_y

        try:
            # 获取窗口位置
            window_rect = win32gui.GetWindowRect(self._hwnd)
            client_rect = win32gui.GetClientRect(self._hwnd)

            # 计算边框和标题栏大小
            border_width = (window_rect[2] - window_rect[0] - client_rect[2]) // 2
            title_bar_height = window_rect[3] - window_rect[1] - client_rect[3] - border_width * 2

            # 转换为客户区坐标
            client_x = screen_x - window_rect[0] - border_width
            client_y = screen_y - window_rect[1] - title_bar_height - border_width

            return client_x, client_y

        except Exception as e:
            logger.error(f"坐标转换失败: {e}")
            return screen_x, screen_y

    def click_background(
        self, x: int, y: int, button: str = "left", double_click: bool = False
    ) -> bool:
        """后台点击（窗口不需要激活）"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:

            # 准备消息参数
            lParam = win32api.MAKELONG(x, y)

            if button.lower() == "left":
                down_msg = win32con.WM_LBUTTONDOWN
                up_msg = win32con.WM_LBUTTONUP
                dbl_msg = win32con.WM_LBUTTONDBLCLK
            elif button.lower() == "right":
                down_msg = win32con.WM_RBUTTONDOWN
                up_msg = win32con.WM_RBUTTONUP
                dbl_msg = win32con.WM_RBUTTONDBLCLK
            elif button.lower() == "middle":
                down_msg = win32con.WM_MBUTTONDOWN
                up_msg = win32con.WM_MBUTTONUP
                dbl_msg = None
            else:
                logger.error(f"不支持的按钮类型: {button}")
                return False

            # 使用 PostMessage 而不是 SendMessage（避免激活窗口）
            if double_click and dbl_msg:
                # 双击：直接发送双击消息
                win32gui.PostMessage(self._hwnd, down_msg, 0, lParam)
                win32gui.PostMessage(self._hwnd, up_msg, 0, lParam)
            else:
                # 单击：按下和释放
                win32gui.SendMessage(self._hwnd, down_msg, 0, lParam)
                time.sleep(0.05)
                win32gui.SendMessage(self._hwnd, up_msg, 0, lParam)

            logger.debug(f"后台点击: ({x}, {y}), 按钮: {button}, 双击: {double_click}")
            return True

        except Exception as e:
            logger.error(f"后台点击失败: {e}")
            return False

    def click_relative(
        self, rel_x: int, rel_y: int, button: str = "left", double_click: bool = False
    ) -> bool:
        """相对窗口位置的点击"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
            # 获取窗口位置
            window_rect = win32gui.GetWindowRect(self._hwnd)

            # 计算绝对坐标
            abs_x = window_rect[0] + rel_x
            abs_y = window_rect[1] + rel_y

            return self.click_background(abs_x, abs_y, button, double_click)

        except Exception as e:
            logger.error(f"相对点击失败: {e}")
            return False

    def move_mouse_background(self, x: int, y: int) -> bool:
        """后台移动鼠标"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
            client_x, client_y = self._screen_to_client(x, y)
            lParam = win32api.MAKELONG(client_x, client_y)

            win32gui.SendMessage(self._hwnd, win32con.WM_MOUSEMOVE, 0, lParam)
            logger.debug(f"后台移动鼠标到: ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"后台移动鼠标失败: {e}")
            return False

    def send_key_background(self, virtual_key: int, key_down: bool = True) -> bool:
        """后台发送按键"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
            if key_down:
                message = win32con.WM_KEYDOWN
            else:
                message = win32con.WM_KEYUP

            win32gui.SendMessage(self._hwnd, message, virtual_key, 0)
            logger.debug(f"后台发送按键: {virtual_key}, 按下: {key_down}")
            return True

        except Exception as e:
            logger.error(f"后台发送按键失败: {e}")
            return False

    def send_text_background(self, text: str) -> bool:
        """后台发送文本"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
            for char in text:
                win32gui.SendMessage(self._hwnd, win32con.WM_CHAR, ord(char), 0)
                time.sleep(0.01)  # 短暂延迟

            logger.debug(f"后台发送文本: {text}")
            return True

        except Exception as e:
            logger.error(f"后台发送文本失败: {e}")
            return False

    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        """发送按键事件 - 自动转换为Windows键码"""
        try:
            if not self.is_available():
                return False

            # 激活窗口
            self.activate_window()

            # 转换为Windows键码
            win_keycode = get_windows_keycode(keycode)
            key_name = keycode.name
            if win_keycode == 0:
                logger.error(f"未知的按键代码: {key_name}")
                return False

            if action == "tap" or action == "press":
                # 按下并释放
                win32api.keybd_event(win_keycode, 0, 0, 0)
                win32api.Sleep(50)
                win32api.keybd_event(win_keycode, 0, win32con.KEYEVENTF_KEYUP, 0)

            elif action == "down":
                # 按下
                win32api.keybd_event(win_keycode, 0, 0, 0)

            elif action == "up":
                # 释放
                win32api.keybd_event(win_keycode, 0, win32con.KEYEVENTF_KEYUP, 0)

            else:
                logger.error(f"不支持的按键动作: {action}")
                return False

            logger.debug(f"窗口按键: {action} {key_name}(win:{win_keycode})")
            return True

        except Exception as e:
            logger.error(f"窗口按键异常: {e}")
            return False

    # ==================== 窗口查找功能 ====================

    def list_all_windows(self) -> List[dict]:
        """列出所有窗口（包括系统窗口和隐藏窗口）"""
        try:
            windows = []
            processed_hwnds = set()

            def _process_window(hwnd, is_child=False, parent_hwnd=None):
                if hwnd in processed_hwnds:
                    return
                processed_hwnds.add(hwnd)

                try:
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)

                    # 获取窗口样式
                    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

                    # 检查窗口是否可见（可选，根据需求调整）
                    is_visible = win32gui.IsWindowVisible(hwnd)

                    # 过滤条件可以更宽松
                    if not title and not class_name:
                        return

                    try:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]

                        # 更宽松的尺寸过滤
                        if width <= 0 or height <= 0 or width > 10000 or height > 10000:
                            return

                    except:
                        # 如果无法获取位置信息，使用默认值
                        rect = (0, 0, 0, 0)
                        width = 0
                        height = 0

                    if is_child:
                        actual_parent = parent_hwnd
                    else:
                        actual_parent = win32gui.GetParent(hwnd)
                        is_child = actual_parent != 0

                    window_info = {
                        "hwnd": hwnd,
                        "title": title,
                        "position": (rect[0], rect[1]),
                        "size": (width, height),
                        "class_name": class_name,
                        "is_child": is_child,
                        "parent_hwnd": actual_parent if is_child else None,
                        "is_visible": is_visible,
                        "style": style,
                    }

                    windows.append(window_info)

                    # 递归枚举子窗口
                    def enum_child_proc(child_hwnd, _):
                        _process_window(child_hwnd, is_child=True, parent_hwnd=hwnd)
                        return True

                    win32gui.EnumChildWindows(hwnd, enum_child_proc, None)

                except Exception as e:
                    logger.debug(f"处理窗口 {hwnd} 时出错: {e}")

            # 枚举所有窗口（包括不可见的）
            def enum_all_windows_proc(hwnd, _):
                _process_window(hwnd, is_child=False)
                return True

            win32gui.EnumWindows(enum_all_windows_proc, None)

            logger.debug(f"找到 {len(windows)} 个窗口（包含所有类型）")

            # 按窗口层次结构显示
            self._log_window_hierarchy(windows)

            return windows

        except Exception as e:
            logger.error(f"枚举窗口失败: {e}")
            return []

    def _log_window_hierarchy(self, windows):
        """记录窗口层次结构（用于调试）- 递归版本（清晰树形）"""
        # 分离顶级窗口和子窗口
        top_level_windows = [w for w in windows if not w["is_child"]]
        child_windows = [w for w in windows if w["is_child"]]

        logger.debug(f"顶级窗口: {len(top_level_windows)} 个")
        logger.debug(f"子窗口: {len(child_windows)} 个")

        def log_window_tree(window, depth=0, is_last=True):
            """递归记录窗口树"""
            # 构建树形前缀
            prefix = ""
            if depth > 0:
                prefix = "  " * (depth - 1)
                prefix += "└─ " if is_last else "├─ "

            logger.debug(
                f"{prefix}窗口: '{window['title']}' 句柄: {window['hwnd']}, 类名: '{window['class_name']}'"
            )

            # 查找当前窗口的所有直接子窗口
            children = [w for w in child_windows if w["parent_hwnd"] == window["hwnd"]]

            for i, child in enumerate(children):
                log_window_tree(child, depth + 1, i == len(children) - 1)

        # 为每个顶级窗口构建树
        for i, top_win in enumerate(top_level_windows):
            logger.debug(f"窗口树 {i + 1}:")
            log_window_tree(top_win, 0, i == len(top_level_windows) - 1)
            if i < len(top_level_windows) - 1:
                logger.debug("")  # 在顶级窗口之间添加空行

    def find_window_by_process(self, process_name: str) -> Optional[str]:
        """通过进程名查找窗口"""
        try:
            import psutil

            for proc in psutil.process_iter(["name", "pid"]):
                if process_name.lower() in proc.info["name"].lower():
                    try:
                        # 获取该进程的所有窗口
                        windows = gw.getWindowsWithProcessId(proc.info["pid"])
                        if windows:
                            window_title = windows[0].title
                            logger.info(f"通过进程找到窗口: {window_title}")
                            return window_title
                    except Exception:
                        continue

            logger.warning(f"未找到进程 '{process_name}' 的窗口")
            return None

        except ImportError:
            logger.error("请安装psutil: pip install psutil")
            return None
        except Exception as e:
            logger.error(f"通过进程查找窗口失败: {e}")
            return None

    def is_window_exists(self) -> bool:
        """检查窗口是否仍然存在"""
        if not self.window_title:
            return False

        try:
            windows = gw.getWindowsWithTitle(self.window_title)
            return len(windows) > 0
        except:
            return False

    def wait_for_window(self, timeout: int = 30) -> bool:
        """等待窗口出现"""
        logger.info(f"等待窗口出现: {self.window_title}，超时: {timeout}秒")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._find_and_set_hwnd(self.window_title):
                logger.info("窗口已出现")
                return True
            time.sleep(1)

        logger.error(f"等待窗口超时: {self.window_title}")
        return False


# ==================== 快捷函数 ====================


def list_all_windows() -> List[dict]:
    """列出所有窗口的快捷函数"""
    return WinProvider().list_all_windows()


def find_window_by_title(title_contains: str) -> List[dict]:
    """通过标题查找窗口的快捷函数"""
    windows = WinProvider().list_all_windows()
    return [w for w in windows if title_contains.lower() in w["title"].lower()]


def capture_window_by_title(window_title: str) -> Optional[np.ndarray]:
    """通过窗口标题截图的快捷函数"""
    manager = WinProvider(window_title)
    return manager.capture()


def capture_window_by_title_and_classname(
    window_title: str, class_name: str
) -> Optional[np.ndarray]:
    """通过窗口标题截图的快捷函数"""
    manager = WinProvider(window_title)
    return manager.capture()


def click_window_background(window_title: str, x: int, y: int, button: str = "left") -> bool:
    """通过窗口标题后台点击的快捷函数"""
    manager = WinProvider(window_title)
    return manager.click_background(x, y, button)
