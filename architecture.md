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
        *   A **Toolbar** for quick access to annotation tools like "Select" (for selecting, moving, and resizing existing bounding boxes) and "Draw Bounding Box".
    *   **Image List View (Sidebar):** A dockable widget, typically on the left, that lists all the image files (e.g., `.jpg`, `.png`) found in the currently opened folder. Clicking an image in this list will open it for annotation.
    *   **Image View:** The central widget, implemented as a `QScrollArea`. It contains a `QLabel` that handles its own painting to display the image. This ensures the image is always scaled to fit the available viewport while maintaining its aspect ratio, preventing overflow. The `QLabel` also handles mouse events (`mousePressEvent`, `mouseMoveEvent`, `mouseReleaseEvent`) for drawing new annotations, and for selecting, moving, and resizing existing annotations. Selected bounding boxes are highlighted with a different color and display resize handles. The user can resize bounding boxes by dragging either their corners or their edges (top, bottom, left, right). The cursor dynamically changes its appearance (e.g., diagonal arrows for corner resizing, vertical/horizontal arrows for edge resizing, four-directional arrow for moving) when hovering over resize handles or the body of a selected bounding box, providing intuitive visual feedback to the user.
    *   **Annotation View (Table):** A dockable widget that displays annotation data. The table includes the following columns:
        *   `ID`: The unique identifier of the annotation.
        *   `Class ID`: The integer representing the class of the object.
        *   `X1`: The normalized x-coordinate of the top-left corner of the bounding box.
        *   `Y1`: The normalized y-coordinate of the top-left corner of the bounding box.
        *   `X2`: The normalized x-coordinate of the bottom-right corner of the bounding box.
        *   `Y2`: The normalized y-coordinate of the bottom-right corner of the bounding box.
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
    *   The database stores image paths, `class_id`, and the normalized bounding box coordinates (`x1, y1, x2, y2`).
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
4.  When the user presses the mouse button on the image, `mousePressEvent` is triggered. It records the starting coordinates of the bounding box in the image's pixel coordinate system.
5.  As the user drags the mouse, `mouseMoveEvent` is triggered continuously. This event handler draws a temporary rectangle on the `QLabel` to provide visual feedback.
6.  When the user releases the mouse button, `mouseReleaseEvent` is triggered. It records the final pixel coordinates.
7.  The start and end pixel coordinates are converted into an `[x1, y1, x2, y2]` format, representing the top-left and bottom-right corners. These pixel coordinates are handled with floating-point precision using `QPointF` and `QRectF` and are clamped to ensure they remain within the image boundaries, preserving their size during repositioning and clamping both position and size during resizing. They are then normalized based on the image's dimensions to the format: `<x1> <y1> <x2> <y2>`, where all values are floats between 0 and 1.
8.  An `Annotation` object is created with the `image_id`, a `class_id` (e.g., 0 for the first class), and the normalized `bbox` coordinates. This object is then saved to the SQLite database via the `storage.py` module.
9.  The `image_view` emits an `annotation_added` signal, which is connected to the `annotation_view` to update its display with the new annotation.

## Workflow Example: Selecting and Modifying a Bounding Box

1.  The user clicks the "Select" action in the toolbar, setting the application's state to `current_tool = 'select'`.
2.  The user clicks on the `ImageView`. The `mousePressEvent` handler checks if the click occurred within an existing bounding box or on one of its resize handles.
3.  If a bounding box is hit, it becomes the `selected_annotation`, and its color changes to blue (from red). If a handle is hit, the `selection_handle` is set accordingly (e.g., 'top-left', 'body').
4.  As the user drags the mouse (`mouseMoveEvent`), the `selected_annotation` is either moved (if `selection_handle` is 'body') or resized (if a handle is selected). All coordinate calculations are performed with floating-point precision using `QPointF` and `QRectF`.
    *   **Moving:** The bounding box's size is preserved, and its position is updated based on the mouse movement, clamped to remain within image boundaries.
    *   **Resizing:** The corner opposite to the dragged handle remains fixed. The new bounding box coordinates are calculated based on this fixed point and the mouse's current position. The resulting rectangle is then clamped to ensure it stays within the image boundaries.
    The `x1, y1, x2, y2` coordinates of the `selected_annotation` are updated in real-time. The `ImageView` repaints to show the changes, and the `annotation_view` is updated in real-time to reflect these changes.
5.  When the user releases the mouse button (`mouseReleaseEvent`), the dragging operation ends. The updated `bbox` coordinates of the `selected_annotation` are saved to the database via the `storage.py` module.
6.  The `image_view` emits an `annotation_changed` signal, which is connected to the `annotation_view` to update its display with the modified annotation.

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
