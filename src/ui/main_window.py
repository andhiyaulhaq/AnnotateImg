"""
Main application window.
"""
import os
import logging
from PySide6.QtWidgets import QMainWindow, QDockWidget, QFileDialog, QToolBar, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from .image_view import ImageView
from .image_list_view import ImageListView
from .annotation_view import AnnotationView

logger = logging.getLogger(__name__)

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

        # Connect signals
        self.image_view.annotation_added.connect(self.on_annotation_added)
        self.image_view.annotation_changed.connect(self.annotation_view.update_annotation)
        self.image_view.annotation_deleted.connect(self.annotation_view.remove_annotation)
        self.annotation_view.annotation_selected_from_table.connect(self.image_view.select_annotation_from_table)
        self.image_view.annotation_selected_on_image.connect(self.annotation_view.select_annotation_in_table)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.file_menu = self.menu_bar.addMenu("File")

        self.open_folder_action = QAction("Open Folder", self)
        self.open_folder_action.triggered.connect(self.open_folder)
        self.file_menu.addAction(self.open_folder_action)

        # Toolbar
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        self.select_tool_action = QAction("Select", self)
        self.select_tool_action.setCheckable(True)
        self.select_tool_action.triggered.connect(self.set_select_tool)
        self.toolbar.addAction(self.select_tool_action)

        self.draw_bbox_action = QAction("Draw BBox", self)
        self.draw_bbox_action.setCheckable(True)
        self.draw_bbox_action.triggered.connect(self.set_draw_bbox_tool)
        self.toolbar.addAction(self.draw_bbox_action)
        
        logger.info("Main window initialized.")

    def set_select_tool(self):
        if self.select_tool_action.isChecked():
            self.current_tool = "select"
            self.draw_bbox_action.setChecked(False)
            logger.info("Tool set to: Select")
        else:
            self.current_tool = None
            logger.info("Tool unset.")
        self.image_view.set_tool(self.current_tool)
        # Explicitly deselect any annotation when changing tools
        self.image_view.image_label.selected_annotation = None
        self.image_view.image_label.update()
        self.image_view.annotation_selected_on_image.emit(None) # Emit None to deselect in table

    def set_draw_bbox_tool(self):
        if self.draw_bbox_action.isChecked():
            self.current_tool = "bbox"
            self.select_tool_action.setChecked(False)
            logger.info("Tool set to: Draw BBox")
        else:
            self.current_tool = None
            logger.info("Tool unset.")
        self.image_view.set_tool(self.current_tool)
        # Explicitly deselect any annotation when changing tools
        self.image_view.image_label.selected_annotation = None
        self.image_view.image_label.update()
        self.image_view.annotation_selected_on_image.emit(None) # Emit None to deselect in table

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            try:
                logger.info(f"Opening folder: {folder_path}")
                self.current_folder = folder_path
                self.image_list_view.clear()
                self.annotation_view.clear_annotations()
                self.image_view.set_image(None)
                
                image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                self.image_list_view.addItems(image_files)
                logger.info(f"Found {len(image_files)} images in folder.")
            except OSError as e:
                logger.error(f"Error accessing folder {folder_path}: {e}")
                QMessageBox.critical(self, "Error", f"Could not access the folder: {e}")

    def on_annotation_added(self, annotation):
        logger.info(f"New annotation added with ID: {annotation.id}")
        self.annotation_view.add_annotation(annotation)

    def on_image_clicked(self, item):
        if self.current_folder:
            image_path = os.path.join(self.current_folder, item.text())
            logger.info(f"Image selected: {image_path}")
            self.image_view.set_image(image_path)
            self.annotation_view.load_annotations(self.image_view.annotations)
