# Image Annotation Tool Architecture

This document outlines the proposed software architecture for the Image Annotation Tool.

## Core Technologies

*   **Programming Language:** Python
*   **UI Framework:** PySide6
*   **Image Processing:** OpenCV-Python
*   **Numerical Operations:** NumPy
*   **Database:** SQLite

## High-Level Architecture

The application will be designed using a modular approach to separate concerns, making it easier to develop, test, and maintain. The main components are:

1.  **User Interface (UI) Layer:**
    *   Built with PySide6.
    *   Responsible for all visual elements and user interaction.
    *   **Main Window:** The main container of the application. It will have:
        *   A **Menu Bar** with "File", "Edit", and "View" menus. The "File" menu will contain an "Open Folder" action to allow users to select a directory of images.
        *   A **Toolbar** for quick access to annotation tools like "Select" and "Draw Bounding Box".
    *   **Image List View (Sidebar):** A dockable widget, typically on the left, that lists all the image files (e.g., `.jpg`, `.png`) found in the currently opened folder. Clicking an image in this list will open it for annotation.
    *   **Image View:** The central widget, implemented as a `QScrollArea`. It contains a `QLabel` which displays the image and handles mouse events (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`) for drawing annotations. The image is scaled to fit the viewport by default, maintaining its aspect ratio.
    *   **Annotation View (Table):** A dockable widget that displays annotation data. The table will include the following columns:
        *   `File Path`: The path to the image file containing the annotation.
        *   `XYWH Normalized`: The bounding box coordinates `(x_center, y_center, width, height)`, normalized to be between 0 and 1.
        *   `x_center`, `y_center`, `width`, `height`: The individual normalized coordinate components in separate columns for easy viewing and editing.
    *   Handles user input events, such as mouse clicks and drags on the `ImageView` for drawing, and signals from other widgets like the toolbar or image list.

2.  **Image Processing & Annotation Layer:**
    *   Uses OpenCV and NumPy for image manipulation.
    *   Handles loading, processing, and displaying images.
    *   Manages the creation and drawing of annotations (e.g., bounding boxes, polygons) on the image canvas.
    *   This layer will receive user input events from the UI layer and translate them into annotation actions.

3.  **Data Management Layer:**
    *   Responsible for managing all annotation data.
    *   Will use an SQLite database (`annotations.db`) to store annotations for all images.
    *   This allows for persistent storage, enabling the user to move back and forth between images and view their previous annotations.
    *   The database will store image paths, annotation coordinates, labels, and other metadata.
    *   Handles creating, reading, updating, and deleting annotation records in the database.

4.  **Application Core:**
    *   The main entry point of the application.
    *   Initializes the UI and other components.
    *   Connects the different layers (e.g., connecting UI events to the image processing layer).
    *   Manages the overall application state.

## Directory Structure (Proposed)

```
.
├── src/
│   ├── main.py               # Application entry point
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py      # Main application window
│   │   ├── image_view.py       # Widget for displaying the image
│   │   ├── annotation_view.py  # Widget for displaying annotation data in a table
│   │   └── image_list_view.py  # Widget for listing images in a folder
│   ├── image/
│   │   ├── __init__.py
│   │   └── processing.py       # Image loading and manipulation
│   ├── annotations/
│   │   ├── __init__.py
│   │   ├── annotation.py       # Data structure for a single annotation
│   │   └── storage.py          # Saving and loading annotations (using SQLite)
│   └── utils/
│       └── __init__.py
├── requirements.txt        # Project dependencies
└── README.md
```

## Workflow Example: Opening an Image Directory and Displaying an Image

1.  User clicks "File" -> "Open Folder".
2.  The `main_window.py` opens a file dialog (`QFileDialog`) to select a directory.
3.  Once a directory is selected, the `main_window.py` scans the directory for image files (e.g., .jpg, .png).
4.  The list of found image files is passed to the `image_list_view.py` which displays them in the sidebar.
5.  A `itemClicked` signal from the `image_list_view` is connected to a handler method in `main_window.py`.
6.  When the user clicks on an image name in the sidebar, the handler method is executed.
7.  The handler retrieves the full path of the selected image.
8.  The image path is passed to a function in the `image.processing` module to load the image using OpenCV.
9.  The loaded image (as a NumPy array) is converted to a `QPixmap` and displayed in the `image_view.py` widget.
10. The Data Management Layer is then called to query the SQLite database for any existing annotations for that image, which are subsequently loaded and drawn on the image.

## Workflow Example: Drawing a Bounding Box

1.  A `QToolBar` is added to the `main_window.py`, containing a `QAction` for "Draw Bounding Box".
2.  The user clicks the "Draw Bounding Box" action. This sets a state in the application (e.g., `current_tool = 'bounding_box'`).
3.  The `image_view.py` (specifically the `QLabel` inside it) will have mouse event handlers (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`).
4.  When the user presses the mouse button on the image, `mousePressEvent` is triggered. It records the starting coordinates of the bounding box.
5.  As the user drags the mouse, `mouseMoveEvent` is triggered continuously. This event handler will draw a temporary rectangle on the `QPixmap` to provide visual feedback. This is done by creating a copy of the original pixmap and using a `QPainter` to draw on it.
6.  When the user releases the mouse button, `mouseReleaseEvent` is triggered. It records the final coordinates.
7.  The start and end coordinates are used to define the bounding box. These coordinates are then normalized based on the image dimensions.
8.  The normalized coordinates are used to create an `Annotation` object, which is then saved to the SQLite database via the `storage.py` module.
9.  The `annotation_view.py` is updated to display the new annotation.
