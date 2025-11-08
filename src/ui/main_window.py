"""
Main application window.
"""
import os
from PySide6.QtWidgets import QMainWindow, QDockWidget, QFileDialog, QToolBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from .image_view import ImageView
from .image_list_view import ImageListView
from .annotation_view import AnnotationView

class MainWindow(QMainWindow):
    """
    Main window of the application.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Annotator")
        self.current_folder = None
        self.current_tool = None

        # Central widget
        self.image_view = ImageView()
        self.setCentralWidget(self.image_view)

        # Image List View (Sidebar)
        self.image_list_dock = QDockWidget("Images", self)
        self.image_list_view = ImageListView()
        self.image_list_dock.setWidget(self.image_list_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.image_list_dock)
        self.image_list_view.itemClicked.connect(self.on_image_clicked)

        # Annotation View (Table)
        self.annotation_dock = QDockWidget("Annotations", self)
        self.annotation_view = AnnotationView()
        self.annotation_dock.setWidget(self.annotation_view)
        self.addDockWidget(Qt.RightDockWidgetArea, self.annotation_dock)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")

        self.open_folder_action = QAction("Open Folder", self)
        self.open_folder_action.triggered.connect(self.open_folder)
        self.file_menu.addAction(self.open_folder_action)

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)
        self.draw_bbox_action = QAction("Draw BBox", self)
        self.draw_bbox_action.setCheckable(True)
        self.draw_bbox_action.triggered.connect(self.set_draw_bbox_tool)
        self.toolbar.addAction(self.draw_bbox_action)

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            self.current_folder = folder_path
            self.image_list_view.clear()
            image_files = [f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
            self.image_list_view.addItems(image_files)

    def on_image_clicked(self, item):
        if self.current_folder:
            image_path = os.path.join(self.current_folder, item.text())
            self.image_view.set_image(image_path)

    def set_draw_bbox_tool(self):
        if self.draw_bbox_action.isChecked():
            self.current_tool = "bbox"
        else:
            self.current_tool = None
        self.image_view.set_tool(self.current_tool)
