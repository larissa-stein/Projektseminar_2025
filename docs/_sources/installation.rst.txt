Installation
============

To prepare the system for execution, this section outlines the basic installation requirements. The dashboard application can be run either through a local Python environment or via Docker. This section focuses solely on preparing the environment—details on launching the application are covered in later chapters.

Required Software
-----------------

To proceed, ensure that the following software is installed on your system:

- Python 3.12 (recommended)
- Docker Desktop for Windows

.. note::
   Docker Compose is already bundled with Docker Desktop on Windows and does not require separate installation.

Python Environment Setup
------------------------

If you choose to run the application using Python, the following steps are required:

1. **Install Python 3.12**
   Download and install the official Python 3.12 release.

2. **Install required packages**
   All Python dependencies are listed in the ``requirements.txt`` file located in the project directory. To install them:

   a. Open the Command Prompt
   b. Navigate to the project directory
   c. Execute the following command:

   .. code-block:: bat

      pip install -r requirements.txt

   This will install all necessary libraries required to run the application.

Alternative: Docker
-------------------

If you prefer to run the project in a containerized environment, Docker can be used as an alternative to manual setup. Please refer to the dedicated chapter *Docker Deployment* for detailed instructions.
