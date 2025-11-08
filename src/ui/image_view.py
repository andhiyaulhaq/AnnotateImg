"""
Widget for displaying the image.
"""
import logging
from PySide6.QtWidgets import QScrollArea, QLabel, QMessageBox
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QPen
from ..image import processing
from ..annotations.annotation import Annotation
from ..annotations import storage

logger = logging.getLogger(__name__)

class _ImageLabel(QLabel):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()

    def mousePressEvent(self, event):
        if self.parent_view.tool == "bbox" and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = event.pos()
            logger.debug(f"Mouse press: start drawing at {self.start_point}")
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            logger.debug(f"Mouse release: stop drawing at {self.end_point}")
            
            points = [(self.start_point.x(), self.start_point.y()), (self.end_point.x(), self.end_point.y())]
            
            if self.parent_view._pixmap:
                pixmap_rect = self.parent_view._pixmap.rect()
                points = [
                    (
                        max(0, min(p[0], pixmap_rect.width())),
                        max(0, min(p[1], pixmap_rect.height()))
                    )
                    for p in points
                ]

            if self.parent_view.current_image_path:
                try:
                    conn = storage.create_connection("annotations.db")
                    if conn:
                        image_id = storage.get_or_create_image(conn, self.parent_view.current_image_path)
                        if image_id is None:
                            raise ConnectionError("Failed to get or create image record.")

                        new_annotation = Annotation(id=None, image_id=image_id, label="bbox", points=points)
                        anno_id = storage.create_annotation(conn, new_annotation)
                        if anno_id is None:
                            raise ConnectionError("Failed to create annotation record.")
                            
                        new_annotation.id = anno_id
                        
                        self.parent_view.annotations.append(new_annotation)
                        self.parent_view.annotation_added.emit(new_annotation)
                        
                        conn.close()
                except Exception as e:
                    logger.error(f"Error saving annotation: {e}")
                    QMessageBox.critical(self.parent_view, "Error", f"Could not save the annotation: {e}")

            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        pen = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen)

        for annotation in self.parent_view.annotations:
            if len(annotation.points) == 2:
                p1 = QPoint(annotation.points[0][0], annotation.points[0][1])
                p2 = QPoint(annotation.points[1][0], annotation.points[1][1])
                painter.drawRect(QRect(p1, p2))

        if self.drawing:
            rect = QRect(self.start_point, self.end_point)
            painter.drawRect(rect)

class ImageView(QScrollArea):
    """
    Widget to display the image. It's a scroll area containing a label.
    """
    annotation_added = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.image_label = _ImageLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image_label)
        self.image_label.setText("Open a folder to start annotating.")
        self._pixmap = None
        self.tool = None
        self.current_image_path = None
        self.annotations = []
        logger.info("Image view initialized.")

    def set_tool(self, tool):
        self.tool = tool

    def set_image(self, image_path):
        """
        Load and display an image from a file path.
        """
        if image_path is None:
            self.current_image_path = None
            self._pixmap = None
            self.image_label.setText("Open a folder to start annotating.")
            self.annotations = []
            self.image_label.update()
            return

        self.current_image_path = image_path
        try:
            self._pixmap = processing.load_image_as_pixmap(image_path)
            if self._pixmap:
                self.image_label.setPixmap(self._pixmap)
                logger.info(f"Image loaded: {image_path}")
                self.load_annotations()
            else:
                self.image_label.setText(f"Could not load image: {image_path}")
                logger.error(f"Failed to load image: {image_path}")
                self.annotations = []
        except Exception as e:
            logger.error(f"Exception while loading image {image_path}: {e}")
            QMessageBox.critical(self, "Error", f"Could not load the image: {e}")
            self.annotations = []

        self.image_label.update()

    def load_annotations(self):
        """
        Load annotations for the current image.
        """
        self.annotations = []
        if self.current_image_path:
            try:
                conn = storage.create_connection("annotations.db")
                if conn:
                    image_id = storage.get_image_id_by_path(conn, self.current_image_path)
                    if image_id:
                        self.annotations = storage.get_annotations_for_image(conn, image_id)
                    conn.close()
            except Exception as e:
                logger.error(f"Error loading annotations: {e}")
                QMessageBox.warning(self, "Warning", f"Could not load annotations: {e}")
        self.image_label.update()

    def resizeEvent(self, event):
        """
        Handle resize events to scale the image.
        """
        super().resizeEvent(event)
