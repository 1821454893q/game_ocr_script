import cv2
import numpy as np
from gas.util.onnx_util import YOLOONNXDetector

onnx_path = "tests/resource/best.onnx"
input_image_path = "tests/resource/test.png"
output_image_path = "tests/resource/result.png"
class_name = ['退出', '菜单', '等级', '返回', '每日', '任务', '历练', '委托', '再次进行', '退出委托', '加载中', '红色指引标', '黄色指引标', '夜航20', '夜航30', '夜航40', '夜航50', '夜航55', '夜航60', '夜航65', '夜航70', '梦魇残生', '歧路足音', '夜航80', '确认选择', '放弃', '操作']

def test_detector():
    """使用示例"""
    # 初始化检测器
    detector = YOLOONNXDetector(
        model_path=onnx_path,  # 替换为你的ONNX模型路径
        conf_threshold=0.8,
        class_names=class_name,
        input_size=(1280, 1280),
        providers=["CPUExecutionProvider"],
    )

    # 检测单张图片
    result_img, detections, ms = detector.detect(input_image_path)

    # 打印结果
    detector.print_detections(detections)
    print(f"推理时间: {ms:.2f}ms")
    cv2.imshow("result", result_img)
    cv2.waitKey(0)