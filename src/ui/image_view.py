"""
Widget for displaying the image.
"""
import logging
from PySide6.QtWidgets import QScrollArea, QLabel, QMessageBox, QInputDialog
from PySide6.QtCore import Qt, QRect, QPoint, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QPen, QColor, QFont
from ..image import processing
from ..annotations.annotation import Annotation
from ..annotations import storage

logger = logging.getLogger(__name__)

HANDLE_SIZE = 8 # Size of the resize handles
HANDLE_MARGIN = 5 # Margin around edges for resize handles

SELECTED_COLOR = QColor(0, 0, 255)  # Blue
UNSELECTED_COLOR = QColor(255, 0, 0) # Red

class _ImageLabel(QLabel):
    def __init__(self, parent_view):
        super().__init__(parent_view)
        self.parent_view = parent_view
        self.drawing = False
        self.start_point = QPointF()
        self.end_point = QPointF()
        self._pixmap = None

        self.selected_annotation = None
        self.selection_handle = None # 'body', 'top-left', 'top-right', 'bottom-left', 'bottom-right', 'top', 'bottom', 'left', 'right'
        self.dragging = False
        self.last_mouse_pos = QPointF()
        self.setMouseTracking(True) # Enable mouse tracking
        self.setFocusPolicy(Qt.StrongFocus) # Enable keyboard events

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

        return QPointF(image_x, image_y)

    def _norm_to_pixel_rect(self, annotation, img_w, img_h):
        x1_pixel = annotation.x1 * img_w
        y1_pixel = annotation.y1 * img_h
        x2_pixel = annotation.x2 * img_w
        y2_pixel = annotation.y2 * img_h
        return QRectF(x1_pixel, y1_pixel, x2_pixel - x1_pixel, y2_pixel - y1_pixel)

    def _pixel_to_norm_rect(self, pixel_rect_f, img_w, img_h):
        x1_norm = pixel_rect_f.left() / img_w
        y1_norm = pixel_rect_f.top() / img_h
        x2_norm = (pixel_rect_f.left() + pixel_rect_f.width()) / img_w
        y2_norm = (pixel_rect_f.top() + pixel_rect_f.height()) / img_h
        return [x1_norm, y1_norm, x2_norm, y2_norm]

    def _get_handle_rects(self, pixel_rect_f):
        handles = {}
        hs = HANDLE_SIZE // 2
        hm = HANDLE_MARGIN

        # Corner handles
        handles['top-left'] = QRectF(pixel_rect_f.topLeft().x() - hs, pixel_rect_f.topLeft().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['top-right'] = QRectF(pixel_rect_f.topRight().x() - hs, pixel_rect_f.topRight().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['bottom-left'] = QRectF(pixel_rect_f.bottomLeft().x() - hs, pixel_rect_f.bottomLeft().y() - hs, HANDLE_SIZE, HANDLE_SIZE)
        handles['bottom-right'] = QRectF(pixel_rect_f.bottomRight().x() - hs, pixel_rect_f.bottomRight().y() - hs, HANDLE_SIZE, HANDLE_SIZE)

        # Edge handles
        handles['top'] = QRectF(pixel_rect_f.left() + hs, pixel_rect_f.top() - hm, pixel_rect_f.width() - 2 * hs, 2 * hm)
        handles['bottom'] = QRectF(pixel_rect_f.left() + hs, pixel_rect_f.bottom() - hm, pixel_rect_f.width() - 2 * hs, 2 * hm)
        handles['left'] = QRectF(pixel_rect_f.left() - hm, pixel_rect_f.top() + hs, 2 * hm, pixel_rect_f.height() - 2 * hs)
        handles['right'] = QRectF(pixel_rect_f.right() - hm, pixel_rect_f.top() + hs, 2 * hm, pixel_rect_f.height() - 2 * hs)
        
        return handles

    def _hit_test(self, mouse_pos_img_coords):
        if not self._pixmap:
            return None, None

        img_w = self._pixmap.width()
        img_h = self._pixmap.height()

        for annotation in reversed(self.parent_view.annotations): # Check top-most annotations first
            pixel_rect_f = self._norm_to_pixel_rect(annotation, img_w, img_h)
            
            # Check handles first
            handles = self._get_handle_rects(pixel_rect_f)
            for handle_name, handle_rect_f in handles.items():
                if handle_rect_f.contains(mouse_pos_img_coords):
                    return annotation, handle_name
            
            # Check body of the bounding box
            if pixel_rect_f.contains(mouse_pos_img_coords):
                return annotation, 'body'
        
        return None, None

    def _clamp_rect_to_image(self, rect_f, img_w, img_h, preserve_size=False):
        x = rect_f.x()
        y = rect_f.y()
        w = rect_f.width()
        h = rect_f.height()

        if preserve_size:
            # Clamp position while preserving size
            x = max(0.0, min(x, img_w - w))
            y = max(0.0, min(y, img_h - h))
        else:
            # Clamp position and size (for resizing or initial drawing)
            x = max(0.0, x)
            y = max(0.0, y)
            w = min(w, img_w - x)
            h = min(h, img_h - y)
        
        return QRectF(x, y, w, h)

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
                self.parent_view.annotation_selected_on_image.emit(self.selected_annotation)
            else:
                self.selected_annotation = None # Clicked outside, deselect
                logger.debug("Deselected annotation.")
                self.parent_view.annotation_selected_on_image.emit(None) # Emit None for deselection
            self.update()

    def mouseMoveEvent(self, event):
        mouse_pos_img_coords = self.get_image_coords(event.pos())
        if not mouse_pos_img_coords:
            self.unsetCursor() # Reset cursor if outside image area
            return

        if self.drawing:
            self.end_point = mouse_pos_img_coords
            self.update()
        elif self.dragging and self.selected_annotation:
            img_w = self._pixmap.width()
            img_h = self._pixmap.height()

            current_pixel_rect_f = self._norm_to_pixel_rect(self.selected_annotation, img_w, img_h)
            new_pixel_rect_f = QRectF(current_pixel_rect_f)

            if self.selection_handle == 'body':
                delta_x = mouse_pos_img_coords.x() - self.last_mouse_pos.x()
                delta_y = mouse_pos_img_coords.y() - self.last_mouse_pos.y()
                new_pixel_rect_f.translate(delta_x, delta_y)
                new_pixel_rect_f = self._clamp_rect_to_image(new_pixel_rect_f, img_w, img_h, preserve_size=True)
            else: # Resizing
                # Get current pixel coordinates (float)
                current_x1 = current_pixel_rect_f.left()
                current_y1 = current_pixel_rect_f.top()
                current_x2 = current_pixel_rect_f.right()
                current_y2 = current_pixel_rect_f.bottom()

                new_x1, new_y1, new_x2, new_y2 = current_x1, current_y1, current_x2, current_y2

                # Determine the fixed point and update the moving point
                if self.selection_handle == 'top-left':
                    new_x1 = mouse_pos_img_coords.x()
                    new_y1 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'top-right':
                    new_x2 = mouse_pos_img_coords.x()
                    new_y1 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'bottom-left':
                    new_x1 = mouse_pos_img_coords.x()
                    new_y2 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'bottom-right':
                    new_x2 = mouse_pos_img_coords.x()
                    new_y2 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'top':
                    new_y1 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'bottom':
                    new_y2 = mouse_pos_img_coords.y()
                elif self.selection_handle == 'left':
                    new_x1 = mouse_pos_img_coords.x()
                elif self.selection_handle == 'right':
                    new_x2 = mouse_pos_img_coords.x()
                
                # Manually ensure x1 <= x2 and y1 <= y2
                final_x1 = min(new_x1, new_x2)
                final_y1 = min(new_y1, new_y2)
                final_x2 = max(new_x1, new_x2)
                final_y2 = max(new_y1, new_y2)

                # Create a new QRectF from the updated corners
                new_pixel_rect_f = QRectF(final_x1, final_y1, final_x2 - final_x1, final_y2 - final_y1)
                
                # Clamp the new rectangle to image boundaries
                new_pixel_rect_f = self._clamp_rect_to_image(new_pixel_rect_f, img_w, img_h, preserve_size=False)
            
            norm_coords = self._pixel_to_norm_rect(new_pixel_rect_f, img_w, img_h)
            self.selected_annotation.x1 = norm_coords[0]
            self.selected_annotation.y1 = norm_coords[1]
            self.selected_annotation.x2 = norm_coords[2]
            self.selected_annotation.y2 = norm_coords[3]

            self.last_mouse_pos = mouse_pos_img_coords
            self.parent_view.annotation_changed.emit(self.selected_annotation) # Emit signal for real-time update
            self.update()
        else: # Not dragging, just hovering
            if self.parent_view.tool == "select":
                annotation, handle = self._hit_test(mouse_pos_img_coords)
                if annotation:
                    if handle == 'body':
                        self.setCursor(Qt.SizeAllCursor)
                    elif handle == 'top-left' or handle == 'bottom-right':
                        self.setCursor(Qt.SizeFDiagCursor)
                    elif handle == 'top-right' or handle == 'bottom-left':
                        self.setCursor(Qt.SizeBDiagCursor)
                    elif handle == 'top' or handle == 'bottom':
                        self.setCursor(Qt.SizeVerCursor)
                    elif handle == 'left' or handle == 'right':
                        self.setCursor(Qt.SizeHorCursor)
                else:
                    self.unsetCursor()
            else:
                self.unsetCursor()

    def leaveEvent(self, event):
        self.unsetCursor() # Reset cursor when mouse leaves the widget

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.selected_annotation:
            deleted_annotation_id = self.selected_annotation.id # Store ID before clearing selected_annotation
            logger.debug(f"Delete key pressed for annotation ID: {deleted_annotation_id}")
            try:
                conn = storage.create_connection("annotations.db")
                if conn:
                    if storage.delete_annotation(conn, deleted_annotation_id):
                        self.parent_view.annotations.remove(self.selected_annotation)
                        self.parent_view.annotation_deleted.emit(self.selected_annotation)
                        self.selected_annotation = None # Deselect after deletion
                        self.update()
                        logger.info(f"Annotation ID {deleted_annotation_id} deleted successfully.")
                    else:
                        QMessageBox.critical(self.parent_view, "Error", "Failed to delete annotation from database.")
                    conn.close()
            except Exception as e:
                logger.error(f"Error deleting annotation: {e}")
                QMessageBox.critical(self.parent_view, "Error", f"Could not delete the annotation: {e}")
        super().keyPressEvent(event)

    def mouseReleaseEvent(self, event):
        mouse_pos_img_coords = self.get_image_coords(event.pos())
        if not mouse_pos_img_coords:
            return

        if self.drawing:
            self.drawing = False
            self.end_point = mouse_pos_img_coords
            logger.debug(f"Mouse release: stop drawing at {self.end_point}")

            rect_f = QRectF(self.start_point, self.end_point).normalized()
            
            if self._pixmap:
                img_w = self._pixmap.width()
                img_h = self._pixmap.height()

                rect_f = self._clamp_rect_to_image(rect_f, img_w, img_h, preserve_size=False)
                norm_coords = self._pixel_to_norm_rect(rect_f, img_w, img_h)

                if self.parent_view.current_image_path:
                    # Prompt user for class ID
                    class_id, ok = QInputDialog.getInt(self, "Class ID", "Enter Class ID:", 0, 0, 1000, 1)
                    if ok:
                        try:
                            conn = storage.create_connection("annotations.db")
                            if conn:
                                image_id = storage.get_or_create_image(conn, self.parent_view.current_image_path)
                                if image_id is None:
                                    raise ConnectionError("Failed to get or create image record.")

                                new_annotation = Annotation(
                                    id=None, 
                                    image_id=image_id, 
                                    class_id=class_id, 
                                    x1=norm_coords[0], 
                                    y1=norm_coords[1], 
                                    x2=norm_coords[2], 
                                    y2=norm_coords[3]
                                )
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
                    else:
                        logger.info("Annotation creation cancelled by user.")

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

        def to_widget_coords_from_pixels(image_point_f_tuple):
            px = image_point_f_tuple[0] * target_size.width() / pixmap_size.width() + offset_x
            py = image_point_f_tuple[1] * target_size.height() / pixmap_size.height() + offset_y
            return QPointF(px, py)

        for annotation in self.parent_view.annotations:
            pixel_rect_f = self._norm_to_pixel_rect(annotation, img_w, img_h)
            widget_rect_f = QRectF(to_widget_coords_from_pixels(pixel_rect_f.topLeft().toTuple()),
                                   to_widget_coords_from_pixels(pixel_rect_f.bottomRight().toTuple()))

            if annotation == self.selected_annotation:
                painter.setPen(QPen(SELECTED_COLOR, 2, Qt.SolidLine)) # Blue for selected
                painter.drawRect(widget_rect_f)
                # Draw handles
                handles = self._get_handle_rects(pixel_rect_f)
                for handle_name, handle_rect_f_img_coords in handles.items():
                    handle_rect_f_widget_coords = QRectF(to_widget_coords_from_pixels(handle_rect_f_img_coords.topLeft().toTuple()),
                                                         to_widget_coords_from_pixels(handle_rect_f_img_coords.bottomRight().toTuple()))
                    painter.fillRect(handle_rect_f_widget_coords, SELECTED_COLOR) # Blue handles
            else:
                painter.setPen(QPen(UNSELECTED_COLOR, 2, Qt.SolidLine)) # Red for unselected
                painter.drawRect(widget_rect_f)

            # Determine bounding box color for text background
            if annotation == self.selected_annotation:
                bbox_color = SELECTED_COLOR
            else:
                bbox_color = UNSELECTED_COLOR

            # Draw class ID
            class_id_text = str(annotation.class_id)
            font = QFont("Sans-serif", 12)
            font.setBold(True)
            painter.setFont(font)
            
            text_rect = painter.fontMetrics().boundingRect(class_id_text)
            text_x = widget_rect_f.x()
            text_y = widget_rect_f.y() - text_rect.height() # Position directly on top edge

            # Draw background rectangle for text
            painter.fillRect(QRectF(text_x, text_y, text_rect.width(), text_rect.height()), bbox_color)

            # Draw text with a white color
            painter.setPen(QPen(Qt.white, 1)) # Text color
            painter.drawText(QPointF(text_x, text_y + painter.fontMetrics().ascent()), class_id_text)

        if self.drawing:
            p1 = to_widget_coords_from_pixels((self.start_point.x(), self.start_point.y()))
            p2 = to_widget_coords_from_pixels((self.end_point.x(), self.end_point.y()))
            rect_f = QRectF(p1, p2)
            painter.setPen(QPen(UNSELECTED_COLOR, 2, Qt.SolidLine))
            painter.drawRect(rect_f)

class ImageView(QScrollArea):
    """
    Widget to display the image. It's a scroll area containing a label.
    """
    annotation_added = Signal(object)
    annotation_changed = Signal(object) # New signal
    annotation_deleted = Signal(object) # New signal
    annotation_selected_on_image = Signal(object) # New signal

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

    def select_annotation_from_table(self, annotation):
        """
        Select an annotation based on a selection from the table.
        """
        self.image_label.selected_annotation = annotation
        self.image_label.update()
        logger.debug(f"Annotation ID {annotation.id} selected from table.")
        self.annotation_selected_on_image.emit(annotation)
