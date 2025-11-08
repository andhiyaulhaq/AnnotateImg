"""
Saving and loading annotations (using SQLite).
"""
import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn

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
    except sqlite3.Error as e:
        print(e)
