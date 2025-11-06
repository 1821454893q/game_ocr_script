import pygetwindow as gw
import cv2
import numpy as np
from PIL import Image
import os
import time
import win32gui
import win32ui
import win32con

def list_all_windows():
    """列出所有窗口供选择"""
    windows = gw.getAllTitles()
    print("=== 可用窗口列表 ===")
    valid_windows = []
    for i, title in enumerate(windows):
        if title.strip():  # 只显示非空标题
            valid_windows.append(title)
            print(f"[{i}] {title}")
    print("==================")
    return valid_windows

def capture_window_by_title(window_title, save_path=None):
    """
    后台截取指定窗口的截图
    即使窗口被遮挡或最小化也能工作
    """
    try:
        # 查找窗口
        windows = gw.getWindowsWithTitle(window_title)
        if not windows:
            print(f"❌ 未找到窗口: {window_title}")
            return None
        
        window = windows[0]
        print(f"✅ 找到窗口: {window_title}")
        print(f"   位置: ({window.left}, {window.top})")
        print(f"   大小: {window.width}x{window.height}")
        print(f"   状态: {'最小化' if window.isMinimized else '正常'}")
        
        # 获取窗口句柄
        hwnd = window._hWnd
        
        # 方法1: 使用pygetwindow（简单但可能截不到最小化窗口）
        try:
            # 尝试直接截图
            screenshot = window.getClientFrame()
            screenshot_cv = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_cv, cv2.COLOR_RGB2BGR)
            print("   📸 使用方法1截图成功")
        except Exception as e:
            print(f"   ⚠️ 方法1失败: {e}")
            # 方法2: 使用Windows API（更可靠的后台截图）
            screenshot_cv = capture_window_win32(hwnd)
            if screenshot_cv is None:
                return None
        
        # 显示图片
        display_image(screenshot_cv, window_title)
        
        # 保存图片（可选）
        if save_path:
            cv2.imwrite(save_path, screenshot_cv)
            print(f"   💾 图片已保存: {save_path}")
        
        return screenshot_cv
        
    except Exception as e:
        print(f"❌ 截图失败: {e}")
        return None

def capture_window_win32(hwnd):
    """使用Windows API进行后台截图"""
    try:
        # 获取窗口客户区大小
        left, top, right, bottom = win32gui.GetClientRect(hwnd)
        width = right - left
        height = bottom - top
        
        if width == 0 or height == 0:
            print("   ⚠️ 窗口客户区大小为0,可能最小化")
            return None
        
        # 创建设备上下文
        hwndDC = win32gui.GetWindowDC(hwnd)
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        saveDC = mfcDC.CreateCompatibleDC()
        
        # 创建位图对象
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        
        # 选择位图到设备上下文
        saveDC.SelectObject(saveBitMap)
        
        # 截图
        result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
        
        if result is None:
            # 转换位图数据
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            
            # 转换为numpy数组
            screenshot = np.frombuffer(bmpstr, dtype='uint8')
            screenshot.shape = (height, width, 4)  # BGRA格式
            
            # 转换为BGR（OpenCV格式）
            screenshot_cv = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
            
            return screenshot_cv
        else:
            return None
            
    except ImportError:
        print("   ❌ 请安装pywin32: pip install pywin32")
        return None
    except Exception as e:
        print(f"   ❌ Windows API截图失败: {e}")
        return None

def display_image(image, window_title):
    """显示图片"""
    # 调整图片大小以适应屏幕显示
    height, width = image.shape[:2]
    max_display_size = 800
    
    if max(width, height) > max_display_size:
        scale = max_display_size / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        display_image = cv2.resize(image, (new_width, new_height))
    else:
        display_image = image
    
    # 显示图片
    cv2.imshow(f'窗口截图: {window_title}', display_image)
    print("   👀 图片已显示，按任意键关闭窗口...")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def save_multiple_windows():
    """批量保存多个窗口截图"""
    windows = list_all_windows()
    
    # 创建截图目录
    os.makedirs("window_screenshots", exist_ok=True)
    
    for i, title in enumerate(windows):
        if title.strip():
            print(f"\n[{i+1}/{len(windows)}] 截取: {title}")
            save_path = f"window_screenshots/{title.replace(':', '_').replace('/', '_')}_{int(time.time())}.png"
            capture_window_by_title(title, save_path)
            time.sleep(1)  # 避免太快

def main():
    """主程序"""
    print("🎮 后台窗口截图工具")
    print("=" * 50)
    
    while True:
        print("\n选择操作:")
        print("1. 查看所有窗口")
        print("2. 截取指定窗口")
        print("3. 批量截取所有窗口")
        print("4. 退出")
        
        choice = input("请输入选择 (1-4): ").strip()
        
        if choice == "1":
            list_all_windows()
            
        elif choice == "2":
            windows = list_all_windows()
            if windows:
                try:
                    selection = input("输入窗口编号或直接输入窗口标题: ").strip()
                    if selection.isdigit():
                        window_title = windows[int(selection)]
                    else:
                        window_title = selection
                    
                    save_option = input("是否保存图片? (y/n): ").strip().lower()
                    save_path = f"{window_title.replace(':', '_')}_{int(time.time())}.png" if save_option == 'y' else None
                    
                    capture_window_by_title(window_title, save_path)
                except (IndexError, ValueError):
                    print("❌ 无效选择")
                    
        elif choice == "3":
            save_multiple_windows()
            
        elif choice == "4":
            print("👋 再见!")
            break
            
        else:
            print("❌ 无效选择")

if __name__ == "__main__":
    main()