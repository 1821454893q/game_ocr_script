import ctypes
import re
import time
from ctypes import windll
from typing import List, Tuple, Optional,Callable
from pathlib import Path

import psutil
import win32api
import win32con
import win32gui
import win32process
from dataclasses import dataclass, field

from gas.logger import get_logger

logger = get_logger()

# wuwa相关进程
CLIENT_WIN64_SHIPPING_EXE = "EMLauncher-Win64-Shipping.exe"  # 登录客户端
WUTHERING_WAVES_EXE = "EM-Win64-Shipping.exe"  # 游戏主程序
LAUNCHER_EXE = "EMLauncher.exe"  # 启动器

# wuwa窗口相关属性
WUWA_HWND_CLASS_NAME = "UnrealWindow"
WUWA_HWND_TITLE = ["二重螺旋  ", "Wuthering Waves  "]
# 国服登录窗口
OFFICIAL_LOGIN_HWND_CLASS_NAME = "#32770"
OFFICIAL_LOGIN_HWND_TITLE = ""
# b服登录窗口
BILIBILI_LOGIN_HWND_CLASS_NAME = "CLoginDlg_P_8340_\\d{10}"  # CLoginDlg_P_8340_1720374432
BILIBILI_LOGIN_HWND_TITLE = "bilibili游戏 登录_弹框"
# UE4-Client崩溃窗口
UE4_CLIENT_HWND_CLASS_NAME = "#32770"
UE4_CLIENT_HWND_TITLE = "UE4-Client Game已崩溃，即将关闭"

# dpi
STANDARD_DPI = 96  # 96 是标准 DPI

@dataclass
class WindowInfo:
    """窗口信息结构体"""
    hwnd: int
    title: str
    position: Tuple[int, int]
    size: Tuple[int, int]
    class_name: str
    is_child: bool = False
    parent: Optional['WindowInfo'] = None
    is_visible: bool = False
    style: int = 0
    children: List['WindowInfo'] = field(default_factory=list)

    def __repr__(self):
        return f"WindowInfo(hwnd={self.hwnd}, title='{self.title}', class_name='{self.class_name}')"


# 获取当前系统所有窗口句柄
def list_all_windows() -> List[WindowInfo]:
    """列出所有窗口（包括系统窗口和隐藏窗口），按树形结构返回"""
    try:
        windows_dict = {}  # 用于快速查找窗口
        windows_list = []  # 最终返回的列表
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

                # 检查窗口是否可见
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

                # 创建窗口信息结构体
                window_info = WindowInfo(
                    hwnd=hwnd,
                    title=title,
                    position=(rect[0], rect[1]),
                    size=(width, height),
                    class_name=class_name,
                    is_child=False,  # 初始值，后续会修正
                    parent=None,  # 初始化为None，后续会设置
                    is_visible=is_visible,
                    style=style,
                    children=[]  # 子窗口列表
                )

                # 存储到字典和列表
                windows_dict[hwnd] = window_info
                windows_list.append(window_info)

                # 递归枚举子窗口
                def enum_child_proc(child_hwnd, _):
                    _process_window(child_hwnd, is_child=True, parent_hwnd=hwnd)
                    return True

                win32gui.EnumChildWindows(hwnd, enum_child_proc, None)

            except Exception as e:
                print(f"处理窗口 {hwnd} 时出错: {e}")

        # 枚举所有窗口（包括不可见的）
        def enum_all_windows_proc(hwnd, _):
            _process_window(hwnd, is_child=False)
            return True

        win32gui.EnumWindows(enum_all_windows_proc, None)

        # 构建窗口树形结构
        _build_window_tree(windows_dict, windows_list)

        print(f"找到 {len(windows_list)} 个窗口（包含所有类型）")

        return windows_list

    except Exception as e:
        print(f"枚举窗口失败: {e}")
        return []


def _build_window_tree(windows_dict: dict, windows_list: List[WindowInfo]):
    """构建窗口的树形结构"""
    # 建立父子关系
    for window in windows_list:
        parent_hwnd = win32gui.GetParent(window.hwnd)
        if parent_hwnd and parent_hwnd in windows_dict:
            parent_window = windows_dict[parent_hwnd]
            window.parent = parent_window
            window.is_child = True
            parent_window.children.append(window)
    
    # 清理根窗口的parent引用（确保根窗口的parent为None）
    for window in windows_list:
        if not window.is_child:
            window.parent = None


def find_in_children(windows: List[WindowInfo], call: Callable[[WindowInfo],bool]) -> Optional[WindowInfo]:
    """在子窗口中递归查找满足条件的窗口"""
    for window in windows:
        if call(window):
            return window
        result = find_in_children(window.children, call)
        if result:
            return result
    return None

def get_pid_by_exe_name(exe_name: str):
    for proc in psutil.process_iter(["name", "pid"]):
        if proc.info["name"] == exe_name:
            pro_pid = proc.info["pid"]
            # print(f"pid: {pro_pid}")
            return pro_pid
    return None

def get_hwnd_by_exe_name(exe_name: str) -> list | None:
    ge_pid = get_pid_by_exe_name(exe_name)
    if ge_pid is None:
        return None
    windows_list = list_all_windows()
    rt_hwnd_list: list = []
    for windows in windows_list:
        _, found_pid = win32process.GetWindowThreadProcessId(windows.hwnd)
        if found_pid == ge_pid:
            rt_hwnd_list.append(windows.hwnd)
            
    return rt_hwnd_list


def get_exe_path_from_hwnd(hwnd: int) -> str | None:
    # 获取进程 ID
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid = pid.value

    # 通过 psutil 获取进程路径
    try:
        proc = psutil.Process(pid)
        return proc.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def _find_all_windows(class_name=None, titles=None):
    result = []

    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            if (class_name is None or win32gui.GetClassName(hwnd) == class_name) and (
                not titles or win32gui.GetWindowText(hwnd) in titles
            ):
                result.append(hwnd)

    win32gui.EnumWindows(callback, None)
    return result


def get_hwnd_by_class_and_title(class_name: str, titles: list[str] | str) -> list:
    if isinstance(titles, str):
        titles = [titles]
    windows = []
    logger.debug("window class: %s, title: %s", class_name, titles)
    # window = win32gui.FindWindow(class_name, title)  # 只会返回一个
    find_windows = _find_all_windows(class_name, titles)
    logger.debug("windows: %s", find_windows)
    windows.extend(find_windows)
    return windows


def get_hwnds() -> list:
    return get_hwnd_by_class_and_title(WUWA_HWND_CLASS_NAME, WUWA_HWND_TITLE)


def get_hwnd(filter_path: str | None = None, force: bool = False) -> int | None:
    """
    获取游戏窗口句柄
    :param filter_path: 指定游戏路径，用于多窗口时选出指定的窗口
    :param force: 默认False宽松模式，没有匹配到就返回随机第一个；为True 则强制窗口路径必须为指定路径的程序，否则返回None
    :return:
    """
    if filter_path is not None:
        logger.debug(f"get_hwnd入参: {filter_path}")
    hwnds = get_hwnds()
    if not hwnds:
        return None
    # 同时有多个游戏进程在运行时
    if filter_path:  # 找出指定的那个
        hwnd = filter_hwnds(hwnds, filter_path)
        if hwnd:
            return hwnd
        elif force:
            return None
    return hwnds[0]  # 默认返回找到的第一个窗口


def filter_hwnds(hwnds: list, filter_path: str):
    filter_wwg_path = get_wwg_path(filter_path)
    if not filter_wwg_path:
        return None
    for hwnd in hwnds:
        exe_path: str = get_exe_path_from_hwnd(hwnd)
        wwg_path = get_wwg_path(exe_path)
        if not wwg_path:
            continue
        # logger.info("filter_wwg_path: %s", filter_wwg_path)
        # logger.info("wwg_path       : %s", wwg_path)
        # logger.info(wwg_path.resolve() == filter_wwg_path.resolve())
        if wwg_path.resolve() == filter_wwg_path.resolve():
            return hwnd
    return None


def get_wwg_path(path_str: str) -> Path | None:
    """获取Wuthering Waves Game目录绝对路径"""
    if not path_str:
        return None
    try:
        # 兼容Wuthering Waves.exe 和 Client-Win64-Shipping.exe
        if path_str.endswith(WUTHERING_WAVES_EXE):
            return Path(path_str).parent
        if path_str.endswith(CLIENT_WIN64_SHIPPING_EXE):
            return Path(path_str).parent.parent.parent.parent
    except Exception:
        return None


def get_ww_exe_path(path_str: str) -> str:
    ww_exe_path = get_wwg_path(path_str)
    return str(ww_exe_path.joinpath(WUTHERING_WAVES_EXE).resolve())


def get_child_hwnds(hwnd):
    child_hwnds = []
    win32gui.EnumChildWindows(hwnd, lambda c_hwnd, _: child_hwnds.append(c_hwnd), None)
    return child_hwnds


# 官服 获取账号登录界面窗口句柄 by wakening
def get_login_hwnd_official() -> list | None:
    # 只返回可见窗口
    wd_hwnd_list = get_hwnd_by_exe_name(CLIENT_WIN64_SHIPPING_EXE)
    if wd_hwnd_list is None or len(wd_hwnd_list) == 0:
        return None
    login_hwnd_list = []
    for wd_hwnd in wd_hwnd_list:
        if (
            win32gui.IsWindow(wd_hwnd)
            and win32gui.IsWindowEnabled(wd_hwnd)
            and win32gui.IsWindowVisible(wd_hwnd)
        ):
            window_class = win32gui.GetClassName(wd_hwnd)
            # logger.debug(f"window: {wd_hwnd}, window class: {window_class}, title: {win32gui.GetWindowText(wd_hwnd)}")
            # window class: UnrealWindow, title: 鸣潮
            # window class: #32770, title:
            # 目前游戏v1.1版本有游戏本体窗口，账号登录窗口等
            # 账号登录窗口没有标题，类名#32770不确定是否会变，无法准确定位
            # 考虑到后续窗口可能变多，返回数组 by wakening
            if window_class != WUWA_HWND_CLASS_NAME:
                login_hwnd_list.append(wd_hwnd)
    return login_hwnd_list

# 强制关闭进程
# noinspection PyUnresolvedReferences
def force_close_process(hwnd):
    # 卡死时发送窗口消息无效
    # win32gui.SendMessage(hwnd, win32con.WM_CLOSE, 0, 0)
    # 根据窗口句柄获取进程ID
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    # 获取进程句柄
    handle = win32api.OpenProcess(win32con.PROCESS_TERMINATE, 0, pid)
    win32api.TerminateProcess(handle, -1)
    win32api.CloseHandle(handle)


def window_activate(hwnd):
    win32gui.PostMessage(hwnd, win32con.WM_ACTIVATE, win32con.WA_ACTIVE, 0)
    time.sleep(0.05)


PROCESS_DPI_UNAWARE = 0
PROCESS_SYSTEM_DPI_AWARE = 1
PROCESS_PER_MONITOR_DPI_AWARE = 2


def enable_dpi_awareness():
    """
    启用全局DPI感知，支持每显示器DPI感知
    """
    logger.debug("Enable global DPI awareness")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
    except Exception:
        logger.exception("Failed to enable DPI awareness")


# 窗口的大小和位置在不同的缩放设置下可能会分为“实际大小”和“逻辑大小”：
#
# 实际大小（Physical Size）：
# 实际大小是根据显示器的物理像素来度量的尺寸。它考虑了系统的 DPI 设置（例如 100%, 150%, 200% 等）。在缩放较高的情况下，实际大小会相应变大，以适应更高的像素密度。
# 逻辑大小（Logical Size）：
#
# 逻辑大小是应用程序内部使用的坐标系统，通常不受 DPI 缩放影响。它是按照设计时的标准像素（通常是 96 DPI）来计算的，不考虑显示器的缩放因子。
# 在高 DPI 设置下，应用程序会将逻辑像素映射到实际的物理像素上。因此，逻辑像素看起来会更小，实际物理像素则会更大。
# 获取窗口物理矩形
def get_window_rect(hwnd) -> tuple[int, int, int, int]:
    """获取特定窗口的绝对坐标，左上右下，（包括标题栏、边框等非客户区"""
    return win32gui.GetWindowRect(hwnd)


def get_client_rect(hwnd) -> tuple[int, int, int, int]:
    """获取特定窗口客户区的相对坐标，即内容区域（如编辑框、绘图区等），不包含非客户区（标题栏、边框等）"""
    return win32gui.GetClientRect(hwnd)


def get_window_wh(hwnd) -> (int, int):
    """获取特定窗口的宽高px"""
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    logger.debug("window rect: (%s, %s, %s, %s)", left, top, right, bot)
    width = right - left
    height = bot - top
    logger.debug("window w, h: %d, %d", width, height)
    return width, height


def get_client_wh(hwnd):
    """获取特定窗口客户区的宽高px"""
    left, top, right, bot = win32gui.GetClientRect(hwnd)
    logger.debug("client rect: (%s, %s, %s, %s)", left, top, right, bot)
    width = right - left
    height = bot - top
    logger.debug("client w, h: %d, %d", width, height)
    return width, height


def get_screen_wh():
    """电脑屏幕的宽高px（分辨率）"""
    # noinspection PyUnresolvedReferences
    width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    # noinspection PyUnresolvedReferences
    height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
    logger.debug("screen w, h: %d, %d", width, height)
    return width, height


def get_client_rect_on_screen(hwnd) -> tuple[int, int, int, int]:
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    # 将客户区左上角 (0, 0) 转换为屏幕坐标
    client_point = win32gui.ClientToScreen(hwnd, (0, 0))
    client_left, client_top = client_point
    # 计算客户区右下的屏幕坐标
    client_right = client_point[0] + (right - left)
    client_bottom = client_point[1] + (bottom - top)
    return client_left, client_top, client_right, client_bottom


def get_focus_rect_on_screen(
    hwnd, region: tuple[float, float, float, float] | None = None
) -> tuple[int, int, int, int]:
    """获取窗口 相对区域 的 绝对屏幕坐标"""
    client_rect_on_screen = get_client_rect_on_screen(hwnd)
    if region is None:
        return client_rect_on_screen
    w = client_rect_on_screen[2] - client_rect_on_screen[0]
    h = client_rect_on_screen[3] - client_rect_on_screen[1]
    return (
        int(client_rect_on_screen[0] + w * region[0]),
        int(client_rect_on_screen[1] + h * region[1]),
        int(client_rect_on_screen[0] + w * region[2]),
        int(client_rect_on_screen[1] + h * region[3]),
    )


def get_sys_dpi():
    dpi = windll.user32.GetDpiForSystem()
    logger.debug(f"System DPI: {dpi}")
    return dpi


def get_window_dpi(hwnd):
    dpi = windll.user32.GetDpiForWindow(hwnd)
    logger.debug(f"Window DPI: {dpi}")
    return dpi


def set_hwnd_left_top(hwnd=None):
    logger.debug("将窗口移动至左上角")
    if hwnd is None:
        hwnd = get_hwnd()
    win32gui.SetWindowPos(
        hwnd, 0, 0, 0, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW
    )


def set_hwnd_center(hwnd=None):
    logger.debug("将窗口居中")
    if hwnd is None:
        hwnd = get_hwnd()
    # 获取屏幕工作区的宽度和高度（排除任务栏）
    # noinspection PyUnresolvedReferences
    screen_rect = win32api.GetMonitorInfo(win32api.EnumDisplayMonitors()[0][0])["Work"]
    work_width = screen_rect[2] - screen_rect[0]  # 工作区宽度
    work_height = screen_rect[3] - screen_rect[1]  # 工作区高度

    # 获取窗口的宽度和高度
    window_rect = win32gui.GetWindowRect(hwnd)  # 获取窗口的矩形框
    window_width = window_rect[2] - window_rect[0]  # 右边界 - 左边界 = 宽度
    window_height = window_rect[3] - window_rect[1]  # 下边界 - 上边界 = 高度

    # 计算窗口的新位置，使其居中（在工作区范围内）
    x = (work_width - window_width) // 2 + screen_rect[0]
    y = (work_height - window_height) // 2 + screen_rect[1]

    # 设置窗口位置（保持原来的大小，不改变层级，显示窗口）
    win32gui.SetWindowPos(
        hwnd, 0, x, y, 0, 0, win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_SHOWWINDOW
    )


def is_foreground_window(hwnd):
    """判断窗口是否为前台窗口"""
    if hwnd is None:
        return False
    # 获取当前前台窗口的句柄
    foreground_hwnd = win32gui.GetForegroundWindow()
    # 判断目标窗口句柄是否与前台窗口句柄相同
    return hwnd == foreground_hwnd
