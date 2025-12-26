# src/ocr_engine.py
import time
from typing import List, Tuple, Optional
import cv2
import numpy as np
from paddleocr import TextRecognition

from gas.interfaces.interfaces import IDeviceProvider
from gas.cons.key_code import KeyCode
from gas.providers.adb_provider import ADBProvider
from gas.relative_recorder import PynputClickRecorder

from gas.logger import get_logger
from gas.providers.win_provider import WinProvider
import gas.util.img_util as imgUtil

logger = get_logger()


class OCREngine:
    """OCR引擎 - 专注于OCR逻辑"""

    def __init__(self, device_provider: IDeviceProvider = None):
        # 设备提供者
        self.device = device_provider

        # 初始化OCR模型
        self.model_det = TextRecognition(model_name="PP-OCRv5_mobile_det")
        self.model_rec = TextRecognition(model_name="PP-OCRv5_mobile_rec")

        logger.info("OCR引擎初始化完成")

    @classmethod
    def create_with_window(self, window_title: str, class_name: str = None, capture_mode: int = 1):
        """创建使用窗口提供者的OCR引擎"""
        provider = WinProvider(window_title, class_name, capture_mode)

        return self(provider)

    @classmethod
    def create_with_adb(self, adb_path: str, device_id: str = None):
        """创建使用ADB提供者的OCR引擎"""
        provider = ADBProvider(adb_path, device_id)
        return self(provider)

    def set_device_provider(self, provider: IDeviceProvider):
        """设置设备提供者"""
        self.device = provider
        logger.info(f"设备提供者已设置: {type(provider).__name__}")

    def is_ready(self) -> bool:
        """检查引擎是否就绪"""
        return self.device is not None and self.device.is_available()

    def find_text(self, target_text: str, confidence: float = 0.5) -> Optional[Tuple[int, int, str]]:
        """查找文本并返回坐标"""
        logger.info(f"开始搜索文本: {target_text}")

        try:
            start_time = time.time()

            # 使用设备提供者截图
            screenshot = self.device.capture()
            if screenshot is None:
                logger.error("截图失败")
                return None

            # 文本检测 - OCR核心逻辑
            det_results = self.model_det.predict(screenshot, batch_size=1)

            for res in det_results:
                dt_polys = res.json["res"]["dt_polys"]
                dt_scores = res.json["res"]["dt_scores"]

                logger.debug(f"检测到 {len(dt_polys)} 个文本区域")

                for i, score in enumerate(dt_scores):
                    if score < confidence:
                        continue

                    # 裁剪区域 - 使用 ImageProcessor
                    cropped = imgUtil.crop_by_polygon(screenshot, dt_polys[i])
                    if cropped.size == 0:
                        logger.debug(f"跳过无效的裁剪区域 {i}")
                        continue

                    # 文本识别 - OCR核心逻辑
                    rec_results = self.model_rec.predict(cropped, batch_size=1)
                    for rec in rec_results:
                        rec_text = rec.json["res"]["rec_text"]
                        logger.debug(f"识别文本: {rec_text} (置信度: {score:.3f})")

                        if rec_text and target_text in rec_text:
                            # 计算中心坐标 - 使用 ImageProcessor
                            bbox = imgUtil.get_bounding_box(dt_polys[i])
                            center_x, center_y = imgUtil.get_center(bbox)

                            total_time = (time.time() - start_time) * 1000
                            logger.info(
                                f"✅ 找到文本 '{rec_text}',坐标: ({center_x}, {center_y}),符合目标 '{target_text}',耗时: {total_time:.1f}ms"
                            )

                            return center_x, center_y, rec_text

            logger.warn(f"未找到文本: {target_text}")
            return None

        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            return None

    def find_text_in_region(
        self, target_text: str, region: Tuple[int, int, int, int], confidence: float = 0.5
    ) -> Optional[Tuple[int, int, str]]:
        """在指定区域内查找文本"""
        logger.info(f"在区域 {region} 中搜索文本: {target_text}")

        try:
            # 截图
            screenshot = self.device.capture()
            if screenshot is None:
                return None

            # 裁剪指定区域
            left, top, right, bottom = region
            region_image = screenshot[top:bottom, left:right]

            if region_image.size == 0:
                logger.error("区域裁剪失败")
                return None

            # 在裁剪后的区域进行OCR
            det_results = self.model_det.predict(region_image, batch_size=1)

            for res in det_results:
                dt_polys = res.json["res"]["dt_polys"]
                dt_scores = res.json["res"]["dt_scores"]

                for i, score in enumerate(dt_scores):
                    if score < confidence:
                        continue

                    cropped = imgUtil.crop_by_polygon(region_image, dt_polys[i])
                    if cropped.size == 0:
                        continue

                    rec_results = self.model_rec.predict(cropped, batch_size=1)
                    for rec in rec_results:
                        rec_text = rec.json["res"]["rec_text"]

                        if rec_text and target_text in rec_text:
                            # 调整坐标到全屏坐标系
                            bbox = imgUtil.get_bounding_box(dt_polys[i])
                            abs_bbox = (
                                bbox[0] + left,
                                bbox[1] + top,
                                bbox[2] + left,
                                bbox[3] + top,
                            )
                            center_x, center_y = imgUtil.get_center(abs_bbox)

                            logger.info(f"✅ 在区域内找到文本 '{rec_text}'，坐标: ({center_x}, {center_y})")
                            return center_x, center_y, rec_text

            return None

        except Exception as e:
            logger.error(f"区域OCR处理异常: {e}")
            return None

    def click_text(self, target_text: str, confidence: float = 0.5) -> bool:
        """查找并点击文本"""
        result = self.find_text(target_text, confidence)
        if result:
            x, y, text = result
            success = self.device.click(x, y)
            if success:
                logger.info(f"🖱️ 已点击: {text} ({x}, {y})")
            else:
                logger.error(f"点击失败: {text} ({x}, {y})")
            return success

        logger.warning(f"点击失败，未找到文本: {target_text}")
        return False

    def click(self, x: int, y: int) -> bool:
        return self.device.click(x, y)

    def mouse_left_down(self, x: int, y: int) -> bool:
        return self.device.click(x, y, "down")

    def mouse_left_up(self, x: int, y: int) -> bool:
        return self.device.click(x, y, "up")

    def exist_text(self, target_text: str, confidence: float = 0.5) -> bool:
        """检查文本是否存在"""
        return self.find_text(target_text, confidence) is not None

    def wait_for_text(
        self, target_text: str, timeout: int = 30, confidence: float = 0.5, interval: float = 1.0
    ) -> Optional[Tuple[int, int, str]]:
        """等待文本出现"""
        import time

        logger.debug(f"等待文本出现: {target_text}，超时: {timeout}秒")

        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.find_text(target_text, confidence)
            if result:
                logger.debug("文本已出现")
                return result

            logger.debug(f"文本未出现，等待 {interval} 秒后重试...")
            time.sleep(interval)

        logger.error(f"等待文本超时: {target_text}")
        return None

    def get_device_info(self) -> dict:
        """获取设备信息"""
        if self.device:
            return self.device.get_info()
        return {}

    def input_text(self, text: str) -> bool:
        """输入文本"""
        success = self.device.input_text(text)
        if success:
            logger.debug(f"已输入文本: {text}")
        else:
            logger.error(f"文本输入失败: {text}")
        return success

    def key_click(self, key: KeyCode) -> bool:
        """发送按键事件"""
        success = self.device.key_event(key, action="tap")
        if success:
            logger.debug(f"已发送按键事件: {key.name}")
        else:
            logger.error(f"发送按键事件失败: {key.name}")
        return success

    def key_down(self, key: KeyCode) -> bool:
        """发送按键事件"""
        success = self.device.key_event(key, action="down")
        if success:
            logger.debug(f"已发送按键事件: {key.name}")
        else:
            logger.error(f"发送按键事件失败: {key.name}")
        return success

    def key_up(self, key: KeyCode) -> bool:
        """发送按键事件"""
        success = self.device.key_event(key, action="up")
        if success:
            logger.debug(f"已发送按键事件: {key.name}")
        else:
            logger.error(f"发送按键事件失败: {key.name}")
        return success

    def swipe(self, x1: int, y1: int, x2: int, y2: int, is_drag: bool = True, duration: float = 0.5) -> bool:
        """滑动"""
        success = self.device.swipe(x1, y1, x2, y2, is_drag, duration)
        if success:
            logger.debug(f"已滑动: ({x1}, {y1}) -> ({x2}, {y2})")
        else:
            logger.error(f"滑动失败: ({x1}, {y1}) -> ({x2}, {y2})")
        return success
