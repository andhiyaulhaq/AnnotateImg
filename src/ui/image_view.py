"""
Widget for displaying the image.
"""
from PySide6.QtWidgets import QScrollArea, QLabel
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QPen
from ..image import processing

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
            self.update()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            # TODO: Save annotation
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drawing:
            painter = QPainter(self)
            pen = QPen(Qt.red, 2, Qt.SolidLine)
            painter.setPen(pen)
            rect = QRect(self.start_point, self.end_point)
            painter.drawRect(rect)

class ImageView(QScrollArea):
    """
    Widget to display the image. It's a scroll area containing a label.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.image_label = _ImageLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image_label)
        self.image_label.setText("Open a folder to start annotating.")
        self._pixmap = None
        self.tool = None

    def set_tool(self, tool):
        self.tool = tool

    def set_image(self, image_path):
        """
        Load and display an image from a file path.
        """
        self._pixmap = processing.load_image_as_pixmap(image_path)
        if self._pixmap:
            self.image_label.setPixmap(self._pixmap)
        else:
            self.image_label.setText(f"Could not load image: {image_path}")

    def resizeEvent(self, event):
        """
        Handle resize events to scale the image.
        """
        # Scaling is handled by the QScrollArea with setWidgetResizable(True)
        super().resizeEvent(event)
