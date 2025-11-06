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

from .logger import get_logger

logger = get_logger()

# Windows API 常量
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001

class WindowManager:
    """Windows窗口管理工具 - 包含截图和后台操作"""
    
    def __init__(self, window_title: str = None):
        self.window_title = window_title
        self._hwnd = None
        self._window = None
        
        if window_title:
            self._find_and_set_window(window_title)
    
    def _find_and_set_window(self, window_title: str) -> bool:
        """查找并设置目标窗口"""
        try:
            windows = gw.getWindowsWithTitle(window_title)
            if not windows:
                logger.error(f"未找到窗口: {window_title}")
                return False
            
            self._window = windows[0]
            self._hwnd = self._window._hWnd
            self.window_title = window_title
            
            logger.info(f"✅ 找到窗口: {window_title} (HWND: {self._hwnd})")
            return True
            
        except Exception as e:
            logger.error(f"查找窗口失败: {e}")
            return False
    
    # ==================== 窗口管理功能 ====================
    
    def set_window(self, window_title: str) -> bool:
        """设置目标窗口"""
        return self._find_and_set_window(window_title)
    
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
                "is_maximized": self._window.isMaximized
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
            screenshot = self._capture_win32(self._hwnd)
            if screenshot is not None:
                logger.debug(f"截图成功，尺寸: {screenshot.shape}")
            else:
                logger.error("截图失败")
            
            return screenshot
            
        except Exception as e:
            logger.error(f"截图异常: {e}")
            return None
    
    def _capture_win32(self, hwnd) -> Optional[np.ndarray]:
        """使用Windows API进行后台截图"""
        try:
            # 获取窗口客户区大小
            left, top, right, bottom = win32gui.GetClientRect(hwnd)
            width = right - left
            height = bottom - top
            
            if width <= 0 or height <= 0:
                logger.error("窗口客户区大小无效")
                return None
            
            # 创建设备上下文
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # 创建位图对象
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # 使用PrintWindow进行后台截图
            result = win32gui.PrintWindow(hwnd, saveDC.GetSafeHdc(), 0)
            
            if result == 1:
                logger.debug("PrintWindow截图成功")
            else:
                logger.warning("PrintWindow返回非预期结果")
            
            # 获取位图数据
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 转换为numpy数组
            img = np.frombuffer(bmpstr, dtype='uint8')
            img.shape = (height, width, 4)  # BGRA格式
            
            # 转换为BGR（OpenCV格式）
            img_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            
            # 清理资源
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return img_bgr
            
        except Exception as e:
            logger.error(f"Windows API截图失败: {e}")
            return None
    
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
            title_bar_height = (window_rect[3] - window_rect[1] - client_rect[3] - border_width * 2)
            
            # 转换为客户区坐标
            client_x = screen_x - window_rect[0] - border_width
            client_y = screen_y - window_rect[1] - title_bar_height - border_width
            
            return client_x, client_y
            
        except Exception as e:
            logger.error(f"坐标转换失败: {e}")
            return screen_x, screen_y
    
    def click_background(self, x: int, y: int, button: str = "left", 
                        double_click: bool = False) -> bool:
        """后台点击（窗口不需要激活）"""
        if not self._hwnd:
            logger.error("未设置目标窗口")
            return False
        
        try:
            # 转换为客户区坐标
            client_x, client_y = self._screen_to_client(x, y)
            
            # 准备消息参数
            lParam = win32api.MAKELONG(client_x, client_y)
            
            if button.lower() == "left":
                down_msg = WM_LBUTTONDOWN
                up_msg = WM_LBUTTONUP
            elif button.lower() == "right":
                down_msg = WM_RBUTTONDOWN
                up_msg = WM_RBUTTONUP
            else:
                logger.error(f"不支持的按钮类型: {button}")
                return False
            
            # 发送鼠标消息
            win32gui.SendMessage(self._hwnd, down_msg, MK_LBUTTON, lParam)
            time.sleep(0.05)  # 短暂延迟模拟真实点击
            win32gui.SendMessage(self._hwnd, up_msg, 0, lParam)
            
            # 双击处理
            if double_click:
                time.sleep(0.1)
                win32gui.SendMessage(self._hwnd, down_msg, MK_LBUTTON, lParam)
                time.sleep(0.05)
                win32gui.SendMessage(self._hwnd, up_msg, 0, lParam)
            
            logger.debug(f"后台点击: ({x}, {y}), 按钮: {button}, 双击: {double_click}")
            return True
            
        except Exception as e:
            logger.error(f"后台点击失败: {e}")
            return False
    
    def click_relative(self, rel_x: int, rel_y: int, button: str = "left", 
                      double_click: bool = False) -> bool:
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
            
            win32gui.SendMessage(self._hwnd, WM_MOUSEMOVE, 0, lParam)
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
    
    # ==================== 窗口查找功能 ====================
    
    def list_all_windows(self) -> List[dict]:
        """列出所有可见窗口"""
        try:
            windows = []
            
            def enum_windows_proc(hwnd, extra):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title.strip():
                        try:
                            rect = win32gui.GetWindowRect(hwnd)
                            windows.append({
                                "hwnd": hwnd,
                                "title": title,
                                "position": (rect[0], rect[1]),
                                "size": (rect[2] - rect[0], rect[3] - rect[1])
                            })
                        except:
                            pass
                return True
            
            win32gui.EnumWindows(enum_windows_proc, None)
            
            logger.debug(f"找到 {len(windows)} 个可见窗口")
            return windows
            
        except Exception as e:
            logger.error(f"枚举窗口失败: {e}")
            return []
    
    def find_window_by_process(self, process_name: str) -> Optional[str]:
        """通过进程名查找窗口"""
        try:
            import psutil
            
            for proc in psutil.process_iter(['name', 'pid']):
                if process_name.lower() in proc.info['name'].lower():
                    try:
                        # 获取该进程的所有窗口
                        windows = gw.getWindowsWithProcessId(proc.info['pid'])
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
            if self._find_and_set_window(self.window_title):
                logger.info("窗口已出现")
                return True
            time.sleep(1)
        
        logger.error(f"等待窗口超时: {self.window_title}")
        return False

# ==================== 快捷函数 ====================

def list_all_windows() -> List[dict]:
    """列出所有窗口的快捷函数"""
    return WindowManager().list_all_windows()

def find_window_by_title(title_contains: str) -> List[dict]:
    """通过标题查找窗口的快捷函数"""
    windows = WindowManager().list_all_windows()
    return [w for w in windows if title_contains.lower() in w['title'].lower()]

def capture_window_by_title(window_title: str) -> Optional[np.ndarray]:
    """通过窗口标题截图的快捷函数"""
    manager = WindowManager(window_title)
    return manager.capture()

def click_window_background(window_title: str, x: int, y: int, 
                           button: str = "left") -> bool:
    """通过窗口标题后台点击的快捷函数"""
    manager = WindowManager(window_title)
    return manager.click_background(x, y, button)

# 常用虚拟键码
VK_KEYS = {
    'enter': win32con.VK_RETURN,
    'tab': win32con.VK_TAB,
    'space': win32con.VK_SPACE,
    'escape': win32con.VK_ESCAPE,
    'backspace': win32con.VK_BACK,
    'delete': win32con.VK_DELETE,
    'home': win32con.VK_HOME,
    'end': win32con.VK_END,
    'pageup': win32con.VK_PRIOR,
    'pagedown': win32con.VK_NEXT,
    'left': win32con.VK_LEFT,
    'right': win32con.VK_RIGHT,
    'up': win32con.VK_UP,
    'down': win32con.VK_DOWN,
    'f1': win32con.VK_F1,
    'f2': win32con.VK_F2,
    'f3': win32con.VK_F3,
    'f4': win32con.VK_F4,
    'f5': win32con.VK_F5,
    'f6': win32con.VK_F6,
    'f7': win32con.VK_F7,
    'f8': win32con.VK_F8,
    'f9': win32con.VK_F9,
    'f10': win32con.VK_F10,
    'f11': win32con.VK_F11,
    'f12': win32con.VK_F12,
}