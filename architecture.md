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
    *   **Image View:** The central widget, implemented as a `QScrollArea`. It contains a `QLabel` that handles its own painting to display the image. This ensures the image is always scaled to fit the available viewport while maintaining its aspect ratio, preventing overflow. The `QLabel` also handles mouse events (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`) for drawing annotations.
    *   **Annotation View (Table):** A dockable widget that displays annotation data. The table includes the following columns:
        *   `ID`: The unique identifier of the annotation.
        *   `Label`: The label of the annotation (e.g., "bbox").
        *   `Points`: The coordinates of the annotation's points.
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
10. The Data Management Layer is then called to query the SQLite database for any existing annotations for that image, which are subsequently loaded and drawn on the image. The `annotation_view` is also updated with the annotations.

## Workflow Example: Drawing a Bounding Box

1.  A `QToolBar` is added to the `main_window.py`, containing a `QAction` for "Draw Bounding Box".
2.  The user clicks the "Draw Bounding Box" action. This sets a state in the application (e.g., `current_tool = 'bbox'`).
3.  The `image_view.py` (specifically the `QLabel` inside it) has mouse event handlers (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`).
4.  When the user presses the mouse button on the image, `mousePressEvent` is triggered. It records the starting coordinates of the bounding box.
5.  As the user drags the mouse, `mouseMoveEvent` is triggered continuously. The mouse coordinates, which are relative to the widget, are transformed to the coordinate system of the original image. This ensures that the annotation is correctly placed regardless of how the image is scaled or resized in the view. This event handler draws a temporary rectangle on the `QLabel` to provide visual feedback.
6.  When the user releases the mouse button, `mouseReleaseEvent` is triggered. It records the final coordinates, also transformed to the image's coordinate system.
7.  The start and end coordinates are used to define the bounding box. The pixel coordinates, now correctly mapped to the image, are stored.
8.  An `Annotation` object is created with the image_id, a default label, and the points. This object is then saved to the SQLite database via the `storage.py` module.
9.  The `image_view` emits an `annotation_added` signal, which is connected to the `annotation_view` to update its display with the new annotation.

## Logging and Error Handling

To ensure robustness and maintainability, the application implements comprehensive logging and error handling.

*   **Logging:**
    *   The application uses Python's built-in `logging` module.
    *   A central logger is configured in `src/utils/logging.py` to output all activity to the terminal (stdout).
    *   Log messages are added throughout the application to track user actions (e.g., opening a folder, selecting an image), application events (e.g., application start, window initialization), and the outcome of critical operations (e.g., database transactions, image loading).
    *   Logs are formatted to include a timestamp, logger name, log level, and the message.

*   **Error Handling:**
    *   Error handling is implemented using `try...except` blocks to catch potential exceptions at critical points, such as file I/O, database operations, and image processing.
    *   When an error is caught, it is logged with a detailed message, including the exception information.
    *   For errors that affect the user experience (e.g., failing to open a folder, failing to load an image), a `QMessageBox` dialog is displayed to provide clear and immediate feedback to the user.
    *   This strategy prevents the application from crashing unexpectedly and provides valuable diagnostic information for debugging.
