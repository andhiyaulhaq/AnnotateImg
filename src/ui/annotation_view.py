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
        self.model.setHorizontalHeaderLabels(['ID', 'Label', 'Points'])
        self.setModel(self.model)
        logger.info("Annotation view initialized.")

    def add_annotation(self, annotation):
        """
        Add a single annotation to the table.
        """
        points_str = "; ".join([f"({p[0]},{p[1]})" for p in annotation.points])
        self.model.appendRow([
            QStandardItem(str(annotation.id)),
            QStandardItem(annotation.label),
            QStandardItem(points_str),
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
