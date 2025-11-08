# src/providers/windows_provider.py
import time
import dxcam
import pydirectinput
import cv2
import numpy as np
from typing import Optional, Tuple

from ocr_tool.key_code import KeyCode, get_pydirectinput_keyname
from ..interfaces import IDeviceProvider
from ..logger import get_logger

logger = get_logger()

# 设置pydirectinput配置
pydirectinput.FAILSAFE = True  # 启用安全模式（鼠标移动到角落可中断）
pydirectinput.PAUSE = 0.05  # 操作间隔


class WindowsProvider(IDeviceProvider):
    """Windows桌面提供者 - 使用DXcam截图和pydirectinput输入"""

    def __init__(self, region: Tuple[int, int, int, int] = None, output_idx: int = 0):
        """
        初始化Windows提供者

        Args:
            region: 截图区域 (left, top, width, height)，None表示全屏
            output_idx: 显示器索引，0为主显示器
        """
        self.region = region
        self.output_idx = output_idx
        self._camera = None
        self._screen_size = None
        self._init_camera()

    def _init_camera(self):
        """初始化DXcam相机"""
        try:
            # 获取所有显示器信息
            cameras = dxcam.create(output_idx=self.output_idx, output_color="BGR")
            if cameras is None:
                logger.error("DXcam初始化失败：无法创建相机实例")
                return

            self._camera = cameras
            logger.info(f"DXcam初始化成功，显示器索引: {self.output_idx}")

        except Exception as e:
            logger.error(f"DXcam初始化异常: {e}")

    def is_available(self) -> bool:
        """检查DXcam和pydirectinput是否可用"""
        try:
            # 测试DXcam
            if self._camera is None:
                return False

            # 测试截图
            test_frame = self._camera.grab()
            if test_frame is None:
                logger.warning("DXcam截图测试失败")
                return False

            # 测试输入（模拟一个无害的操作）
            pydirectinput.moveRel(0, 0)

            logger.debug("Windows提供者可用性检查通过")
            return True

        except Exception as e:
            logger.error(f"Windows提供者可用性检查失败: {e}")
            return False

    def capture(self) -> Optional[np.ndarray]:
        """使用DXcam截图"""
        try:
            if self._camera is None:
                logger.error("DXcam相机未初始化")
                return None

            # 使用DXcam截图
            frame = self._camera.grab()

            if frame is not None:
                # 更新屏幕尺寸信息
                height, width = frame.shape[:2]
                self._screen_size = (width, height, 0, 0)
                logger.debug(f"DXcam截图成功: {width}x{height}")
                return frame
            else:
                logger.warning("DXcam截图返回空帧")
                return None

        except Exception as e:
            logger.error(f"DXcam截图异常: {e}")
            return None

    def get_size(self) -> Optional[Tuple[int, int, int, int]]:
        """获取屏幕尺寸"""
        if self._screen_size:
            return self._screen_size

        try:
            # 尝试通过截图获取尺寸
            test_frame = self.capture()
            if test_frame is not None:
                height, width = test_frame.shape[:2]
                self._screen_size = (width, height, 0, 0)
                return self._screen_size

            # 备用方法：使用pydirectinput获取屏幕尺寸
            screen_size = pydirectinput.size()
            width, height = screen_size
            self._screen_size = (width, height, 0, 0)
            logger.debug(f"获取屏幕尺寸: {width}x{height}")
            return self._screen_size

        except Exception as e:
            logger.error(f"获取屏幕尺寸异常: {e}")
            return None

    def click(self, x: int, y: int) -> bool:
        """使用pydirectinput点击坐标"""
        try:
            # 移动鼠标并点击
            pydirectinput.moveTo(x, y)
            pydirectinput.click()

            logger.debug(f"Windows点击: ({x}, {y})")
            return True

        except Exception as e:
            logger.error(f"Windows点击异常: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """使用pydirectinput滑动（模拟拖拽）"""
        try:
            # 移动鼠标到起点
            pydirectinput.moveTo(x1, y1)
            # 按下鼠标左键
            pydirectinput.mouseDown()
            # 添加滑动延迟
            time.sleep(duration / 1000.0)
            # 移动到终点
            pydirectinput.moveTo(x2, y2)
            # 释放鼠标左键
            pydirectinput.mouseUp()

            logger.debug(f"Windows滑动: ({x1},{y1}) -> ({x2},{y2}), 时长: {duration}ms")
            return True

        except Exception as e:
            logger.error(f"Windows滑动异常: {e}")
            return False

    def input_text(self, text: str) -> bool:
        """使用pydirectinput输入文本"""
        try:
            # pydirectinput可以直接输入文本
            pydirectinput.write(text)

            logger.debug(f"Windows文本输入: {text}")
            return True

        except Exception as e:
            logger.error(f"Windows文本输入异常: {e}")
            return False

    # 在WindowsProvider的key_event方法中修改这部分：
    def key_event(self, keycode: KeyCode, action: str = "tap") -> bool:
        """发送Windows按键事件"""
        try:
            # 使用pydirectinput键名映射
            key_name = get_pydirectinput_keyname(keycode)
            if not key_name:
                logger.error(f"未知的pydirectinput按键: {keycode.name}")
                return False

            # 原有的按键逻辑保持不变...
            if action == "tap" or action == "press":
                pydirectinput.press(key_name)
            elif action == "down":
                pydirectinput.keyDown(key_name)
            elif action == "up":
                pydirectinput.keyUp(key_name)
            else:
                logger.error(f"不支持的按键动作: {action}")
                return False

            logger.debug(f"Windows按键: {action} {key_name}")
            return True

        except Exception as e:
            logger.error(f"Windows按键异常: {e}")
            return False

    def get_info(self) -> dict:
        """获取Windows设备信息"""
        try:
            size = self.get_size()

            return {
                "type": "windows",
                "provider": "dxcam_pydirectinput",
                "screen_size": size,
                "region": self.region,
                "output_idx": self.output_idx,
            }
        except Exception as e:
            logger.error(f"获取Windows设备信息异常: {e}")
            return {}

    def start_video_capture(self, fps: int = 60):
        """开始连续视频捕获（高性能模式）"""
        try:
            if self._camera is not None:
                self._camera.start(target_fps=fps)
                logger.info(f"开始视频捕获，目标FPS: {fps}")
        except Exception as e:
            logger.error(f"启动视频捕获异常: {e}")

    def stop_video_capture(self):
        """停止连续视频捕获"""
        try:
            if self._camera is not None:
                self._camera.stop()
                logger.info("停止视频捕获")
        except Exception as e:
            logger.error(f"停止视频捕获异常: {e}")

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """获取最新的视频帧（仅在视频捕获模式下有效）"""
        try:
            if self._camera is not None:
                return self._camera.get_latest_frame()
        except Exception as e:
            logger.error(f"获取最新帧异常: {e}")
        return None

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, "_camera") and self._camera is not None:
                self._camera.stop()
        except:
            pass
