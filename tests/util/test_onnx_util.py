import cv2
import numpy as np
from gas.util.onnx_util import YOLOONNXDetector

onnx_path = "best.onnx"
class_names = ["ui_quit", "ui_menu", "ui_lv"]
image_path = "test.png"


def test_detector_image():
    """使用示例"""
    # 1. 初始化检测器
    detector = YOLOONNXDetector(
        onnx_path=onnx_path,
        class_names=class_names,
        conf_threshold=0.1,
    )

    print("=" * 50)
    print("YOLO ONNX 检测器演示")
    print("=" * 50)

    # 2. 检测图片文件
    print("\n 📁 检测图片文件:")
    try:
        result_img, detections, inference_time = detector.detect_image(image_path)
        detector.print_detections(detections)
        print(f"   推理时间: {inference_time:.2f}ms")

        # 显示结果
        cv2.imshow("文件检测结果", result_img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"   文件检测失败: {e}")


def test_detector_array():
    """使用示例"""
    # 1. 初始化检测器
    detector = YOLOONNXDetector(
        onnx_path=onnx_path,
        class_names=class_names,
        conf_threshold=0.1,
    )

    print("=" * 50)
    print("YOLO ONNX 检测器演示")
    print("=" * 50)

    print("\n2. 🎨 检测 numpy 数组:")
    try:
        # 创建一个测试图像
        test_array = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result_img, detections, inference_time = detector.detect_image(test_array)
        detector.print_detections(detections)
    except Exception as e:
        print(f"   数组检测失败: {e}")

    print("✨ 演示完成!")
