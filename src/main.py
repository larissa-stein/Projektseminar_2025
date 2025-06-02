import os
from src.data_download import load_database, load_geojson
from src.jobs_upload import (
    load_job_titles,
    save_job_titles,
    delete_job_title,
    delete_all_job_titles
)
from src.dashboard import app  # Import the Dash app from dashboard.py


def main():
    """
    Main entry point for launching the job advertisement analysis dashboard.

    This function initializes the full dashboard application and starts the Dash web server,
    enabling local access to all dashboard features via a web browser.

    When executed locally (e.g., via Python on a personal machine), the following URL becomes
    available for interaction with the dashboard:
    http://localhost:8050/

    Additionally, the address http://0.0.0.0:8050/ is automatically displayed by the underlying
    Dash/Flask server. While this address appears in the terminal output, it is primarily used
    for containerized environments such as Docker, where external access to the app is required.

    The dashboard provides the following core functionalities:

    * Visualization and interactive exploration of job advertisement data
    * Filtering and comparison across various job-related dimensions
    * Administrative tools to manage job titles used for web scraping
    """

    # Only display on initial start (not during debug reload)
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        print("Dashboard running locally at: http://localhost:8050/")

    # Run the Dash application
    app.run_server(host="0.0.0.0", port=8050, debug=True, use_reloader=False)


if __name__ == '__main__':
    main()