from time import sleep
import time
from gas.cons.key_code import KeyCode
import gas.providers.win_provider as wm
import gas.ocr_engine as ocr
import cv2
import win32gui


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


def login(ocr_engine):
    while True:
        ocr_engine.click_text("二重")
        sleep(1.0)
        ocr_engine.click_text("登录")
        sleep(1.0)
        ocr_engine.click_text("点击进入游戏")
        sleep(1.0)
        if ocr_engine.exist_text("UID"):
            break
        sleep(1.0)


# 进入副本
def enter_instance(ocr_engine: ocr.OCREngine):
    while True:
        if ocr_engine.exist_text("Lv"):
            ocr_engine.click(74, 34)  # 点击菜单

        if ocr_engine.exist_text("整备"):
            # 通过点击进入副本！
            ocr_engine.click(195, 518)  # 历练
            sleep(1.0)
            ocr_engine.click(95, 234)  # 左边副本按钮
            sleep(1.0)
            ocr_engine.click(980, 128)  # 夜航手册
            sleep(1.0)
            ocr_engine.click(1450, 670)  # 前往
            sleep(1.0)
            ocr_engine.click(1300, 840)  # 确认选择
            sleep(1.0)
            ocr_engine.click(1390, 775)  # 开始挑战
            break
        sleep(1.0)


# 重复挑战
def repeat_instance(ocr_engine: ocr.OCREngine):
    nowTime = int(time.time())
    internal = 60  # 60秒
    text = ""
    moveY = 800
    while True:
        if ocr_engine.click_text("再次进行"):
            nowTime = int(time.time())
            sleep(1.0)

        if ocr_engine.click_text("开始挑战"):
            nowTime = int(time.time())
            sleep(1.0)

        result = ocr_engine.find_text("已驱逐敌人")
        if result:
            x, y, tempText = result
            if tempText != text:
                text = tempText
                print(f"{text} 变化 更新计时")
                nowTime = int(time.time())

        ocr_engine.swipe(270, 700, 270, moveY)
        moveY -= 50
        if moveY < 600:
            moveY = 800

        # 太久没打完 重新进入副本
        if int(time.time()) - nowTime > internal:
            reenter_instance(ocr_engine)
            nowTime = int(time.time())
        sleep(1.0)


# 重新进入副本
def reenter_instance(ocr_engine: ocr.OCREngine):
    ocr_engine.click(74, 34)  # 点击菜单
    sleep(1.0)
    ocr_engine.click(1460, 800)  # 放弃挑战
    sleep(1.0)
    ocr_engine.click(980, 520)  # 确定


# 服务器断线重连
def reconnect(ocr_engine: ocr.OCREngine):
    if ocr_engine.exist_text("游戏服务器连接断开"):
        ocr_engine.click_text("重新连接")
    sleep(1.0)


def test_bitblt():
    hander = [0x0280E44]
    w = wm.WinProvider("二重螺旋  ", "UnrealWindow", 2)
    # w = wm.WinProvider("MuMuNxDevice", "Qt5156QWindowIcon", 2)

    for h in hander:

        # cn = win32gui.GetClassName(h)
        # t = win32gui.GetWindowText(h)
        # print(f"title {t} calssname {cn}")

        # cv = w.capture_print_window(h)
        # cv2.imshow("title", cv)
        # cv2.waitKey(0)

        # cv = w.capture_bitblt(h)
        # cv2.imshow("title", cv)
        # cv2.waitKey(0)

        # cv = w.capture()
        # cv = w.capture()
        # cv2.imshow("title", cv)
        # cv2.waitKey(0)

        w.click(680, 670)

    # tempList = []
    # hander = []
    # while True:
    #     response = input("回车之后会更新hwnd (输入q退出): ")

    #     if response.lower() == "q":
    #         break

    #     tempList2 = []
    #     wList = wm.list_all_windows()
    #     for l in wList:
    #         tempList2.append(l["hwnd"])

    #     # 修复：正确接收返回值
    #     result = find_unique_values(tempList, tempList2)

    #     print(f"新增窗口句柄: {result['unique_in_arr2']}")
    #     print(f"消失窗口句柄: {result['unique_in_arr1']}")
    #     print(f"总共变化: {len(result['all_unique'])} 个窗口")
    #     print("-" * 50)
    #     tempList = tempList2


if __name__ == "__main__":
    # # 示例2: 使用ADB提供者
    # adb_path = r"D:\Program Files\Netease\MuMu Player 12\nx_device\12.0\shell\adb.exe"
    # # ocr_adb = ocr.OCREngine.create_with_adb(adb_path, "127.0.0.1:16366")
    # # ocr_adb = ocr.OCREngine.create_with_window("MuMuNxDevice", "Qt5156QWindowIcon", 2)
    ocr_adb = ocr.OCREngine.create_with_window("二重螺旋  ", "UnrealWindow", 2)
    # ocr_adb.click_text("游戏")
    for i in range(100):
        # ocr_adb.key_click(KeyCode.SPACE)
        x1, y1, x2, y2 = 200, 300, 200, 400
        ocr_adb.mouse_left_down(x1, y1)
        time.sleep(1)
        ocr_adb.swipe(x1, y1, x2, y2)
        time.sleep(1)
        ocr_adb.mouse_left_up(x2, y2)
        time.sleep(1)

    # # 首次开始 登录 掉线 登录
    login(ocr_adb)
    # # 进入副本
    # enter_instance(ocr_adb)

    # reenter_instance(ocr_adb)

    # ocr_adb.start_relative_recording()

    # test_bitblt()

    pass
