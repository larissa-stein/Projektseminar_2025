import json
import os
from pathlib import Path

# Determine the base directory of the script
BASE_DIR = Path(__file__).parent

# Path to the JSON file where job titles are stored
JOB_TITLE_FILE = os.path.join(BASE_DIR, "job_titles.json")


def load_job_titles():
    """
    Load saved job titles from a local JSON file.

    This function reads job titles that were previously stored in a local JSON file.
    These job titles are typically defined by users in the admin dashboard and used
    for scraping job advertisements. The loaded list is made available to the dashboard
    upon application start.

    Returns:
        list: A list of job titles. Returns an empty list if the file is missing or unreadable.
    """
    if os.path.exists(JOB_TITLE_FILE):
        with open(JOB_TITLE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_job_titles(job_title_list):
    """
    Save the provided list of job titles to a local JSON file.

    This function overwrites the existing local job titles file with the given list.
    It is used after the user adds or removes job titles in the admin dashboard.
    The saved list is also used as the basis for uploading to the MongoDB database.

    Args:
        job_title_list (list): A list of job titles to be saved.
    """
    with open(JOB_TITLE_FILE, "w", encoding="utf-8") as f:
        json.dump(job_title_list, f, ensure_ascii=False, indent=2)
    print(f"Job titles saved locally at {JOB_TITLE_FILE}")


def delete_job_title(job_title):
    """
    Delete a specific job title from the list.

    This function removes a single job title from the saved list if it exists.
    The updated list is then saved to the JSON file.

    Args:
        job_title (str): The job title to remove.
    """
    job_title_list = load_job_titles()
    if job_title in job_title_list:
        job_title_list.remove(job_title)
        save_job_titles(job_title_list)


def delete_all_job_titles():
    """
    Delete all saved job titles.

    This function clears the entire list of saved job titles
    by overwriting the JSON file with an empty list.
    """
    save_job_titles([])
