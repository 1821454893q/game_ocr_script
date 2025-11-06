import pygetwindow as gw

def debug_window_info():
    """调试窗口信息"""
    windows = gw.getAllTitles()
    for i, title in enumerate(windows):
        if title.strip():
            try:
                win = gw.getWindowsWithTitle(title)[0]
                print(f"[{i}] 标题: {title}")
                print(f"    位置: ({win.left}, {win.top})")
                print(f"    大小: {win.width}x{win.height}")
                print(f"    进程ID: {win._hWnd}")
                print("    " + "-" * 30)
            except:
                pass

# 运行这个来查看详细的窗口信息
debug_window_info()