import ctypes
import time

import win32api
import win32con
import win32gui

from gas.util import file_util

from gas.logger import get_logger

logger = get_logger()


# 一些windows系统相关的工具函数，代码少都放到一个模块里

#################### 管理员权限 ####################


def is_admin():
    try:
        # 检查是否有管理员权限
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception as e:
        return False


#################### 系统通知 ####################


class WindowsBalloonTip:
    def __init__(
        self, title, msg, timeout, icon_path, class_name="WWA_NotifyWindow", tooltip_text="WWA"
    ):
        message_map = {
            win32con.WM_DESTROY: self.on_destroy,
        }

        # 创建窗口类
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = class_name
        wc.lpfnWndProc = self.wnd_proc  # 将窗口过程函数绑定到消息处理
        class_atom = win32gui.RegisterClass(wc)

        # 创建窗口
        hwnd = win32gui.CreateWindow(
            wc.lpszClassName,
            "Taskbar",
            0,
            0,
            0,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            0,
            0,
            hinst,
            None,
        )

        # 加载指定的 ico 图标文件
        icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
        try:
            hicon = win32gui.LoadImage(hinst, icon_path, win32con.IMAGE_ICON, 0, 0, icon_flags)
            # logger.info(f"图标加载成功: {icon_path}")
        except Exception as e:
            logger.error(f"加载图标失败: {icon_path}, 错误: {e}")
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)  # 加载默认图标

        # 设置通知的标志
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP | win32gui.NIF_INFO
        nid = (hwnd, 0, flags, win32con.WM_USER + 20, hicon, tooltip_text)  # 图标 + 提示文字
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

        # 发送通知修改
        win32gui.Shell_NotifyIcon(
            win32gui.NIM_MODIFY,
            (hwnd, 0, flags, win32con.WM_USER + 20, hicon, tooltip_text, msg, 200, title),
        )

        time.sleep(timeout)  # 显示通知，设置超时时间

        # 销毁窗口并退出消息循环
        win32gui.DestroyWindow(hwnd)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        """窗口过程处理函数"""
        if msg == win32con.WM_DESTROY:
            self.on_destroy(hwnd, msg, wparam, lparam)
        return 0  # 返回有效的LRESULT，通常为0

    def on_destroy(self, hwnd, msg, wparam, lparam):
        """处理窗口销毁消息"""
        win32gui.PostQuitMessage(0)


def show_windows_notification(msg: str, wait_time: int = 2, title: str = "WWA"):
    """
    显示一个系统通知
    :param msg: 通知的内容
    :param wait_time: 通知显示时间（秒）
    :param title: 通知的标题
    """
    try:
        icon_path = file_util.get_ico()
        # logger.debug(f"icon_path: {icon_path}")
        # img_util.show_img(img_util.read_img(icon_path))
        # time.sleep(20)
        class_name = "WWA_NotifyWindow"
        tooltip_text = "WWA"
        # 创建并显示通知
        WindowsBalloonTip(title, msg, wait_time, icon_path, class_name, tooltip_text)
        # 启动消息循环，直到消息被清理
        win32gui.PumpMessages()
    except Exception as e:
        logger.exception(f"发送系统通知失败, msg: {msg}, error: {str(e)}")
