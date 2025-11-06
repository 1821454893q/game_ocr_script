# src/ocr_engine.py
import time
from typing import List, Tuple, Optional
import cv2
import numpy as np
from paddleocr import TextRecognition

from .logger import get_logger
from .window_manager import WindowManager
from .image_processor import ImageProcessor

logger = get_logger()


class OCREngine:
    """OCR引擎 - 专注于OCR逻辑"""

    def __init__(self, window_title: str = None):
        # 窗口操作交给 WindowManager 类
        self.window_manager = WindowManager(window_title)

        # 图像处理交给 ImageProcessor 类
        self.image_processor = ImageProcessor()

        # 初始化OCR模型
        self.model_det = TextRecognition(model_name="PP-OCRv5_mobile_det")
        self.model_rec = TextRecognition(model_name="PP-OCRv5_mobile_rec")

        logger.info("OCR引擎初始化完成")

    def set_window(self, window_title: str) -> bool:
        """设置目标窗口"""
        return self.window_manager.set_window(window_title)

    def get_window_info(self) -> Optional[dict]:
        """获取窗口信息"""
        return self.window_manager.get_window_info()

    def activate_window(self) -> bool:
        """激活窗口"""
        return self.window_manager.activate_window()

    def find_text(
        self, target_text: str, confidence: float = 0.8
    ) -> Optional[Tuple[int, int, str]]:
        """查找文本并返回坐标"""
        logger.info(f"开始搜索文本: {target_text}")

        try:
            start_time = time.time()

            # 截图 - 使用 WindowCapture
            screenshot = self.window_manager.capture()
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
                    cropped = self.image_processor.crop_by_polygon(screenshot, dt_polys[i])
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
                            bbox = self.image_processor.get_bounding_box(dt_polys[i])
                            center_x, center_y = self.image_processor.get_center(bbox)

                            total_time = (time.time() - start_time) * 1000
                            logger.info(
                                f"✅ 找到文本 '{rec_text}'，坐标: ({center_x}, {center_y})，耗时: {total_time:.1f}ms"
                            )

                            return center_x, center_y, rec_text

            logger.warn(f"未找到文本: {target_text}")
            return None

        except Exception as e:
            logger.error(f"OCR处理异常: {e}")
            return None

    def find_text_in_region(
        self, target_text: str, region: Tuple[int, int, int, int], confidence: float = 0.8
    ) -> Optional[Tuple[int, int, str]]:
        """在指定区域内查找文本"""
        logger.info(f"在区域 {region} 中搜索文本: {target_text}")

        try:
            # 截图
            screenshot = self.window_manager.capture()
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

                    cropped = self.image_processor.crop_by_polygon(region_image, dt_polys[i])
                    if cropped.size == 0:
                        continue

                    rec_results = self.model_rec.predict(cropped, batch_size=1)
                    for rec in rec_results:
                        rec_text = rec.json["res"]["rec_text"]

                        if rec_text and target_text in rec_text:
                            # 调整坐标到全屏坐标系
                            bbox = self.image_processor.get_bounding_box(dt_polys[i])
                            abs_bbox = (
                                bbox[0] + left,
                                bbox[1] + top,
                                bbox[2] + left,
                                bbox[3] + top,
                            )
                            center_x, center_y = self.image_processor.get_center(abs_bbox)

                            logger.info(
                                f"✅ 在区域内找到文本 '{rec_text}'，坐标: ({center_x}, {center_y})"
                            )
                            return center_x, center_y, rec_text

            return None

        except Exception as e:
            logger.error(f"区域OCR处理异常: {e}")
            return None

    def click_text(self, target_text: str, confidence: float = 0.8) -> bool:
        """查找并点击文本"""
        result = self.find_text(target_text, confidence)
        if result:
            x, y, text = result

            WindowManager.click_background(x, y)
            logger.info(f"🖱️ 已点击: {text} ({x}, {y})")
            return True

        logger.warning(f"点击失败，未找到文本: {target_text}")
        return False

    def wait_for_text(
        self, target_text: str, timeout: int = 30, confidence: float = 0.8, interval: float = 1.0
    ) -> Optional[Tuple[int, int, str]]:
        """等待文本出现"""
        import time

        logger.info(f"等待文本出现: {target_text}，超时: {timeout}秒")

        start_time = time.time()
        while time.time() - start_time < timeout:
            result = self.find_text(target_text, confidence)
            if result:
                logger.info("文本已出现")
                return result

            logger.debug(f"文本未出现，等待 {interval} 秒后重试...")
            time.sleep(interval)

        logger.error(f"等待文本超时: {target_text}")
        return None
