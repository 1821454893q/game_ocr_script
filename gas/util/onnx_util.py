import onnxruntime as ort
import cv2
import numpy as np
import time
from pathlib import Path
from typing import Union, List, Dict, Optional
import win32gui
import win32ui
import win32con

from gas.logger import get_logger

log = get_logger()


class YOLOONNXDetector:
    """
    YOLO ONNX 检测器 - 支持多种输入源
    功能：图片文件、numpy数组、窗口句柄截图
    """

    def __init__(
        self,
        onnx_path: str,
        class_names: List[str] = None,
        conf_threshold: float = 0.3,
        iou_threshold: float = 0.5,
        input_size: tuple = (640, 640),
    ):
        """
        初始化检测器

        Args:
            onnx_path: ONNX模型文件路径
            class_names: 类别名称列表
            conf_threshold: 置信度阈值
            iou_threshold: IOU阈值
            input_size: 模型输入尺寸 (width, height)
        """
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_width, self.input_height = input_size

        log.debug("🔧 正在初始化 YOLO ONNX 检测器...")

        # 创建 ONNX Runtime 会话
        providers = ["CPUExecutionProvider"]
        try:
            self.session = ort.InferenceSession(onnx_path, providers=providers)
        except Exception as e:
            raise ValueError(f"无法加载 ONNX 模型: {e}")

        # 获取模型信息
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]

        # 如果提供了输入尺寸，使用提供的尺寸
        if input_size != (640, 640):
            model_input_shape = self.session.get_inputs()[0].shape
            if len(model_input_shape) == 4:
                self.input_height = model_input_shape[2]
                self.input_width = model_input_shape[3]

        # 类别名称
        self.class_names = class_names or ["object"]  # 默认类别

        log.debug("✅ YOLO ONNX 检测器初始化成功")
        log.debug(f"   输入尺寸: {self.input_width}x{self.input_height}")
        log.debug(f"   类别数量: {len(self.class_names)}")
        log.debug(f"   类别列表: {self.class_names}")

    # ==================== 图像预处理方法 ====================

    def _preprocess_image(self, image: np.ndarray) -> tuple:
        """
        通用图像预处理

        Args:
            image: 输入图像 (BGR格式)

        Returns:
            tuple: (预处理后的tensor, 原始图像, 原始尺寸)
        """
        if image is None:
            raise ValueError("输入图像为空")

        original_image = image.copy()
        original_height, original_width = image.shape[:2]

        # 调整尺寸
        resized = cv2.resize(image, (self.input_width, self.input_height))

        # 归一化
        normalized = resized / 255.0

        # BGR -> RGB
        rgb_image = normalized[:, :, ::-1]

        # (H, W, C) -> (C, H, W)
        channel_first = np.transpose(rgb_image, (2, 0, 1))

        # (C, H, W) -> (1, C, H, W)
        batched = np.expand_dims(channel_first, axis=0)

        # 转换为 float32
        input_tensor = batched.astype(np.float32)

        return input_tensor, original_image, (original_width, original_height)

    # ==================== 后处理方法 ====================

    def _postprocess_detections(self, outputs: List[np.ndarray], original_shape: tuple) -> List[Dict]:
        """
        后处理检测结果

        Args:
            outputs: 模型输出
            original_shape: 原始图像尺寸 (width, height)

        Returns:
            List[Dict]: 检测结果列表
        """
        predictions = outputs[0]

        # 处理 YOLO 输出格式 (1, 84, 8400) -> (8400, 84)
        if len(predictions.shape) == 3:
            predictions = np.squeeze(predictions, 0).T

        boxes = predictions[:, :4]  # x_center, y_center, width, height
        scores = predictions[:, 4:]  # 类别分数

        # 找到最大分数和类别
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # 过滤低置信度
        keep_indices = confidences > self.conf_threshold
        boxes = boxes[keep_indices]
        confidences = confidences[keep_indices]
        class_ids = class_ids[keep_indices]

        if len(boxes) == 0:
            return []

        # NMS 去重
        boxes_list = []
        for box in boxes:
            x_center, y_center, width, height = box
            x1 = x_center - width / 2
            y1 = y_center - height / 2
            boxes_list.append([x1, y1, width, height])

        indices = cv2.dnn.NMSBoxes(boxes_list, confidences.tolist(), self.conf_threshold, self.iou_threshold)

        # 转换坐标为原始图片坐标
        detections = []
        orig_width, orig_height = original_shape

        for idx in indices:
            i = idx[0] if isinstance(idx, (np.ndarray, list)) else idx

            x_center, y_center, width, height = boxes[i]
            confidence = confidences[i]
            class_id = class_ids[i]

            # 转换为绝对坐标
            x_center_abs = x_center * orig_width
            y_center_abs = y_center * orig_height
            width_abs = width * orig_width
            height_abs = height * orig_height

            # 计算边界框
            x1 = int(x_center_abs - width_abs / 2)
            y1 = int(y_center_abs - height_abs / 2)
            x2 = int(x_center_abs + width_abs / 2)
            y2 = int(y_center_abs + height_abs / 2)

            # 确保坐标在范围内
            x1 = max(0, min(x1, orig_width - 1))
            y1 = max(0, min(y1, orig_height - 1))
            x2 = max(0, min(x2, orig_width - 1))
            y2 = max(0, min(y2, orig_height - 1))

            class_name = self.class_names[class_id] if class_id < len(self.class_names) else f"class_{class_id}"

            detections.append(
                {
                    "box": [x1, y1, x2, y2],
                    "confidence": float(confidence),
                    "class_id": int(class_id),
                    "class_name": class_name,
                    "center": (int(x_center_abs), int(y_center_abs)),
                }
            )

        return detections

    # ==================== 主要检测方法 ====================

    def detect_image(self, image_source: Union[str, np.ndarray]) -> tuple:
        """
        通用检测方法 - 支持多种输入源

        Args:
            image_source: 图像源，可以是:
                         - 图片文件路径 (str)
                         - numpy数组 (np.ndarray)

        Returns:
            tuple: (结果图像, 检测结果列表, 推理时间ms)
        """
        image_array = None
        source_type = "unknown"

        # 处理不同类型的输入源
        if isinstance(image_source, str):
            # 图片文件路径
            source_type = "file"
            image_array = cv2.imread(image_source)
            if image_array is None:
                raise ValueError(f"无法读取图片文件: {image_source}")

        elif isinstance(image_source, np.ndarray):
            # numpy数组
            source_type = "array"
            image_array = image_source

        else:
            raise ValueError(f"不支持的输入类型: {type(image_source)}")

        log.debug(f"🎯 检测来源: {source_type}")

        # 预处理
        input_tensor, original_image, original_shape = self._preprocess_image(image_array)

        # 推理
        start_time = time.time()
        outputs = self.session.run(self.output_names, {self.input_name: input_tensor})
        inference_time = (time.time() - start_time) * 1000

        # 后处理
        detections = self._postprocess_detections(outputs, original_shape)

        # 绘制结果
        result_image = self._draw_detections(original_image, detections)

        return result_image, detections, inference_time

    def detect_batch(self, image_sources: List[Union[str, np.ndarray, int]]) -> List[tuple]:
        """
        批量检测

        Args:
            image_sources: 图像源列表

        Returns:
            List[tuple]: 每个图像的检测结果
        """
        results = []
        for i, source in enumerate(image_sources):
            log.debug(f"\n📦 处理第 {i+1}/{len(image_sources)} 个图像...")
            try:
                result = self.detect_image(source)
                results.append(result)
            except Exception as e:
                log.debug(f"❌ 处理第 {i+1} 个图像失败: {e}")
                results.append((None, [], 0))
        return results

    # ==================== 工具方法 ====================

    def _draw_detections(self, image: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        在图像上绘制检测结果

        Args:
            image: 原始图像
            detections: 检测结果列表

        Returns:
            绘制了检测结果的图像
        """
        result_image = image.copy()
        colors = [
            (0, 255, 0),  # 绿色
            (255, 0, 0),  # 蓝色
            (0, 0, 255),  # 红色
            (255, 255, 0),  # 青色
            (255, 0, 255),  # 紫色
            (0, 255, 255),  # 黄色
        ]

        for detection in detections:
            x1, y1, x2, y2 = detection["box"]
            confidence = detection["confidence"]
            class_name = detection["class_name"]
            class_id = detection["class_id"]

            color = colors[class_id % len(colors)]

            # 绘制边界框
            cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)

            # 绘制标签
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]

            # 标签背景
            cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)

            # 标签文本
            cv2.putText(result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

            # 绘制中心点
            center_x, center_y = detection["center"]
            cv2.circle(result_image, (center_x, center_y), 3, color, -1)

        return result_image

    def print_detections(self, detections: List[Dict]):
        """打印检测结果"""
        log.debug(f"📊 检测到 {len(detections)} 个目标:")
        for i, det in enumerate(detections):
            log.debug(f"  🎯 目标 {i+1}:")
            log.debug(f"     类别: {det['class_name']}")
            log.debug(f"     置信度: {det['confidence']:.4f}")
            log.debug(f"     位置: {det['box']}")
            log.debug(f"     中心点: {det['center']}")

    def save_result(self, image: np.ndarray, filename: str = "detection_result.jpg"):
        """保存结果图像"""
        cv2.imwrite(filename, image)
        log.debug(f"💾 结果已保存为: {filename}")
