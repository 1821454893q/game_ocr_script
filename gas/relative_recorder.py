# src/pynput_recorder.py
import time
from pynput import mouse, keyboard
from typing import List, Tuple
import pyautogui
from gas.logger import get_logger

logger = get_logger()


class PynputClickRecorder:
    """使用pynput的点击记录器 - 最稳定"""

    def __init__(self, ocr_engine):
        self.ocr_engine = ocr_engine
        self.recorded_clicks: List[Tuple[float, float]] = []
        self.screen_width, self.screen_height = pyautogui.size()
        self.is_recording = False
        self.mouse_listener = None
        self.keyboard_listener = None

    def record_clicks(self):
        """记录点击序列 - 使用pynput监听真实点击"""
        logger.info(f"开始记录相对坐标，屏幕分辨率: {self.screen_width}x{self.screen_height}")
        logger.info("点击鼠标左键记录坐标，按ESC键停止记录")

        self.recorded_clicks = []
        self.is_recording = True
        click_count = 0

        def on_click(x, y, button, pressed):
            if not self.is_recording:
                return False

            if pressed and button == mouse.Button.left:
                # 转换为相对坐标
                rel_x = round(x / self.screen_width, 4)
                rel_y = round(y / self.screen_height, 4)

                self.recorded_clicks.append((rel_x, rel_y))
                click_count = len(self.recorded_clicks)

                print(f"✅ 记录点击 {click_count}: ({rel_x:.4f}, {rel_y:.4f})")

        def on_press(key):
            if key == keyboard.Key.esc:
                self.stop_recording()
                return False

        # 启动监听器
        self.mouse_listener = mouse.Listener(on_click=on_click)
        self.keyboard_listener = keyboard.Listener(on_press=on_press)

        self.mouse_listener.start()
        self.keyboard_listener.start()

        print("开始监听鼠标点击... (按ESC键结束)")

        try:
            self.keyboard_listener.join()
        except KeyboardInterrupt:
            self.stop_recording()

        self._generate_code()

    def stop_recording(self):
        """停止记录"""
        self.is_recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("\n停止记录")

    def _generate_code(self):
        """生成代码"""
        if not self.recorded_clicks:
            print("没有记录到点击")
            return

        code_lines = [
            "# 自动生成的点击代码",
            "from time import sleep",
            "",
            "def execute_clicks(ocr_engine):",
            '    """执行点击序列"""',
        ]

        for i, (rel_x, rel_y) in enumerate(self.recorded_clicks, 1):
            code_lines.append(f"    # 点击{i}")
            code_lines.append(f"    ocr_engine.click_relative({rel_x:.4f}, {rel_y:.4f})")
            code_lines.append("    sleep(1.0)")
            code_lines.append("")

        code = "\n".join(code_lines)

        print("\n" + "=" * 60)
        print("生成的代码:")
        print("=" * 60)
        print(code)
        print("=" * 60)

        with open("click_script.py", "w", encoding="utf-8") as f:
            f.write(code)
        print("代码已保存到 click_script.py")
