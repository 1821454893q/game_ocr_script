import ocr_tool.window_manager as wm
import ocr_tool.ocr_engine as ocr
import cv2


if __name__ == "__main__":

    # 类名='Qt5156QWindowIcon', 标题='MuMuNxDevice'
    engine = ocr.OCREngine("MuMuNxDevice", "Qt5156QWindowIcon")

    engine.click_text("开始游戏", 0.6)
    engine.click_text("登录", 0.6)
    engine.click_text("进入", 0.6)
    engine.click_text("委托", 0.6)
    engine.click_text("云二重螺旋", 0.6)
    if engine.exist_text("因为您长时间未操作游戏，已中断连接", 0.6):
        engine.click_text("退出游戏", 0.6)
