"""
Widget for displaying the image.
"""
import logging
from PySide6.QtWidgets import QScrollArea, QLabel, QMessageBox
from PySide6.QtCore import Qt, QRect, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QColor
from ..image import processing
from ..annotations.annotation import Annotation
from ..annotations import storage

logger = logging.getLogger(__name__)

HANDLE_SIZE = 8 # Size of the resize handles

class _ImageLabel(QLabel):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self._pixmap = None

        self.selected_annotation = None
        self.selection_handle = None # 'body', 'top-left', 'top-right', 'bottom-left', 'bottom-right'
        self.dragging = False
        self.last_mouse_pos = QPoint()

    def set_pixmap(self, pixmap):
        self._pixmap = pixmap
        if self._pixmap is None:
            self.setText("Open a folder to start annotating.")
        else:
            self.setText("")
        self.selected_annotation = None # Clear selection on new image
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

    def _yolo_to_pixel_rect(self, bbox, img_w, img_h):
        x_center, y_center, norm_w, norm_h = bbox
        w = norm_w * img_w
        h = norm_h * img_h
        x = x_center * img_w - w / 2
        y = y_center * img_h - h / 2
        return QRect(int(x), int(y), int(w), int(h))

    def _pixel_rect_to_yolo(self, rect, img_w, img_h):
        x_center = (rect.x() + rect.width() / 2) / img_w
        y_center = (rect.y() + rect.height() / 2) / img_h
        norm_w = rect.width() / img_w
        norm_h = rect.height() / img_h
        return [x_center, y_center, norm_w, norm_h]

    def _get_handle_rects(self, pixel_rect):
        handles = {}
        hs = HANDLE_SIZE // 2
        handles['top-left'] = QRect(pixel_rect.topLeft().x() - hs, pixel_rect.topLeft().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['top-right'] = QRect(pixel_rect.topRight().x() - hs, pixel_rect.topRight().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['bottom-left'] = QRect(pixel_rect.bottomLeft().x() - hs, pixel_rect.bottomLeft().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['bottom-right'] = QRect(pixel_rect.bottomRight().x() - hs, pixel_rect.bottomRight().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        return handles

    def _hit_test(self, mouse_pos_img_coords):
        if not self._pixmap:
            return None, None

        img_w = self._pixmap.width()
        img_h = self._pixmap.height()

        for annotation in reversed(self.parent_view.annotations): # Check top-most annotations first
            pixel_rect = self._yolo_to_pixel_rect(annotation.bbox, img_w, img_h)
            
            # Check handles first
            handles = self._get_handle_rects(pixel_rect)
            for handle_name, handle_rect in handles.items():
                if handle_rect.contains(mouse_pos_img_coords):
                    return annotation, handle_name
            
            # Check body of the bounding box
            if pixel_rect.contains(mouse_pos_img_coords):
                return annotation, 'body'
        
        return None, None

    def _clamp_rect_to_image(self, rect, img_w, img_h, preserve_size=False):
        x = rect.x()
        y = rect.y()
        w = rect.width()
        h = rect.height()

        if preserve_size:
            # Clamp position while preserving size
            x = max(0, min(x, img_w - w))
            y = max(0, min(y, img_h - h))
        else:
            # Clamp position and size (for resizing or initial drawing)
            x = max(0, x)
            y = max(0, y)
            w = min(w, img_w - x)
            h = min(h, img_h - y)
        
        return QRect(x, y, w, h)

    def mousePressEvent(self, event):
        mouse_pos_img_coords = self.get_image_coords(event.pos())
        if not mouse_pos_img_coords:
            return

        if self.parent_view.tool == "bbox" and event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = mouse_pos_img_coords
            self.end_point = mouse_pos_img_coords
            logger.debug(f"Mouse press: start drawing at {self.start_point}")
            self.update()
        elif self.parent_view.tool == "select" and event.button() == Qt.LeftButton:
            self.selected_annotation, self.selection_handle = self._hit_test(mouse_pos_img_coords)
            if self.selected_annotation:
                self.dragging = True
                self.last_mouse_pos = mouse_pos_img_coords
                logger.debug(f"Selected annotation ID: {self.selected_annotation.id}, handle: {self.selection_handle}")
            else:
                self.selected_annotation = None # Clicked outside, deselect
                logger.debug("Deselected annotation.")
            self.update()

    def mouseMoveEvent(self, event):
        mouse_pos_img_coords = self.get_image_coords(event.pos())
        if not mouse_pos_img_coords:
            return

        if self.drawing:
            self.end_point = mouse_pos_img_coords
            self.update()
        elif self.dragging and self.selected_annotation:
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()

            current_pixel_rect = self._yolo_to_pixel_rect(self.selected_annotation.bbox, img_w, img_h)
            new_pixel_rect = QRect(current_pixel_rect)

            if self.selection_handle == 'body':
                delta_x = mouse_pos_img_coords.x() - self.last_mouse_pos.x()
                delta_y = mouse_pos_img_coords.y() - self.last_mouse_pos.y()
                new_pixel_rect.translate(delta_x, delta_y)
                new_pixel_rect = self._clamp_rect_to_image(new_pixel_rect, img_w, img_h, preserve_size=True)
            else: # Resizing
                x1 = current_pixel_rect.left()
                y1 = current_pixel_rect.top()
                x2 = current_pixel_rect.right()
                y2 = current_pixel_rect.bottom()

                # Determine the fixed point and update the moving point
                if self.selection_handle == 'top-left':
                    x1 = mouse_pos_img_coords.x()
                    y1 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'top-right':
                    x2 = mouse_pos_img_coords.x()
                    y1 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'bottom-left':
                    x1 = mouse_pos_img_coords.x()
                    y2 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'bottom-right':
                    x2 = mouse_pos_img_coords.x()
                    y2 = mouse_pos_img_coords.y()
                
                # Create a new QRect from the updated corners, ensuring it's normalized
                new_pixel_rect = QRect(QPoint(x1, y1), QPoint(x2, y2)).normalized()
                
                # Clamp the new rectangle to image boundaries
                new_pixel_rect = self._clamp_rect_to_image(new_pixel_rect, img_w, img_h, preserve_size=False)
            
            self.selected_annotation.bbox = self._pixel_rect_to_yolo(new_pixel_rect, img_w, img_h)
            self.last_mouse_pos = mouse_pos_img_coords
            self.update()

    def mouseReleaseEvent(self, event):
        mouse_pos_img_coords = self.get_image_coords(event.pos())
        if not mouse_pos_img_coords:
            return

        if self.drawing:
            self.drawing = False
            self.end_point = mouse_pos_img_coords
            logger.debug(f"Mouse release: stop drawing at {self.end_point}")

            rect = QRect(self.start_point, self.end_point).normalized()
            
            if self._pixmap:
                img_w = self._pixmap.width()
                img_h = self._pixmap.height()

                rect = self._clamp_rect_to_image(rect, img_w, img_h, preserve_size=False)
                bbox = self._pixel_rect_to_yolo(rect, img_w, img_h)

                if self.parent_view.current_image_path:
                    try:
                        conn = storage.create_connection("annotations.db")
                        if conn:
                            image_id = storage.get_or_create_image(conn, self.parent_view.current_image_path)
                            if image_id is None:
                                raise ConnectionError("Failed to get or create image record.")

                            new_annotation = Annotation(id=None, image_id=image_id, class_id=0, bbox=bbox)
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
        elif self.dragging and self.selected_annotation:
            self.dragging = False
            self.selection_handle = None
            # Save changes to DB
            if self.parent_view.current_image_path:
                try:
                    conn = storage.create_connection("annotations.db")
                    if conn:
                        storage.update_annotation(conn, self.selected_annotation)
                        conn.close()
                        self.parent_view.annotation_changed.emit(self.selected_annotation)
                except Exception as e:
                    logger.error(f"Error updating annotation: {e}")
                    QMessageBox.critical(self.parent_view, "Error", f"Could not update the annotation: {e}")
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

        img_w = self._pixmap.width()
        img_h = self._pixmap.height()

        def to_widget_coords_from_pixels(image_point_tuple):
            px = image_point_tuple[0] * target_size.width() / pixmap_size.width() + offset_x
            py = image_point_tuple[1] * target_size.height() / pixmap_size.height() + offset_y
            return QPoint(int(px), int(py))

        for annotation in self.parent_view.annotations:
            x_center, y_center, norm_w, norm_h = annotation.bbox
            
            w = norm_w * img_w
            h = norm_h * img_h
            x = x_center * img_w - w / 2
            y = y_center * img_h - h / 2

            pixel_rect = QRect(int(x), int(y), int(w), int(h))
            widget_rect = QRect(to_widget_coords_from_pixels(pixel_rect.topLeft().toTuple()),
                                to_widget_coords_from_pixels(pixel_rect.bottomRight().toTuple()))

            if annotation == self.selected_annotation:
                painter.setPen(QPen(QColor(0, 0, 255), 2, Qt.SolidLine)) # Blue for selected
                painter.drawRect(widget_rect)
                # Draw handles
                handles = self._get_handle_rects(pixel_rect)
                for handle_name, handle_rect_img_coords in handles.items():
                    handle_rect_widget_coords = QRect(to_widget_coords_from_pixels(handle_rect_img_coords.topLeft().toTuple()),
                                                      to_widget_coords_from_pixels(handle_rect_img_coords.bottomRight().toTuple()))
                    painter.fillRect(handle_rect_widget_coords, QColor(0, 255, 0)) # Green handles
            else:
                painter.setPen(QPen(Qt.red, 2, Qt.SolidLine)) # Red for unselected
                painter.drawRect(widget_rect)

        if self.drawing:
            p1 = to_widget_coords_from_pixels((self.start_point.x(), self.start_point.y()))
            p2 = to_widget_coords_from_pixels((self.end_point.x(), self.end_point.y()))
            rect = QRect(p1, p2)
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawRect(rect)

class ImageView(QScrollArea):
    """
    Widget to display the image. It's a scroll area containing a label.
    """
    annotation_added = Signal(object)
    annotation_changed = Signal(object) # New signal

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
        self.image_label.selected_annotation = None # Deselect when changing tool
        self.image_label.update()

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
