from time import sleep
import time
from gas.cons.key_code import KeyCode
import gas.providers.win_provider as wm
from gas.recorder.operation_player import OperationPlayer, ReplayConfig
import gas.ocr_engine as ocr
from gas.logger import get_logger
import cv2
import win32gui

if __name__ == "__main__":
    ocr_engine = ocr.OCREngine.create_with_window("MuMuNxDevice", "Qt5156QWindowIcon", 2)
    # ocr_engine = ocr.OCREngine.create_with_adb()

    if ocr_engine.is_ready() is False:
        print("ocr引擎启动失败")
    player = OperationPlayer(ocr_engine.device)

    player.load_from_file(r"E:\inner_py\ocr_utils\tests\recorder\test.json")
    player.replay()
