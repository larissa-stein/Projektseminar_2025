Docker Setup
============

This section explains how Docker is used to deploy the dashboard developed in the "Projektseminar 2025". It outlines the installation requirements, usage instructions, and how to access the application through a web browser.

Overview
--------

Docker allows the dashboard to run inside a self-contained container. This means that all necessary software (e.g., Python, Dash, libraries, and source code) is bundled together. As a result, the dashboard runs consistently on any machine without requiring manual setup of environments.

What Docker Provides:

- Portable, reproducible environment
- Simplified deployment across systems
- Easy start/stop with a single command

Installation Requirements
-------------------------

Before running the project with Docker, ensure the following components are installed:

- `Docker Desktop` (available at https://www.docker.com/products/docker-desktop)
- A Git client (e.g., GitHub Desktop) to download the project
- Internet access for image and package downloads

Project Integration
-------------------

Docker is integrated into the project through the following components:

- ``Dockerfile``: Defines the environment (based on ``python:3.11-slim``), installs all Python dependencies from ``requirements.txt``, copies the code, and runs the dashboard.
- ``.dockerignore``: Prevents unnecessary files (e.g., virtual environments or local builds) from being copied into the container.
- ``run_main.py``: Entry point used by Docker to start the dashboard application.
- ``.env``: Contains environment variables, e.g., MongoDB credentials.

How to Build and Run the Container
----------------------------------

1. **Open a terminal or command prompt** in the project root folder.

2. **Build the Docker image**:

   .. code-block:: bash

      docker build -t dashboard-app .

   The name ``dashboard-app`` is freely chosen and can be replaced with any image name you prefer.
   Just make sure to use the same name in the run command below.

3. **Start the container**:

   .. code-block:: bash

      docker run --env-file .env -p 8050:8050 --name dashboard-container dashboard-app

   - ``--env-file .env`` loads required credentials and settings from the environment file
   - ``-p 8050:8050`` maps the container's internal port 8050 to the host machine
   - ``--name dashboard-container`` assigns a convenient name to the container for easier reference

4. **Access the dashboard**:

   Open a web browser and go to:

   ::

      http://localhost:8050

How to Stop the Container
-------------------------

To stop the container when no longer needed:

.. code-block:: bash

   docker stop dashboard-container

To remove the container completely (if rebuilding):

.. code-block:: bash

   docker rm dashboard-container

Notes on MongoDB Integration
----------------------------

The dashboard uses a MongoDB Atlas cloud database to manage job title data. Credentials are provided through the ``.env`` file and not hardcoded in the source code. MongoDB connection testing is included in ``MongoDB.py`` using the official ``pymongo`` driver.

Security Note
-------------

As part of this Docker setup, the ``.env`` file - containing sensitive environment variables such as the MongoDB URI - was intentionally not included in the repository. To prevent any accidental exposure of credentials, the file is explicitly listed in the ``.gitignore`` file. This ensures that confidential configuration data remains secure and is not published to GitHub.

