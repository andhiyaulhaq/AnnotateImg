"""
Widget for displaying annotation data in a table.
"""
import logging
from PySide6.QtWidgets import QTableView
from PySide6.QtGui import QStandardItemModel, QStandardItem

logger = logging.getLogger(__name__)

class AnnotationView(QTableView):
    """
    Widget to display annotation data.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(['ID', 'Class ID', 'X1', 'Y1', 'X2', 'Y2'])
        self.setModel(self.model)
        logger.info("Annotation view initialized.")

    def add_annotation(self, annotation):
        """
        Add a single annotation to the table.
        """
        self.model.appendRow([
            QStandardItem(str(annotation.id)),
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
            if item_id and int(item_id.text()) == annotation.id:
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
            if item_id and int(item_id.text()) == annotation.id:
                self.model.removeRow(row)
                logger.info(f"Annotation {annotation.id} removed from the view.")
                return
        logger.warning(f"Annotation {annotation.id} not found in the view for removal.")
