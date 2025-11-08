"""
Widget for displaying annotation data in a table.
"""
import logging
from PySide6.QtWidgets import QTableView
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt # Import Qt for UserRole

logger = logging.getLogger(__name__)

class AnnotationView(QTableView):
    """
    Widget to display annotation data.
    """
    annotation_selected_from_table = Signal(object) # New signal

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(['ID', 'Class ID', 'X1', 'Y1', 'X2', 'Y2'])
        self.setModel(self.model)
        self.clicked.connect(self._on_table_clicked) # Connect table click to handler
        logger.info("Annotation view initialized.")

    def _on_table_clicked(self, index):
        """
        Handle a click on the table.
        """
        item = self.model.item(index.row(), 0) # Get the ID item
        if item:
            annotation = item.data(Qt.UserRole) # Retrieve the Annotation object
            if annotation:
                self.annotation_selected_from_table.emit(annotation)
                logger.debug(f"Annotation ID {annotation.id} selected from table.")

    def add_annotation(self, annotation):
        """
        Add a single annotation to the table.
        """
        id_item = QStandardItem(str(annotation.id))
        id_item.setData(annotation, Qt.UserRole) # Store the full annotation object
        self.model.appendRow([
            id_item,
            QStandardItem(str(annotation.class_id)),
            QStandardItem(f"{annotation.x1:.4f}"),
            QStandardItem(f"{annotation.y1:.4f}"),
            QStandardItem(f"{annotation.x2:.4f}"),
            QStandardItem(f"{annotation.y2:.4f}"),
        ])
        logger.info(f"Annotation {annotation.id} added to the view.")

    def clear_annotations(self):
        """
        Clear all annotations from the table.
        """
        self.model.removeRows(0, self.model.rowCount())
        logger.info("Annotation view cleared.")

    def load_annotations(self, annotations):
        """
        Load a list of annotations into the table.
        """
        self.clear_annotations()
        for annotation in annotations:
            self.add_annotation(annotation)
        logger.info(f"Loaded {len(annotations)} annotations into the view.")

    def update_annotation(self, annotation):
        """
        Update a single annotation in the table.
        """
        for row in range(self.model.rowCount()):
            item_id = self.model.item(row, 0)
            if item_id:
                stored_annotation = item_id.data(Qt.UserRole)
                # Check if it's the same annotation object (for temporary ones)
                # or if the IDs match (for saved ones)
                if stored_annotation == annotation or (stored_annotation and stored_annotation.id == annotation.id):
                    # Update the stored annotation object
                    item_id.setData(annotation, Qt.UserRole)
                    # Update the display text
                    item_id.setText(str(annotation.id))
                    self.model.item(row, 1).setText(str(annotation.class_id))
                    self.model.item(row, 2).setText(f"{annotation.x1:.4f}")
                    self.model.item(row, 3).setText(f"{annotation.y1:.4f}")
                    self.model.item(row, 4).setText(f"{annotation.x2:.4f}")
                    self.model.item(row, 5).setText(f"{annotation.y2:.4f}")
                    logger.info(f"Annotation {annotation.id} updated in the view.")
                    return
        logger.warning(f"Annotation {annotation.id} not found in the view for update.")

    def remove_annotation(self, annotation):
        """
        Remove a single annotation from the table.
        """
        for row in range(self.model.rowCount()):
            item_id = self.model.item(row, 0)
            if item_id:
                stored_annotation = item_id.data(Qt.UserRole)
                if stored_annotation == annotation or (stored_annotation and stored_annotation.id == annotation.id):
                    self.model.removeRow(row)
                    logger.info(f"Annotation {annotation.id} removed from the view.")
                    return
        logger.warning(f"Annotation {annotation.id} not found in the view for removal.")

    def select_annotation_in_table(self, annotation):
        """
        Selects the row corresponding to the given annotation in the table.
        If annotation is None, clears the selection.
        """
        self.clearSelection() # Clear previous selection

        if annotation is None:
            logger.debug("Annotation deselected in image view, clearing table selection.")
            return

        for row in range(self.model.rowCount()):
            item_id = self.model.item(row, 0)
            if item_id:
                stored_annotation = item_id.data(Qt.UserRole)
                if stored_annotation == annotation or (stored_annotation and stored_annotation.id == annotation.id):
                    self.selectRow(row)
                    logger.debug(f"Annotation ID {annotation.id} selected in table.")
                    return
        logger.warning(f"Annotation {annotation.id} not found in table for selection.")
