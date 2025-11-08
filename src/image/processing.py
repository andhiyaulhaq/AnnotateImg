"""
Image loading and manipulation.
"""
import logging
import cv2
from PySide6.QtGui import QPixmap, QImage

logger = logging.getLogger(__name__)

def load_image_as_pixmap(image_path):
    """
    Load an image from a file path and return a QPixmap.
    """
    try:
        logger.info(f"Attempting to load image: {image_path}")
        cv_image = cv2.imread(image_path)
        if cv_image is not None:
            height, width, channel = cv_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            logger.info(f"Successfully loaded image: {image_path}")
            return QPixmap.fromImage(q_image)
        else:
            logger.error(f"Failed to load image with OpenCV: {image_path}")
            return None
    except Exception as e:
        logger.error(f"An error occurred while loading image {image_path}: {e}")
        return None
