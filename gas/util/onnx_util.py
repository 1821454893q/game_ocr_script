# onnx_util.py
import onnxruntime as ort
import cv2
import numpy as np
import time
from pathlib import Path
from typing import Union, List, Dict, Tuple, Optional
from gas.logger import get_logger

log = get_logger()


class YOLOONNXDetector:
    """
    兼容 YOLOv8 / YOLOv10 / YOLOv11 系列 ONNX 模型的检测器
    """

    def __init__(
        self,
        model_path: Union[str, Path],
        class_names: Optional[List[str]] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        input_size: Tuple[int, int] = (640, 640),
        providers: Optional[List[str]] = None,
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.input_width, self.input_height = input_size

        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {model_path}")

        # 执行提供者CPU
        if providers is None:
            providers = ["CPUExecutionProvider"]

        log.debug(f"Loading ONNX model: {model_path}")
        self.session = ort.InferenceSession(str(self.model_path), providers=providers)

        # 输入/输出信息
        input_info = self.session.get_inputs()[0]
        self.input_name = input_info.name
        self.input_shape = input_info.shape  # [1, 3, H, W] or dynamic

        # 自动获取模型实际输入尺寸（支持动态轴）
        if self.input_shape[2] not in (-1, 0) and self.input_shape[3] not in (-1, 0):
            self.input_height = self.input_shape[2]
            self.input_width = self.input_shape[3]
            log.debug(f"Model input size from ONNX: {self.input_width}x{self.input_height}")
        else:
            log.debug(f"Using user specified input size: {self.input_width}x{self.input_height}")

        self.class_names = class_names or [f"class_{i}" for i in range(80)]
        log.debug(f"Loaded {len(self.class_names)} classes")

    # ==================== 正确的 Letterbox 预处理 ====================
    def _letterbox(
        self, img: np.ndarray, new_shape=(640, 640), color=(114, 114, 114)
    ) -> Tuple[np.ndarray, float, Tuple[int, int]]:
        """
        Letterbox resize (保持比例 + 填充灰边)，返回：
        - resized + padded image
        - ratio
        - (pad_w, pad_h)
        """
        shape = img.shape[:2]  # h, w
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        r = min(new_shape[1] / shape[1], new_shape[0] / shape[0])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))

        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]
        dw /= 2
        dh /= 2

        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)

        return img, r, (dw, dh)

    def _preprocess(self, image: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """
        标准 YOLO ONNX 预处理
        """
        img = image.copy()
        original_shape = img.shape[:2]  # (h, w)

        # letterbox
        img_resized, ratio, (dw, dh) = self._letterbox(img, (self.input_height, self.input_width))

        # BGR -> RGB, HWC -> CHW, /255, add batch dim
        img_input = img_resized[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB + HWC to CHW
        img_input = np.ascontiguousarray(img_input).astype(np.float32) / 255.0
        img_input = img_input[None]  # (1, 3, H, W)

        meta = {
            "original_shape": original_shape,
            "resized_shape": (self.input_height, self.input_width),
            "ratio": ratio,
            "pad": (dw, dh),
        }
        return img_input, meta

    # ==================== 正确的后处理（支持 YOLOv8/v10/v11） ====================
    def _postprocess(self, preds: np.ndarray, meta: Dict) -> List[Dict]:
        """
        完全修复版后处理 - 兼容 YOLOv8/v10/v11 所有官方 ONNX 模型
        """
        # preds: List[np.ndarray]，通常只有1个输出，shape = (1, 84, 8400) 或 (1, 116, 8400) 等
        pred = preds[0]  # (1, 84, 8400)

        # 1. 去除 batch 维度
        pred = pred[0]  # (84, 8400) 或 (4+nc, 8400)

        # 2. 正确转置：从 (channels, num_boxes) -> (num_boxes, channels)
        pred = pred.transpose(1, 0)  # (8400, 84)

        # 3. 分离 boxes 和 scores
        boxes = pred[:, :4]  # (8400, 4)  xywh 中心坐标
        scores = pred[:, 4:]  # (8400, nc)

        # 4. 取最大置信度及其类别
        class_conf = np.max(scores, axis=1)  # (8400,)
        class_ids = np.argmax(scores, axis=1)  # (8400,)

        # 5. 置信度过滤（关键：这里 mask 长度 = 8400，和 boxes 的第0维匹配！）
        mask = class_conf > self.conf_threshold
        if not np.any(mask):
            return []

        boxes = boxes[mask]
        class_conf = class_conf[mask]
        class_ids = class_ids[mask]

        # 6. 转为角点坐标
        x = boxes[:, 0]
        y = boxes[:, 1]
        w = boxes[:, 2]
        h = boxes[:, 3]
        x1 = x - w / 2
        y1 = y - h / 2
        x2 = x + w / 2
        y2 = y + h / 2

        # 7. 去除 letterbox padding 并缩放到原图
        ratio = meta["ratio"]
        dw, dh = meta["pad"]
        x1 = (x1 - dw) / ratio
        y1 = (y1 - dh) / ratio
        x2 = (x2 - dw) / ratio
        y2 = (y2 - dh) / ratio

        # 8. NMS（注意 cv2.dnn.NMSBoxes 需要 [x,y,w,h] 格式）
        nms_boxes = np.stack([x1, y1, x2 - x1, y2 - y1], axis=1).tolist()
        indices = cv2.dnn.NMSBoxes(
            bboxes=nms_boxes,
            scores=class_conf.tolist(),
            score_threshold=self.conf_threshold,
            nms_threshold=self.iou_threshold,
        )

        if len(indices) == 0:
            return []

        # OpenCV >=4.5.4 返回的是 tuple，旧版返回 ndarray
        if isinstance(indices, tuple):
            indices = indices[0]
        indices = np.array(indices).flatten()

        # 9. 组装最终结果
        detections = []
        orig_h, orig_w = meta["original_shape"]

        for i in indices:
            conf = float(class_conf[i])
            cls_id = int(class_ids[i])
            box = [
                max(0, int(x1[i])),
                max(0, int(y1[i])),
                min(orig_w, int(x2[i])),
                min(orig_h, int(y2[i])),
            ]
            detections.append(
                {
                    "box": box,
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}",
                    "center": ((box[0] + box[2]) // 2, (box[1] + box[3]) // 2),
                }
            )

        return detections

    # ==================== 主要接口 ====================
    def detect(
        self,
        source: Union[str, Path, np.ndarray],
        save_path: Optional[Union[str, Path]] = None,
        draw: bool = True,
    ) -> Tuple[np.ndarray, List[Dict], float]:
        """
        单张图像检测
        """
        if isinstance(source, (str, Path)):
            img = cv2.imread(str(source))
            if img is None:
                raise FileNotFoundError(f"Cannot read image: {source}")
        else:
            img = source

        input_tensor, meta = self._preprocess(img)

        start_time = time.time()
        outputs = self.session.run(None, {self.input_name: input_tensor})
        infer_ms = (time.time() - start_time) * 1000

        detections = self._postprocess(outputs, meta)

        result_img = img.copy()
        if draw:
            result_img = self.draw_detections(result_img, detections)

        if save_path:
            cv2.imwrite(str(save_path), result_img)
            log.debug(f"Result saved to {save_path}")

        return result_img, detections, infer_ms

    def draw_detections(self, img: np.ndarray, detections: List[Dict]) -> np.ndarray:
        colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255)]
        for det in detections:
            x1, y1, x2, y2 = det["box"]
            conf = det["confidence"]
            name = det["class_name"]
            color = colors[det["class_id"] % len(colors)]

            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f"{name} {conf:.2f}"
            (w, h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(img, (x1, y1 - 20), (x1 + w, y1), color, -1)
            cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            # 中心点
            cx, cy = det["center"]
            cv2.circle(img, (cx, cy), 4, color, -1)

        return img

    def print_detections(self, detections: List[Dict]):
        log.debug(f"Detected {len(detections)} objects:")
        for i, d in enumerate(detections):
            log.debug(f"  [{i+1}] {d['class_name']:15} {d['confidence']:.3f} {d['box']}")
