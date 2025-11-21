import cv2
import numpy as np
from gas.util.onnx_util import YOLOONNXDetector

onnx_path = "tests/resource/best.onnx"
class_names = ["ui_quit", "ui_menu", "ui_lv"]
input_image_path = "tests/resource/test.png"
output_image_path = "tests/resource/result.png"


def test_detector():
    """使用示例"""
    # 初始化检测器
    detector = YOLOONNXDetector(
        model_path=onnx_path,  # 替换为你的ONNX模型路径
        class_names=class_names,  # 替换为你的类别名称
        conf_threshold=0.8,
        input_size=(640, 640),
        providers=["CPUExecutionProvider"],
    )

    # 检测单张图片
    img = cv2.imread(input_image_path)
    result_img, detections, ms = detector.detect(img)

    # 打印结果
    detector.print_detections(detections)
    print(f"推理时间: {ms:.2f}ms")
    cv2.imshow("result", result_img)
    cv2.waitKey(0)
