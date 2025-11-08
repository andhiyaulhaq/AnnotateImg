"""
Widget for displaying annotation data in a table.
"""
from PySide6.QtWidgets import QTableView
from PySide6.QtGui import QStandardItemModel, QStandardItem

class AnnotationView(QTableView):
    """
    Widget to display annotation data.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels([
            'File Path', 'XYWH Normalized', 'x_center', 'y_center', 'width', 'height'
        ])
        self.setModel(self.model)

        # Placeholder data
        self.model.appendRow([
            QStandardItem("/path/to/image1.jpg"),
            QStandardItem("(0.5, 0.5, 0.2, 0.2)"),
            QStandardItem("0.5"),
            QStandardItem("0.5"),
            QStandardItem("0.2"),
            QStandardItem("0.2"),
        ])
