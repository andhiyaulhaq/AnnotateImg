"""
Application entry point.
"""
import sys
import logging
from PySide6.QtWidgets import QApplication
from .ui.main_window import MainWindow
from .annotations.storage import create_connection, create_tables
from .utils.logging import setup_logger

def main():
    """
    Main function to run the application.
    """
    # Set up logging
    setup_logger()
    logging.info("Application starting...")

    # Database setup
    try:
        conn = create_connection("annotations.db")
        if conn is not None:
            create_tables(conn)
            conn.close()
            logging.info("Database setup successful.")
        else:
            logging.error("Error! Cannot create the database connection.")
            sys.exit(1)
    except Exception as e:
        logging.critical(f"A critical error occurred during database setup: {e}")
        sys.exit(1)


    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    logging.info("Main window shown.")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
