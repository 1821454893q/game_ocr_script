from typing import List, Tuple, Optional
import cv2
import numpy as np
import pyautogui
import view_screenshot_cv as my
import pygetwindow as gw
import utils

from paddleocr import TextRecognition

# PP-OCRv5_server_rec 81MB
# PP-OCRv5_mobile_rec 16MB
modelDet = TextRecognition(model_name="PP-OCRv5_mobile_det")
modelRec = TextRecognition(model_name="PP-OCRv5_mobile_rec")

@utils.calculate_time("整体OCR识别")
def find_text_coordinates(target_text, region=None, confidence=60) -> tuple[list,str]:
    """通过OCR识别文字 并返回坐标"""
    # 查找窗口
    window_title = 'MuMu安卓设备'
    windows = gw.getWindowsWithTitle(window_title)
    if not windows:
        print(f"❌ 未找到窗口: {window_title}")
        return [], ""
    
    window = windows[0]
    # 获取窗口句柄
    hwnd = window._hWnd
    screenshot_cv = my.capture_window_win32(hwnd)

    if screenshot_cv is None:
        print("❌ 截图失败")
        return [], ""

    screenshot_height, screenshot_width = screenshot_cv.shape[:2]
    print(f"✅ 截图成功，尺寸: {screenshot_width}x{screenshot_height}")

    result = modelDet.predict(screenshot_cv, batch_size=1)

    # 可视化结果并保存 json 结果
    for res in result:
        # 注意：这里的数据结构是 numpy array，不是 list
        dt_polys = res.json['res']['dt_polys']  # shape: (39, 4, 2)
        dt_scores = res.json['res']['dt_scores']

        print(f"找到 {len(dt_polys)} 个检测框")

        for i, dt in enumerate(dt_scores):
            if dt < 0.8:
                continue
            # 获取当前检测框的多边形坐标
            polygon = dt_polys[i]  # shape: (4, 2)
            # 裁剪区域
            sc_region = crop_by_polygon_simple(screenshot_cv, polygon)
            
            if sc_region.size == 0:
                print(f"❌ 裁剪失败，跳过该框")
                continue

            # 识别文本
            recRes = modelRec.predict(sc_region, batch_size=1)
            for rec in recRes:
                rec_text = rec.json['res']['rec_text']
                print(f"识别文本: '{rec_text}'")
                if rec_text and target_text in rec_text:
                    print(f"🎯 找到目标文本: '{rec_text}'")
                    bbox = calculate_region(polygon)
                    return [bbox], rec_text

    cv2.destroyAllWindows()
    return [], ""

# 改进裁剪函数，处理 numpy array 格式
def crop_by_polygon_simple(screenshot_cv: np.ndarray, polygon) -> np.ndarray:
    """
    根据多边形的边界框进行矩形裁剪
    支持 list 或 numpy array 格式的 polygon
    """
    try:
        # 处理 numpy array 格式
        if isinstance(polygon, np.ndarray):
            polygon = polygon.tolist()
        
        left, top, right, bottom = calculate_region(polygon)
        
        # 获取原图尺寸
        height, width = screenshot_cv.shape[:2]
        
        # 边界检查
        left = max(0, left)
        top = max(0, top)
        right = min(width, right)
        bottom = min(height, bottom)
        
        # 确保区域有效且不是太小
        if left >= right or top >= bottom:
            print("❌ 无效的裁剪区域: 左>=右 或 上>=下")
            return np.array([])
        
        if (right - left) < 2 or (bottom - top) < 2:
            print("❌ 裁剪区域太小")
            return np.array([])
        
        # 裁剪
        cropped = screenshot_cv[top:bottom, left:right]
        return cropped
        
    except Exception as e:
        print(f"❌ 裁剪失败: {e}")
        return np.array([])

def calculate_region(polygon):
    """计算边界框，支持 list 和 numpy array"""
    try:
        # 转换为列表格式
        if isinstance(polygon, np.ndarray):
            points = polygon.tolist()
        else:
            points = polygon
        
        # 提取所有坐标
        x_coords = [point[0] for point in points]
        y_coords = [point[1] for point in points]
        
        left = min(x_coords)
        top = min(y_coords)
        right = max(x_coords)
        bottom = max(y_coords)
        
        return left, top, right, bottom
        
    except Exception as e:
        print(f"❌ 计算边界框失败: {e}")
        return 0, 0, 0, 0

def get_text_center_coordinates(target_text, region=None) -> Optional[Tuple[int, int, str]]:
    """
    获取文本的中心点坐标
    返回: (center_x, center_y, text) 或 None
    """
    boxes, text = find_text_coordinates(target_text, region)
    
    if boxes and text:  # 检查是否都有值
        try:
            # boxes 是一个列表，包含一个边界框元组
            bbox = boxes[0]  # 获取第一个边界框
            x, y, w, h = bbox  # 解包边界框
            center_x = x + w // 2
            center_y = y + h // 2
            return center_x, center_y, text
        except (ValueError, TypeError) as e:
            print(f"❌ 边界框解析错误: {e}, boxes: {boxes}")
            return None
    
    return None

def test_ocr():
    target_text = "敌人"  # 你要找的文本

    while True:
        choice = input("1-重复 2-结束 3-测试: ").strip()
        if choice == "1":
            text = input(f"目前寻找：{target_text} 需要更新输入新的文本： ").strip()
            if text != "":
                target_text = text

            result = get_text_center_coordinates(target_text)
            
            if result:
                center_x, center_y, res_text = result
                print(f"✅ 找到文本 '{res_text}'")
                print(f"📌 中心坐标: ({center_x}, {center_y})")
                # 可选：立即点击该位置
                # pyautogui.click(center_x, center_y)
            else:
                print("❌ 未找到文本")
        elif choice == "2":
            print("👋 再见!")
            break
        elif choice == "3":
            result = modelDet.predict('./output/image.png')
            for res in result:
                print(f"文本:'{res.print()}'")
                res.save_to_img("output")
                res.save_to_json("output")

if __name__ == "__main__":
    test_ocr()