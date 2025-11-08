"""
Widget for listing images in a folder.
"""
from PySide6.QtWidgets import QListWidget

class ImageListView(QListWidget):
    """
    Widget to display a list of images.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
