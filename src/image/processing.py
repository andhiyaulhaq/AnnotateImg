"""
Image loading and manipulation.
"""
import cv2
from PySide6.QtGui import QPixmap, QImage

def load_image(image_path):
    """
    Load an image from a file path using OpenCV.
    """
    return cv2.imread(image_path)

def load_image_as_pixmap(image_path):
    """
    Load an image from a file path and return a QPixmap.
    """
    cv_image = load_image(image_path)
    if cv_image is not None:
        height, width, channel = cv_image.shape
        bytes_per_line = 3 * width
        q_image = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        return QPixmap.fromImage(q_image)
    return None
