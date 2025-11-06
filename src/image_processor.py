import cv2
import numpy as np
from typing import List, Tuple

from .logger import get_logger

logger = get_logger()


class ImageProcessor:
    """图像处理工具"""

    @staticmethod
    def crop_by_polygon(image: np.ndarray, polygon) -> np.ndarray:
        """根据多边形裁剪图像"""
        try:
            if isinstance(polygon, np.ndarray):
                polygon = polygon.tolist()

            x_coords = [point[0] for point in polygon]
            y_coords = [point[1] for point in polygon]

            left = min(x_coords)
            top = min(y_coords)
            right = max(x_coords)
            bottom = max(y_coords)

            # 边界检查
            height, width = image.shape[:2]
            left = max(0, left)
            top = max(0, top)
            right = min(width, right)
            bottom = min(height, bottom)

            if left >= right or top >= bottom:
                return np.array([])

            cropped = image[top:bottom, left:right]
            return cropped

        except Exception as e:
            logger.error(f"图像裁剪失败: {e}")
            return np.array([])

    @staticmethod
    def get_bounding_box(polygon) -> Tuple[int, int, int, int]:
        """获取边界框"""
        if isinstance(polygon, np.ndarray):
            polygon = polygon.tolist()

        x_coords = [point[0] for point in polygon]
        y_coords = [point[1] for point in polygon]

        left = min(x_coords)
        top = min(y_coords)
        right = max(x_coords)
        bottom = max(y_coords)

        return left, top, right, bottom

    @staticmethod
    def get_center(bbox: Tuple[int, int, int, int]) -> Tuple[int, int]:
        """获取中心点坐标"""
        left, top, right, bottom = bbox
        center_x = (left + right) // 2
        center_y = (top + bottom) // 2
        return center_x, center_y
