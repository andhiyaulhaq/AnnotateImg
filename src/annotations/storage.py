"""
Saving and loading annotations (using SQLite).
"""
import sqlite3
import logging
from .annotation import Annotation

logger = logging.getLogger(__name__)

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logger.info(f"Successfully connected to database: {db_file}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def create_tables(conn):
    """ create tables in the SQLite database
    :param conn: Connection object
    """
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY,
                image_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                bbox TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images (id)
            );
        """)
        logger.info("Tables created or already exist.")
    except sqlite3.Error as e:
        logger.error(f"Error creating tables: {e}")

def get_or_create_image(conn, path):
    """
    Get the ID of an image from its path, creating a new record if it doesn't exist.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM images WHERE path = ?", (path,))
        data = cursor.fetchone()
        if data is None:
            cursor.execute("INSERT INTO images (path) VALUES (?)", (path,))
            conn.commit()
            image_id = cursor.lastrowid
            logger.info(f"Created new image record for path: {path} with ID: {image_id}")
            return image_id
        else:
            return data[0]
    except sqlite3.Error as e:
        logger.error(f"Error getting or creating image for path {path}: {e}")
        return None

def create_annotation(conn, annotation):
    """
    Create a new annotation.
    """
    try:
        bbox_str = ",".join(map(str, annotation.bbox))
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO annotations (image_id, class_id, bbox) VALUES (?, ?, ?)",
            (annotation.image_id, annotation.class_id, bbox_str)
        )
        conn.commit()
        anno_id = cursor.lastrowid
        logger.info(f"Created new annotation with ID: {anno_id} for image ID: {annotation.image_id}")
        return anno_id
    except sqlite3.Error as e:
        logger.error(f"Error creating annotation for image ID {annotation.image_id}: {e}")
        return None

def get_annotations_for_image(conn, image_id):
    """
    Get all annotations for a given image ID.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, class_id, bbox FROM annotations WHERE image_id = ?", (image_id,))
        annotations = []
        for row in cursor.fetchall():
            bbox_str = row[2]
            try:
                bbox = [float(p) for p in bbox_str.split(',')]
                if len(bbox) != 4:
                     raise ValueError("Invalid number of bbox values")
            except (ValueError, TypeError):
                logger.warning(f"Could not parse bbox '{bbox_str}' for annotation id {row[0]}. Skipping.")
                continue

            annotations.append(Annotation(
                id=row[0],
                image_id=image_id,
                class_id=row[1],
                bbox=bbox
            ))
        logger.info(f"Retrieved {len(annotations)} annotations for image ID: {image_id}")
        return annotations
    except sqlite3.Error as e:
        logger.error(f"Error getting annotations for image ID {image_id}: {e}")
        return []

def update_annotation(conn, annotation):
    """
    Update an existing annotation.
    """
    try:
        bbox_str = ",".join(map(str, annotation.bbox))
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE annotations SET class_id = ?, bbox = ? WHERE id = ?",
            (annotation.class_id, bbox_str, annotation.id)
        )
        conn.commit()
        logger.info(f"Updated annotation with ID: {annotation.id}")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error updating annotation with ID {annotation.id}: {e}")
        return False

def get_image_id_by_path(conn, image_path):
    """
    Get the ID of an image from its path.
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM images WHERE path = ?", (image_path,))
        result = cursor.fetchone()
        return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"Error getting image ID for path {image_path}: {e}")
        return None