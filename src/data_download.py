import sqlite3
import gdown
import pandas as pd
import json
from functools import lru_cache
import os
from pathlib import Path

# Determine base directory
BASE_DIR = Path(__file__).parent

DB_PATH = os.path.join(BASE_DIR, "job_analysis.db")
DEFAULT_GEOJSON_PATH = os.path.join(BASE_DIR, "bundeslaender.json")
GOOGLE_DRIVE_URL = "https://drive.google.com/uc?id=1av6u76MAICXikg6f7gLmBsU8NAaOquYc"


@lru_cache(maxsize=None)
def load_database() -> pd.DataFrame | None:
    """Downloads and loads a SQLite database from Google Drive as a pandas DataFrame.

    This function provides temporary access to job analysis data during development.
    In production, the database will be accessed locally or via a Docker container.

    All entries are loaded from the database, which contains all available information
    about the job advertisements.

    To improve performance, the result is cached using least-recently-used (LRU) caching,
    preventing repeated downloads.

    Returns:
        pd.DataFrame | None: A DataFrame containing job analysis data, or None if an error occurs.

    Raises:
        sqlite3.Error: If an error occurs while accessing the SQLite database.
        pd.errors.DatabaseError: If the SQL query using pandas fails.
        Exception: For general errors during download or data loading.
    """
    try:
        # Download with absolute path
        gdown.download(
            GOOGLE_DRIVE_URL,
            DB_PATH,
            quiet=True
        )

        with sqlite3.connect(DB_PATH) as verbindung:
            datenrahmen = pd.read_sql_query(
                "SELECT * FROM job_analysis;",
                verbindung
            )
        return datenrahmen
    except Exception as e:
        print(f"Error loading data: {e}")
        return None


def load_geojson(dateipfad: str = 'bundeslaender.json') -> dict | None:
    """Load a GeoJSON file for geographic visualization in the dashboard.

    The file contains the map of Germany divided into federal states ("Bundesländer").
    It is used to filter and display job postings by region.

    Args:
        dateipfad (str, optional): Path to the GeoJSON file. Defaults to 'bundeslaender.json'.

    Returns:
        dict | None: Parsed GeoJSON data as a dictionary, or None if loading fails.
    """
    try:
        pfad = dateipfad if dateipfad else DEFAULT_GEOJSON_PATH
        with open(pfad, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"GeoJSON file not found at: {pfad}")
    except Exception as e:
        print(f"Error loading GeoJSON file: {e}")
    return None
