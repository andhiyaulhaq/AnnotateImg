# Image Annotation Tool

This is a desktop application designed for efficient image annotation, focusing on bounding box creation and management. Built with Python and PySide6, it provides a user-friendly interface for labeling objects within images, storing annotations persistently in an SQLite database.

## Features

*   **Image Loading & Display**: Load images from a selected folder and display them in a central view, scaled to fit while maintaining aspect ratio.
*   **Bounding Box Annotation**:
    *   **Drawing**: Intuitive drawing of new bounding boxes directly on the image.
    *   **Selection**: Select existing bounding boxes for modification.
    *   **Movement**: Move selected bounding boxes by dragging their body.
    *   **Resizing**: Resize bounding boxes using corner and edge handles, with precise floating-point coordinate handling.
    *   **Dynamic Cursors**: Visual feedback with dynamic cursor changes (e.g., diagonal, vertical, horizontal, four-directional arrows) indicating interaction modes.
*   **Coordinate System**: Utilizes `x1, y1, x2, y2` normalized floating-point coordinates for precise annotation storage and manipulation.
*   **Class ID Input**: Prompts the user with a dialog to enter a class ID for each new bounding box created.
*   **YOLO-like Label Display**: Bounding box class IDs are displayed at the top-left corner with a bold, sans-serif, white font, and a background color that matches the bounding box's state (blue for selected, red for unselected), without any padding.
*   **Persistent Storage**: Annotations are saved to an SQLite database (`annotations.db`), allowing users to resume work across sessions and navigate between images with their annotations preserved.
*   **Annotation Table View**: A dedicated table displays all annotations for the current image, showing `ID`, `Class ID`, `X1`, `Y1`, `X2`, and `Y2` coordinates.
*   **Annotation Deletion**: Delete selected bounding boxes by pressing the "Delete" key.
*   **Synchronized Selection**:
    *   Selecting a bounding box in the image highlights its corresponding row in the annotation table.
    *   Clicking a row in the annotation table selects and highlights the corresponding bounding box in the image.
*   **Tool-based Deselection**: Automatically deselects any active annotation (both in the image and the table) when switching between "Select" and "Draw BBox" tools.

## Installation

To set up the project locally, follow these steps:

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/image_annotator.git
    cd image_annotator
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv .venv
    ```

3.  **Activate the virtual environment**:
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

4.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Run the application**:
    ```bash
    python src/main.py
    ```

2.  **Open a Folder**:
    *   Go to `File` -> `Open Folder` and select a directory containing your images.
    *   The images will appear in the "Images" sidebar.

3.  **Annotate Images**:
    *   Select an image from the "Images" sidebar to display it.
    *   Choose the "Draw BBox" tool from the toolbar. Click and drag on the image to draw a bounding box. A dialog will appear to enter the `Class ID`.
    *   Choose the "Select" tool from the toolbar to select, move, or resize existing bounding boxes.
    *   Click on a bounding box to select it. Drag its body to move it, or drag its corners/edges to resize.
    *   To delete a selected bounding box, press the `Delete` key.

4.  **Manage Annotations**:
    *   The "Annotations" table displays details of all bounding boxes for the current image.
    *   Clicking a row in the table will select the corresponding bounding box in the image.
    *   Selecting a bounding box in the image will highlight its row in the table.

## Architecture

For a detailed understanding of the application's architecture, including its modular design, data flow, and component interactions, please refer to the [architecture.md](architecture.md) file.
