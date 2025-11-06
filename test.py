import ocr_tool.window_manager as wm
import ocr_tool.ocr_engine as ocr
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


if __name__ == "__main__":
    tempList = []
    hander = []
    while True:
        response = input("回车之后会更新hwnd (输入q退出): ")

        if response.lower() == "q":
            break

        tempList2 = []
        wList = wm.list_all_windows()
        for l in wList:
            tempList2.append(l["hwnd"])

        # 修复：正确接收返回值
        result = find_unique_values(tempList, tempList2)

        print(f"新增窗口句柄: {result['unique_in_arr2']}")
        print(f"消失窗口句柄: {result['unique_in_arr1']}")
        print(f"总共变化: {len(result['all_unique'])} 个窗口")
        print("-" * 50)
        tempList = tempList2

    hander = [788480, 1115400, 984480, 460706, 655536, 3539122, 460466, 1181110, 2360632, 1051064, 1050680, 787770, 591432, 1901896, 2295752, 199120, 14158048, 918762, 199152, 1377912, 1377480]
    w = wm.WindowManager("二重螺旋  ", "UnrealWindow")
    for h in hander:
        cv = w.capture_bitblt(h)
        cv2.imshow("title", cv)
        cv2.waitKey(0)

    # w = wm.WindowManager("MuMu安卓设备", "Qt5156QWindowIcon")
    # cv = w.capture()
    # cv2.imshow("title", cv)
    # cv2.waitKey(0)
    # cv2.waitKey(0)

    # w = wm.WindowManager("nemudisplay", "nemuwin")
    # cv = w.capture()
    # cv2.imshow("title", cv)
    # cv2.waitKey(0)
