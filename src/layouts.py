from dash import html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import os
from pathlib import Path

COLOR_1 = '#AD1B02'


def get_general_dashboard_layout(datenrahmen, encoded_image, job_portale, bundeslaender, branchen, positionen,
                                 unternehmensgroessen):
    """
    Constructs the layout for the "Allgemeine Analyse der Stellenanzeigen" dashboard in a Dash web application.

    This dashboard serves as an initial overview of the dataset and provides key insights into the distribution
    and structure of job advertisements across various dimensions. It is designed to be the starting point
    for users navigating the broader dashboard suite.

    The layout is visually divided into two vertical sections:

    **Left Section:**
        - **Choropleth Map**: Displays the number of job advertisements per federal state in Germany.
          This allows users to visually identify geographical patterns and regional demand variations
          in the job market.

    **Right Section:**
        - **KPI Card**: A compact card highlighting three central metrics:
            - Total number of job advertisements available in the dataset.
            - Number of distinct job titles users can select from.
            - Number of distinct companies advertising job positions.

          These key performance indicators (KPIs) provide users with a quick, high-level understanding of the dataset’s scope.

        - **Bar Chart**: Visualizes the distribution of job postings by company size.
          This helps assess which types of companies are most active in the job market.

        - **Line Chart**: Illustrates the trend of job advertisements per job portal over time.
          This trend analysis enables users to see how the number of postings fluctuates across different platforms,
          offering insight into market dynamics and platform relevance.

    All visual components are integrated using responsive Dash and Dash Bootstrap Components, ensuring accessibility
    and clarity across devices.

    Args:
        datenrahmen (pd.DataFrame): A dataframe containing job advertisement data. It must include
            columns relevant to location, portal, industry, job position, and company size.
        encoded_image (str): A base64-encoded string of the logo image to be displayed (not currently shown in layout).
        job_portale (list): List of job portals from which the postings were scraped.
        bundeslaender (list): List of German federal states.
        branchen (list): List of industries represented in the data.
        positionen (list): List of job positions found in the dataset.
        unternehmensgroessen (list): List of company size categories (e.g., small, medium, large).

    Returns:
        html.Div: A Dash HTML Div component containing the structured layout and all associated
            visual elements such as maps, charts, and KPIs, ready for rendering in the dashboard interface.

    Note:
        This dashboard acts as a foundation for further analytical dashboards and helps guide users
        by providing a holistic view of the job advertisement landscape before exploring more specific metrics.
    """

    # Layout for the general dashboard view
    return html.Div([
        # Left half (50% of the 80% main area = 40% total width)
        html.Div([
            # Top chart (map)
            html.Div([
                html.H5('Anzahl der Stellenausschreibungen je Bundesland',
                        style={'textAlign': 'center', 'color': '#000000', 'marginBottom': '5px'}),
                dcc.Graph(
                    id='karte',
                    style={'height': '80vh', 'width': '100%'},
                    config={'displayModeBar': False}
                )
            ], style={'width': '100%'})
        ], style={
            'width': '50%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '0 5px'
        }),

        # Right half (50% of the 80% main area = 40% total width)
        html.Div([

            # Top row: Card and bar chart side by side
            html.Div([
                # Card (40% of the right half)
                html.Div([
                    html.H5('Ergebnisse',
                            style={
                                'textAlign': 'center',
                                'color': '#000000',
                                'marginBottom': '2vh',
                                'fontSize': 'calc(0.8rem + 0.5vh)'  # Responsive font size
                            }),
                    dbc.Card(
                        [
                            dbc.CardHeader(
                                "Kennzahlen",
                                style={
                                    'padding': '1vh',
                                    'textAlign': 'center',
                                    'fontWeight': 'bold',
                                    'fontSize': 'calc(0.6rem + 0.5vh)'
                                }
                            ),
                            dbc.CardBody(
                                [
                                    html.Div(
                                        style={
                                            'height': '100%',
                                            'display': 'flex',
                                            'flexDirection': 'column',
                                            'justifyContent': 'space-around',
                                            'alignItems': 'center'
                                        },
                                        children=[
                                            # Block 1: Total number of job listings
                                            html.Div(
                                                [
                                                    html.H5(
                                                        id='gesamtanzahl-karte',
                                                        style={
                                                            'textAlign': 'center',
                                                            'fontSize': 'calc(1rem + 1.5vh)',
                                                            'margin': '0',
                                                            'lineHeight': '1.2',
                                                            'fontWeight': 'bold'
                                                        }
                                                    ),
                                                    html.P(
                                                        "Anzahl der Stellenanzeigen insgesamt",
                                                        style={
                                                            'textAlign': 'center',
                                                            'margin': '0',
                                                            'fontSize': 'calc(0.5rem + 0.5vh)'
                                                        }
                                                    )
                                                ],
                                                style={'marginBottom': '1vh'}
                                            ),
                                            # Block 2: Number of selectable job titles
                                            html.Div(
                                                [
                                                    html.H5(
                                                        id='anzahl-jobtitel',
                                                        style={
                                                            'textAlign': 'center',
                                                            'fontSize': 'calc(1rem + 1.5vh)',
                                                            'margin': '0',
                                                            'lineHeight': '1.2',
                                                            'fontWeight': 'bold'
                                                        }
                                                    ),
                                                    html.P(
                                                        "Anzahl der auswählbaren Job Titel",
                                                        style={
                                                            'textAlign': 'center',
                                                            'margin': '0',
                                                            'fontSize': 'calc(0.5rem + 0.5vh)'
                                                        }
                                                    )
                                                ],
                                                style={'marginBottom': '1vh'}
                                            ),
                                            # Block 3: Number of selectable companies
                                            html.Div(
                                                [
                                                    html.H5(
                                                        id='anzahl-unternehmen',
                                                        style={
                                                            'textAlign': 'center',
                                                            'fontSize': 'calc(1rem + 1.5vh)',
                                                            'margin': '0',
                                                            'lineHeight': '1.2',
                                                            'fontWeight': 'bold'
                                                        }
                                                    ),
                                                    html.P(
                                                        "Anzahl der auswählbaren Unternehmen",
                                                        style={
                                                            'textAlign': 'center',
                                                            'margin': '0',
                                                            'fontSize': 'calc(0.5rem + 0.5vh)'
                                                        }
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ],
                                style={
                                    'height': '100%',
                                    'padding': '1vh',
                                    'overflow': 'hidden'
                                }
                            )
                        ],
                        style={
                            "height": "30vh",
                            "width": "100%",
                            "border": "none",
                            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
                        }
                    )
                ], style={
                    'width': '40%',
                    'display': 'inline-block',
                    'verticalAlign': 'top',
                    'paddingLeft': '1%'
                }),

                # Bar chart (60% of the right half)
                html.Div([
                    html.H5('Anzahl der Stellenausschreibungen nach Unternehmensgröße',
                            style={'textAlign': 'center', 'color': '#000000', 'marginBottom': '5px'}),
                    dcc.Graph(
                        id='unternehmensgroesse-balken',
                        style={'height': '35vh', 'width': '100%'},
                        config={'displayModeBar': False}
                    )
                ], style={
                    'width': '50%',
                    'display': 'inline-block',
                    'padding': '0 5px'
                })

            ], style={
                'width': '100%',
                'marginBottom': '10px'
            }),

            # Bottom row: Job ad trend by portal
            html.Div([
                html.H5('Trend der Stellenanzeigen pro Jobportal',
                        style={'textAlign': 'center', 'color': '#000000', 'marginBottom': '5px'}),
                dcc.Graph(
                    id='trend-linie',
                    style={'height': '38vh', 'width': '100%'},
                    config={'displayModeBar': False}
                )
            ], style={'width': '100%'})
        ], style={
            'width': '50%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '0 5px'
        })
    ], style={
        'width': '100%',
        'margin': '0',
        'padding': '0'
    })


def get_comparison_dashboard_layout(datenrahmen, unternehmen):
    """
    Builds the layout for the "Vergleich der Stellenanzeigen" section of the dashboard based on job advertisements.

    This section provides a central interface for conducting all relevant comparisons between
    compensation and benefits structures. It enables side-by-side analysis of job titles and companies
    to support transparent benchmarking. Both sections (left and right) operate independently and allow
    flexible comparisons, such as evaluating the same job title across two companies.

    Key features:
        - Two mirrored sections with:
            * Dropdown filters for selecting job titles and companies
            * Bar charts that visualize grouped compensation and benefit components
            * Dynamic headings based on selected filters
        - Data is loaded and interpreted here for the first time in the dashboard pipeline
        - Compensation and benefit elements are dynamically grouped into categories,
          enabling a structured comparison view

    Bar charts were deliberately chosen to ensure clear and intuitive comparisons of categorical values
    across companies and job titles. The design was iteratively improved based on feedback to
    maximize accessibility and ease of use for end users.

    Notes:
        - If the 'Job_Titel' column is not found in the DataFrame, the layout will still render
          but dropdowns will remain empty, and a warning is printed to the console.

    Args:
        datenrahmen (pd.DataFrame): A DataFrame containing job data, which must include
            at least a 'Job_Titel' column for job title filtering. Additional columns are used
            for downstream visualizations.
        unternehmen (list): A list of company names used to populate the company filter dropdowns.

    Returns:
        html.Div: A Dash HTML Div component representing the full layout of the comparison dashboard,
        including filters and charts for both sides of the comparison view.
    """

    # Fallback: If the required column doesn't exist, use empty options
    job_titel_options = []
    if 'Job_Titel' in datenrahmen.columns:
        job_titel_options = [{'label': job_titel, 'value': job_titel}
                             for job_titel in sorted(datenrahmen['Job_Titel'].unique())]
    else:
        print("Warnung: 'Job_Titel' Spalte nicht gefunden!")

    # Main layout for the comparison dashboard
    return html.Div([

        # Main container for side-by-side layout
        html.Div([
            # Left comparison section
            html.Div([
                # Top row of filters
                html.Div([
                    # Job title dropdown
                    html.Div([
                        html.Label("Job Titel", style={'fontSize': '14px', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='filter-job-titel-links',
                            options=job_titel_options,
                            placeholder="Wähle Job Titel",
                            clearable=True,
                            style={'width': '100%'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),

                    # Company dropdown filter
                    html.Div([
                        html.Label("Unternehmen", style={'fontSize': '14px', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='filter-unternehmen-links',
                            options=[{'label': unternehmen, 'value': unternehmen} for unternehmen in unternehmen],
                            placeholder="Wähle Unternehmen",
                            clearable=True,
                            style={'width': '100%'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block'})
                ], style={
                    'marginBottom': '15px',
                    'width': '100%'
                }),

                # Bar chart for compensation categories (left)
                html.Div([
                    html.H4('Vergleich nach Kategorien', style={
                        'textAlign': 'center',
                        'marginTop': '0',
                        'marginBottom': '5px'
                    }),
                    html.H5(id='titel-links', style={
                        'textAlign': 'center',
                        'marginTop': '0',
                        'marginBottom': '10px',
                        'fontSize': '0.9rem',
                        'color': '#666'
                    }),
                    dcc.Graph(
                        id='verguetungen-balken-links',
                        style={
                            'height': 'calc(90vh - 200px)',  # Adjusted height for extra title space
                            'width': '100%',
                            'marginTop': '0'
                        },
                        config={'displayModeBar': False}
                    )
                ], style={
                    'height': '100%',
                    'display': 'flex',
                    'flexDirection': 'column'
                })
            ], style={
                'width': '49%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'padding': '10px',
                'height': '90vh',
                'boxSizing': 'border-box'
            }),

            # Right comparison section
            html.Div([
                # Top row of filters
                html.Div([
                    # Job title dropdown
                    html.Div([
                        html.Label("Job Titel", style={'fontSize': '14px', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='filter-job-titel-rechts',
                            options=[{'label': job_titel, 'value': job_titel} for job_titel in
                                     sorted(datenrahmen['Job_Titel'].unique())],
                            placeholder="Wähle Job Titel",
                            clearable=True,
                            style={'width': '100%'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block', 'marginRight': '2%'}),

                    # Company dropdown filter
                    html.Div([
                        html.Label("Unternehmen", style={'fontSize': '14px', 'marginBottom': '5px'}),
                        dcc.Dropdown(
                            id='filter-unternehmen-rechts',
                            options=[{'label': unternehmen, 'value': unternehmen} for unternehmen in unternehmen],
                            placeholder="Wähle Unternehmen",
                            clearable=True,
                            style={'width': '100%'}
                        )
                    ], style={'width': '48%', 'display': 'inline-block'})
                ], style={
                    'marginBottom': '15px',
                    'width': '100%'
                }),

                # Bar chart for compensation categories (right)
                html.Div([
                    html.H4('Vergleich nach Kategorien', style={
                        'textAlign': 'center',
                        'marginTop': '0',
                        'marginBottom': '5px'
                    }),
                    html.H5(id='titel-rechts', style={
                        'textAlign': 'center',
                        'marginTop': '0',
                        'marginBottom': '10px',
                        'fontSize': '0.9rem',
                        'color': '#666'
                    }),
                    dcc.Graph(
                        id='verguetungen-balken-rechts',
                        style={
                            'height': 'calc(90vh - 200px)',  # Adjusted height for extra title space
                            'width': '100%',
                            'marginTop': '0'
                        },
                        config={'displayModeBar': False}
                    )
                ], style={
                    'height': '100%',
                    'display': 'flex',
                    'flexDirection': 'column'
                })
            ], style={
                'width': '49%',
                'display': 'inline-block',
                'verticalAlign': 'top',
                'padding': '10px',
                'height': '90vh',
                'boxSizing': 'border-box'
            })
        ], style={
            'width': '100%',
            'height': '90vh',
            'overflow': 'hidden',
            'margin': '0',
            'padding': '0'
        })
    ], style={
        'width': '100%',
        'height': '90vh',
        'overflow': 'hidden',
        'margin': '0',
        'padding': '0'
    })


def get_admin_dashboard_layout():
    """
    Builds the layout for the admin section of the dashboard.

    This interface allows authorized users to control which job titles are included
    in the scraping process. It is password-protected to restrict access and is
    designed for internal use only.

    The job title list (left side) can be freely modified to define which positions
    should be analyzed. Once finalized, the list can be uploaded to the database
    (MongoDB) using the corresponding button. The 'Job TitelListe leeren' button enables complete
    reset of the job title selection—useful primarily when restarting the project or
    redefining the scraping scope from scratch. Although technically possible during
    active use, clearing the list is not recommended.

    Key features:
        - Password-protected modal to restrict access to authorized users only.
        - Editable job title list input and display section.
        - Action buttons for clearing and uploading the job title list.
        - Informational alert box guiding the user through the workflow.
        - Confirmation modal for list clearing and success modal after upload.

    Returns:
        html.Div: A Dash HTML Div component containing the full layout of the admin dashboard.
    """
    # Layout Admin section
    return html.Div([

        # Password modal (initially invisible)
        dbc.Modal(
            [
                dbc.ModalHeader("Dieser Bereich ist Passwort-geschützt"),
                dbc.ModalBody([
                    html.P("Bitte geben Sie das Passwort ein, um diesen Bereich öffnen zu können."),
                    dcc.Input(
                        id='admin-passwort-eingabe',
                        type='password',
                        placeholder='Passwort eingeben',
                        style={'width': '100%'},
                        n_submit=0  # Enables submission via Enter key
                    ),
                    html.Div(id='passwort-feedback', style={'marginTop': '10px', 'color': 'red'})
                ]),
                dbc.ModalFooter([
                    dbc.Button(
                        "Bestätigen",
                        id='passwort-bestaetigen',
                        color='primary'
                    )
                ])
            ],
            id='passwort-modal',
            is_open=True,
            backdrop='static',
            keyboard=False
        ),

        # Main content container (becomes visible after successful password entry)
        html.Div([
            dbc.Row([
                # Left column (Job title management)
                dbc.Col([
                    html.H4("Hier bitte einen Job Titel eingeben",
                            style={'marginBottom': '20px'}),
                    dcc.Input(
                        id='jobtitel-eingabe',
                        type='text',
                        placeholder='Hier bitte einen Job Titel eingeben',
                        style={'width': '100%', 'marginBottom': '10px', 'padding': '10px'},
                        debounce=True,
                        autoComplete='off'
                    ),
                    html.Div(
                        id='jobtitel-liste-container',
                        style={
                            'marginTop': '20px',
                            'border': '1px solid #ddd',
                            'borderRadius': '5px',
                            'padding': '10px',
                            'height': 'calc(100vh - 250px)',  # Responsive height
                            'minHeight': '200px',
                            'overflowY': 'auto',
                            'backgroundColor': '#f8f9fa'
                        }
                    )
                ], width=6, style={'padding': '20px', 'height': '100%'}),  # Ensure full-height container

                # Right column (Actions & instructions)
                dbc.Col([
                    # Informational alert
                    dbc.Alert(
                        [
                            html.H4("Hinweis", className="alert-heading",
                                    style={'color': COLOR_1}),
                            html.Ol([
                                html.Li("Tragen Sie alle gewünschten Job-Titel in die Liste ein"),
                                html.Li("Klicken Sie auf 'Liste der Job Titel hochladen'"),
                                html.Li("Die gespeicherte Liste wird für die Suche nach Stellenanzeigen verwendet")
                            ], style={'paddingLeft': '20px'})
                        ],
                        color="warning",
                        style={'marginBottom': '20px'}
                    ),
                    # Clear job title list button
                    dbc.Button(
                        "Job Titel Liste leeren",
                        id='liste-leeren',
                        color='danger',
                        className="mb-3",
                        style={'width': '100%', 'padding': '10px'}
                    ),
                    # Upload job title list button
                    dbc.Button(
                        "Liste der Job Titel hochladen",
                        id='liste-hochladen',
                        color='success',
                        style={'width': '100%', 'padding': '10px'}
                    ),

                    # Confirmation modal for clearing the list
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Achtung",
                                            style={'fontWeight': 'bold', 'color': 'red'}),
                            dbc.ModalBody("Wollen Sie wirklich alle Job Titel aus der Liste entfernen?"),
                            dbc.ModalFooter([
                                dbc.Button(
                                    "Ja, alle entfernen",
                                    id="bestätigen-liste-leeren-ja",
                                    color="danger",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    "Abbrechen",
                                    id="bestätigen-liste-leeren-nein",
                                    color="secondary"
                                )
                            ])
                        ],
                        id="bestätigen-liste-leeren-modal",
                        is_open=False,
                    ),

                    # Success modal for upload
                    dbc.Modal(
                        [
                            dbc.ModalHeader(" "),
                            dbc.ModalBody("Liste erfolgreich hochgeladen"),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Schließen",
                                    id="erfolg-modal-schliessen",
                                    color="success"
                                )
                            )
                        ],
                        id="erfolg-modal",
                        is_open=False
                    )
                ], width=6, style={'padding': '20px'})
            ], style={'width': '100%', 'margin': '0'})
        ], style={'display': 'none', 'width': '100%'}, id='admin-inhalt')
    ], style={'width': '100%'})
