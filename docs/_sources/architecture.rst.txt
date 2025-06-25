System Architecture
===================

Component Interaction and Data Flow
-----------------------------------

The project consists of three technically distinct components that work together to support an AI-driven market analysis of compensation and benefits in post-merger integration scenarios:

1. **Web Scraping (Backend)**  
   Job advertisements are automatically collected based on predefined job titles. The extracted raw text data is stored in a MongoDB database for further processing.

2. **Natural Language Processing (Processing Layer)**  
   A pipeline retrieves the raw job advertisements from MongoDB, processes them using natural language processing techniques, and extracts structured information such as predefined categories, compensations, and benefits. The results are stored in a structured SQLite database.

3. **Dashboard Interface (Frontend)**  
   The dashboard provides an interactive visual interface for exploring the structured data stored in the SQLite database. Additionally, it allows users to define or upload job titles, which are stored in MongoDB and subsequently used by the scraper to collect new data.

This triangular system architecture enables a continuous and iterative cycle of data enrichment and analysis. Each component plays a distinct role and is connected via shared data interfaces:

.. mermaid::

   graph TD
       A[Web Scraper]
       B[NLP Pipeline]
       C[Dashboard]

       A -->|Raw job data via MongoDB| B
       B -->|Structured data via SQLite| C
       C -->|Job titles via MongoDB| A

This design allows for scalable, real-time insights based on continuously updated market data.

Dashboard Code Structure
------------------------

The dashboard was implemented in Python using the Dash framework by Plotly. Dash was chosen for its ability to create interactive, browser-based data visualizations using pure Python, without requiring frontend development expertise. The relevant modules are located in the `src/` directory and are organized to reflect distinct responsibilities within the dashboard architecture. This separation of concerns promotes clarity, modularity, and ease of maintenance.

**Modules Overview:**

.. code-block:: text

   src/
   ├── data_download.py     # SQLite data retrieval from Google Drive
   ├── MongoDB.py           # Interface and connection for the MongoDB
   ├── dashboard.py         # Dashboard initialization and callback logic
   ├── layouts.py           # Layouts for the three dashboard views of the navigation bar
   ├── jobs_upload.py       # Upload and management of job title lists in MongoDB
   └── main.py              # App startup with local and Docker URLs

**Module Descriptions:**

- :code:`data_download.py`
  Provides functionality to access structured job advertisement data from the SQLite database hosted on Google Drive. This data serves as the basis for all dashboard visualizations.

  .. note::

     **Important:** The Google Drive link may change if the file is moved, renamed, or replaced. In such cases, the data connection must be reconfigured.
     This external linkage becomes unnecessary if the SQLite file is stored locally on the same machine where the dashboard is executed, ensuring greater stability and independence from cloud storage.

- :code:`MongoDB.py`
  Provides utility functions to connect to MongoDB and upload job titles. It ensures the communication between the dashboard and the MongoDB database.

- :code:`dashboard.py`
  Initializes the dashboard application, registers the callback functions, and integrates layout components. It provides the overall structure and logic required for the dashboard to function.

- :code:`layouts.py`
  Defines the layouts of the three distinct dashboard views accessible via the navigation menu. Each layout corresponds to a specific analytical perspective and organizes charts, filters, and other visual components.

- :code:`jobs_upload.py`
  Manages the upload and modification of job title lists via the dashboard interface. These functions allow users to manage which job titles are stored in MongoDB and subsequently used by the web scraping component.

- :code:`main.py`
  Serves as the entry point of the application. It starts the Dash server and outputs both a local and Docker-accessible URL.

This modular structure enables clear functional boundaries, making the dashboard easy to maintain, scalable, and adaptable to future extensions such as new data sources, analytical views, or administrative tools.

Dashboard Layout Structure
--------------------------

The overall dashboard layout follows a 20/80 screen width distribution. On the **left 20%**, global filters are displayed. These filters apply across the first two main sections of the dashboard and were iteratively defined in consultation with PwC to support a consistent, user-friendly analysis experience. The **right 80%** of the interface is used for dynamically rendered dashboard views.

The general layout structure is implemented in :code:`dashboard.py`, while the content of each dynamic dashboard section is defined in :code:`layouts.py`.

.. figure:: _static/layout.png
   :alt: Dashboard layout with 20/80 distribution
   :align: center
   :width: 80%

