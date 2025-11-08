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
                label TEXT NOT NULL,
                points TEXT NOT NULL,
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
        points_str = ";".join([f"{p[0]},{p[1]}" for p in annotation.points])
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO annotations (image_id, label, points) VALUES (?, ?, ?)",
            (annotation.image_id, annotation.label, points_str)
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
        cursor.execute("SELECT id, label, points FROM annotations WHERE image_id = ?", (image_id,))
        annotations = []
        for row in cursor.fetchall():
            points_str = row[2].split(';')
            points = []
            for p_str in points_str:
                if p_str:
                    try:
                        x_str, y_str = p_str.split(',')
                        points.append((int(x_str), int(y_str)))
                    except ValueError:
                        logger.warning(f"Could not parse point '{p_str}' for annotation id {row[0]}. Skipping.")
            
            if points:
                annotations.append(Annotation(
                    id=row[0],
                    image_id=image_id,
                    label=row[1],
                    points=points
                ))
        logger.info(f"Retrieved {len(annotations)} annotations for image ID: {image_id}")
        return annotations
    except sqlite3.Error as e:
        logger.error(f"Error getting annotations for image ID {image_id}: {e}")
        return []

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
