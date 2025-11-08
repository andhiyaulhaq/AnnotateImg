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
        self._pixmap = None

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        if self._pixmap is None:
            self.setText("Open a folder to start annotating.")
        else:
            self.setText("")
        self.update()

    def get_image_coords(self, widget_pos):
        if not self._pixmap:
            return None

        pixmap_size = self._pixmap.size()
        label_size = self.size()

        scaled_size = pixmap_size.scaled(label_size, Qt.KeepAspectRatio)

        offset_x = (label_size.width() - scaled_size.width()) / 2
        offset_y = (label_size.height() - scaled_size.height()) / 2

        if not (offset_x <= widget_pos.x() < offset_x + scaled_size.width() and
                offset_y <= widget_pos.y() < offset_y + scaled_size.height()):
            return None

        image_x = (widget_pos.x() - offset_x) * pixmap_size.width() / scaled_size.width()
        image_y = (widget_pos.y() - offset_y) * pixmap_size.height() / scaled_size.height()

        return QPoint(int(image_x), int(image_y))

    def mousePressEvent(self, event):
        if self.parent_view.tool == "bbox" and event.button() == Qt.LeftButton:
            image_pos = self.get_image_coords(event.pos())
            if image_pos:
                self.drawing = True
                self.start_point = image_pos
                self.end_point = image_pos
                logger.debug(f"Mouse press: start drawing at {self.start_point}")
                self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            image_pos = self.get_image_coords(event.pos())
            if image_pos:
                self.end_point = image_pos
                self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            image_pos = self.get_image_coords(event.pos())
            if image_pos:
                self.end_point = image_pos
            logger.debug(f"Mouse release: stop drawing at {self.end_point}")
            
            points = [(self.start_point.x(), self.start_point.y()), (self.end_point.x(), self.end_point.y())]
            
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
        painter = QPainter(self)

        if not self._pixmap:
            super().paintEvent(event)
            return

        label_size = self.size()
        pixmap_size = self._pixmap.size()
        
        target_size = pixmap_size.scaled(label_size, Qt.KeepAspectRatio)
        
        offset_x = (label_size.width() - target_size.width()) / 2
        offset_y = (label_size.height() - target_size.height()) / 2
        
        target_rect = QRect(int(offset_x), int(offset_y), target_size.width(), target_size.height())

        painter.drawPixmap(target_rect, self._pixmap)

        pen = QPen(Qt.red, 2, Qt.SolidLine)
        painter.setPen(pen)

        def to_widget_coords(image_point):
            x = image_point[0] * target_size.width() / pixmap_size.width() + offset_x
            y = image_point[1] * target_size.height() / pixmap_size.height() + offset_y
            return QPoint(int(x), int(y))

        for annotation in self.parent_view.annotations:
            if len(annotation.points) == 2:
                p1 = to_widget_coords(annotation.points[0])
                p2 = to_widget_coords(annotation.points[1])
                painter.drawRect(QRect(p1, p2))

        if self.drawing:
            p1 = to_widget_coords((self.start_point.x(), self.start_point.y()))
            p2 = to_widget_coords((self.end_point.x(), self.end_point.y()))
            rect = QRect(p1, p2)
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
            self.image_label.set_pixmap(None)
            self.annotations = []
            return

        self.current_image_path = image_path
        try:
            self._pixmap = processing.load_image_as_pixmap(image_path)
            if self._pixmap:
                self.image_label.set_pixmap(self._pixmap)
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
