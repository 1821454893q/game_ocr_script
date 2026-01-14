# src/ocr_engine.py
from dataclasses import dataclass
import time
from typing import List, Tuple, Optional, Callable, Any, Union, Pattern
import cv2
import re
import numpy as np
from rapidocr import RapidOCR, EngineType, LangDet, LangRec, ModelType, OCRVersion

from gas.interfaces.interfaces import IDeviceProvider
from gas.cons.key_code import KeyCode
from gas.providers.adb_provider import ADBProvider

from gas.logger import get_logger
from gas.providers.win_provider import WinProvider
import gas.util.img_util as imgUtil
from gas.util.wrap_util import timeit

logger = get_logger()


@dataclass
class TextAction:
    pattern: Union[str, Pattern]  # 支持字符串或编译好的正则
    action: Callable[[int, int, str, "OCREngine"], Any]
    priority: int = 0
    once: bool = False
    description: str = ""

    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.compiled = re.compile(self.pattern)
            if not self.description:
                self.description = self.pattern
        else:
            self.compiled = self.pattern
            if not self.description:
                self.description = self.pattern.pattern

    def matches(self, text: str) -> bool:
        return bool(self.compiled.search(text))


# OCR结果的对象封装
@dataclass(frozen=True)
class OCRItem:
    text: str
    center: Tuple[int, int]
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) axis-aligned
    score: float


@dataclass
class OCREngine:
    """OCR引擎 - 专注于OCR逻辑"""

    def __init__(self, device_provider: IDeviceProvider = None):
        # 设备提供者
        self.device = device_provider

        # 初始化RapidOCR
        self.rapid_ocr = RapidOCR(
            params={
                "Det.engine_type": EngineType.ONNXRUNTIME,
                "Det.lang_type": LangDet.CH,
                "Det.model_type": ModelType.MOBILE,
                "Det.ocr_version": OCRVersion.PPOCRV4,

                "Rec.engine_type": EngineType.ONNXRUNTIME,
                "Rec.lang_type": LangRec.CH,
                "Rec.model_type": ModelType.MOBILE,
                "Rec.ocr_version": OCRVersion.PPOCRV5,
                
                "Cls.engine_type": EngineType.ONNXRUNTIME,
                "Cls.lang_type": LangDet.CH,
                "Cls.model_type": ModelType.MOBILE,
                "Cls.ocr_version": OCRVersion.PPOCRV4,
            }
        )

        # 预热
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        _ = self.rapid_ocr(dummy_img)

        logger.info("OCR引擎初始化完成（RapidOCR ONNX版）")

    @classmethod
    def create_with_window(
        self, window_title: str, class_name: str = None, capture_mode: int = 1, activate_windows: bool = False
    ):
        """创建使用窗口提供者的OCR引擎"""
        provider = WinProvider(window_title, class_name, capture_mode, activate_windows)
        return self(provider)

    @classmethod
    def create_with_adb(self, adb_path: Optional[str] = None, device_id: Optional[str | int] = None):
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

    def find_text(
        self, target_text: str, confidence: float = 0.5, use_regex: bool = False
    ) -> Optional[Tuple[int, int, str]]:
        pattern = re.compile(target_text) if use_regex else None

        ocr_results: List[OCRItem] = self._perform_ocr(confidence=confidence)

        for item in ocr_results:
            text = item.text
            if (use_regex and pattern.search(text)) or (not use_regex and target_text in text):
                x, y = item.center
                logger.info(f"✅ 找到文本 '{text}' (目标: {target_text})，坐标: ({x}, {y})")
                return x, y, text

        logger.warning(f"未找到文本: {target_text}")
        return None

    def find_text_in_region(
        self, target_text: str, region: Tuple[int, int, int, int], confidence: float = 0.5, use_regex: bool = False
    ) -> Optional[Tuple[int, int, str]]:
        pattern = re.compile(target_text) if use_regex else None

        ocr_results: List[OCRItem] = self._perform_ocr(region=region, confidence=confidence)

        for item in ocr_results:
            text = item.text
            if (use_regex and pattern.search(text)) or (not use_regex and target_text in text):
                x, y = item.center
                logger.info(f"✅ 在区域内找到文本 '{text}'，坐标: ({x}, {y})")
                return x, y, text

        return None

    def process_texts(
        self,
        actions: List[TextAction],
        confidence: float = 0.5,
        stop_after_first: bool = False,
        region: Tuple[int, int, int, int] = None,
    ) -> List[Any]:
        """
        批量处理多个文本动作（支持正则），只OCR一次
        """
        if not actions:
            return []

        # 按优先级排序
        sorted_actions = sorted(actions, key=lambda a: a.priority, reverse=True)
        logger.info(f"批量处理动作: {[a.description for a in sorted_actions]}")

        ocr_results: List[OCRItem] = self._perform_ocr(region=region, confidence=confidence)
        if not ocr_results:
            logger.warning("OCR未识别到任何文本")
            return []

        executed_results = []
        remaining_actions = sorted_actions.copy()

        for item in ocr_results:
            text = item.text
            center_x, center_y = item.center

            for action in remaining_actions[:]:
                if action.matches(text):
                    logger.info(f"✅ 匹配动作: '{action.description}' -> 文本 '{text}'")

                    result = action.action(center_x, center_y, text, self)
                    executed_results.append(
                        {"action": action.description, "text": text, "position": (center_x, center_y), "result": result}
                    )

                    if action.once:
                        remaining_actions.remove(action)

                    if stop_after_first:
                        return [r["result"] for r in executed_results]

        if not executed_results:
            logger.warning("未匹配到任何动作")

        return [r["result"] for r in executed_results]

    def click_text(self, target_text: str, confidence: float = 0.5, use_regex: bool = False) -> bool:
        result = self.find_text(target_text, confidence, use_regex)
        if result:
            x, y, text = result
            success = self.device.click(x, y)
            logger.info(f"🖱️ {'成功' if success else '失败'}点击: {text} ({x}, {y})")
            return success
        return False

    def exist_text(self, target_text: str, confidence: float = 0.5, use_regex: bool = False) -> bool:
        return self.find_text(target_text, confidence, use_regex) is not None

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

    @timeit
    def _perform_ocr(
        self, screenshot: np.ndarray = None, region: Tuple[int, int, int, int] = None, confidence: float = 0.5
    ) -> List[OCRItem]:
        """
        核心OCR识别逻辑：返回所有识别到的文本及其位置
        支持全屏或指定区域

        Returns:
            List[OCRItem]: 每个元素支持 .text, .center, .bbox, .score 属性访问
        """
        if screenshot is None:
            screenshot = self.device.capture()
            if screenshot is None:
                logger.error("截图失败")
                return []

        # 如果指定区域，裁剪
        if region:
            left, top, right, bottom = region
            screenshot = screenshot[top:bottom, left:right]
            offset_x, offset_y = left, top
        else:
            offset_x, offset_y = 0, 0

        try:
            # RapidOCR 返回 RapidOCROutput 对象（非 iterable）
            ocr_result = self.rapid_ocr(screenshot)

            if ocr_result is None or not ocr_result.txts:
                logger.debug("OCR未识别到任何文本")
                return []

            ocr_items: List[OCRItem] = []

            # 正确迭代：txts、scores、boxes 长度一致
            for text, score, bbox_points in zip(ocr_result.txts, ocr_result.scores, ocr_result.boxes):
                text = text.strip()
                if score < confidence or not text:
                    continue

                # 计算 axis-aligned bbox 和 center
                xs = [p[0] for p in bbox_points]
                ys = [p[1] for p in bbox_points]
                x1, x2 = int(min(xs)), int(max(xs))
                y1, y2 = int(min(ys)), int(max(ys))

                # 加上区域偏移
                abs_bbox = (x1 + offset_x, y1 + offset_y, x2 + offset_x, y2 + offset_y)
                center = ((x1 + x2) // 2 + offset_x, (y1 + y2) // 2 + offset_y)

                ocr_items.append(OCRItem(text=text, center=center, bbox=abs_bbox, score=score))

            # logger.debug(f"识别结果: {ocr_items}")
            logger.debug(f"OCR识别到 {len(ocr_items)} 个文本区域")
            return ocr_items

        except Exception as e:
            logger.error(f"_perform_ocr 异常: {e}")
            return []

    # 以下方法保持不变...
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

    def click(self, x: int, y: int) -> bool:
        return self.device.click(x, y)

    def mouse_left_down(self, x: int, y: int) -> bool:
        return self.device.click(x, y, "down")

    def mouse_left_up(self, x: int, y: int) -> bool:
        return self.device.click(x, y, "up")
