from time import sleep
import time
from gas.cons.key_code import KeyCode
import gas.providers.win_provider as wm
import gas.ocr_engine as ocr
from gas.logger import get_logger
import cv2
import win32gui


log = get_logger()


def find_unique_values(arr1, arr2):
    """
    找出两个数组中不重复的值（在另一个数组中不存在的值）

    Args:
        arr1: 第一个数组
        arr2: 第二个数组

    Returns:
        dict: 包含两个数组中各自独有值的字典
    """
    set1 = set(arr1)
    set2 = set(arr2)

    return {
        "unique_in_arr1": list(set1 - set2),  # 在arr1中但不在arr2中
        "unique_in_arr2": list(set2 - set1),  # 在arr2中但不在arr1中
        "all_unique": list((set1 - set2) | (set2 - set1)),  # 所有不重复的值
    }


if __name__ == "__main__":
    # # 示例2: 使用ADB提供者
    # adb_path = r"D:\Program Files\Netease\MuMu Player 12\nx_device\12.0\shell\adb.exe"
    # ocr_engine = ocr.OCREngine.create_with_adb()
    ocr_engine = ocr.OCREngine.create_with_window("MuMuNxDevice", "Qt5156QWindowIcon", 2)

    if ocr_engine.is_ready() is False:
        log.error("ocr引擎启动失败")

    actions = [
        ocr.TextAction("再次进行", lambda x, y, t, e: e.click(x, y)),
        ocr.TextAction("开始挑战", lambda x, y, t, e: e.click(x, y)),
    ]

    # ocr_engine.process_texts(actions, confidence=0.8)
    ocr_engine.swipe(720, 250, 250, 250)
