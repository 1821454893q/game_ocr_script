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

from gas.logger import get_logger

logger = get_logger()

# 使用 PrintWindow 前置条件
windll.user32.SetProcessDPIAware()


class WinProvider(IDeviceProvider):
    """Windows窗口管理工具 - 包含截图和后台操作"""

    def __init__(self, window_title: str = None, class_name: str = None, capture_mode: int = 1):
        self.window_title = window_title
        self.class_name = class_name
        self._hwnd = None
        self._window = None
        self._capture_mode = capture_mode

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

    def capture(self) -> Optional[np.ndarray]:
        """截图当前窗口"""
        if not self._hwnd:
            logger.error("未设置目标窗口，请先调用 set_window()")
            return None

        try:
            if self._capture_mode == 1:
                screenshot = self.capture_bitblt(self._hwnd)
            elif self._capture_mode == 2:
                screenshot = self.capture_print_window(self._hwnd)

            if screenshot is not None:
                logger.debug(f"截图成功，尺寸: {screenshot.shape}")
            else:
                logger.error("截图失败")

            return screenshot

        except Exception as e:
            logger.error(f"截图异常: {e}")
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
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
            except:
                pass

    def capture_print_window(self, hwnd) -> Optional[np.ndarray]:
        """使用PrintWindow进行截图"""
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

            # 使用PrintWindow拷贝屏幕内容
            windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 3)

            # 获取位图数据
            bmpstr = saveBitMap.GetBitmapBits(True)

            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype="uint8")
            img.shape = (height, width, 4)  # BGRA格式

            # 转换为BGR（OpenCV格式）
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            logger.debug(f"PrintWindow截图成功: {width}x{height}")
            return img_bgr

        except Exception as e:
            logger.error(f"PrintWindow截图失败: {e}")
            return None
        finally:
            # 清理资源
            try:
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
            except Exception as e:
                logger.error(e)
                pass

    # ==================== 后台鼠标操作 ====================
    def move_mouse(self, x: int, y: int) -> bool:
        """移动鼠标"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False

        try:
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
        if action == "tap":
            logger.debug(f"鼠标点击 ({x},{y})")
            return KeyMouseUtil.click(self._hwnd, x, y) is None

        if action == "down":
            return KeyMouseUtil.mouse_left_down(self._hwnd, x, y) is None

        if action == "up":
            return KeyMouseUtil.mouse_left_up(self._hwnd, x, y) is None

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, is_drga: bool = True, duration: float = 0.5
    ) -> bool:
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

    def input_text(self, text: str) -> bool:
        """输入文本"""
        pass

    def is_available(self) -> bool:
        return True

    def get_info(self) -> dict:
        """获取设备信息"""
        pass

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
