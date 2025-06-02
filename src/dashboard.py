import os
import dash
from dash import Dash, html, dcc, Input, Output, State, ALL, no_update, ctx
from dash import callback_context as ctx
import pandas as pd
from typing import Optional
import plotly.express as px
import dash_bootstrap_components as dbc
from pathlib import Path
import sqlite3
import locale
import json
import base64
from src.data_download import load_database, load_geojson
from src.layouts import (
    get_general_dashboard_layout,
    get_comparison_dashboard_layout,
    get_admin_dashboard_layout
)
from src.jobs_upload import (load_job_titles, save_job_titles, delete_job_title, delete_all_job_titles)
from src.MongoDB import upload_job_titles_to_mongodb

# Determine the base directory of the project
BASE_DIR = Path(__file__).parent

# Set locale for German month names in date formatting
locale.setlocale(locale.LC_TIME, 'de_DE.UTF-8')

# Color scheme
COLOR_1 = '#AD1B02'
COLOR_2 = '#D85604'
COLOR_3 = '#E88D14'
COLOR_4 = '#F3BE26'
COLOR_5 = '#E669A2'  # Pink

# Load data from the remote database (Google Drive)
datenrahmen = load_database()
if datenrahmen is None:
    raise Exception("Datenbank konnte nicht geladen werden")

# Add mapping for types of employment
beschaeftigungsart_mapping = {
    'befristet': ['befristet'],
    'unbefristet': ['Feste Anstellung']
}

# Convert date column to datetime format
datenrahmen['Datum'] = pd.to_datetime(datenrahmen['Datum'], format='%d.%m.%Y')

# Group data for trendline plotting
df_trend = datenrahmen.groupby(['Datum', 'Portal_Name']).size().reset_index(name='Anzahl')

# Load GeoJSON file for map visualization
deutschland_geojson = load_geojson(os.path.join(BASE_DIR, "bundeslaender.json"))

# Load and encode the logo image for display in the dashboard
logo_path = os.path.join(BASE_DIR, "Logo-pwc.png")
if os.path.exists(logo_path):
    with open(logo_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('ascii')
else:
    print("Logo-pwc.png nicht gefunden – das Logo wird nicht angezeigt.")

# Extract global filter options for dashboard interactivity
job_portale = datenrahmen['Portal_Name'].unique()
bundeslaender = datenrahmen[datenrahmen['Land'] == 'Deutschland']['Bundesland'].unique()
beschaeftigungsarten = datenrahmen['Beschäftigungsart'].unique()
monate = sorted(datenrahmen['Datum'].dt.strftime('%Y-%m').unique())
berufserfahrungslevel = datenrahmen['Berufserfahrung_vorausgesetzt'].unique()
positionen = datenrahmen['Position'].unique()
unternehmen = datenrahmen['Unternehmen'].unique()
# unternehmensgroessen = datenrahmen['Unternehmensgröße'].unique()
branchen = datenrahmen['Kategorie'].dropna().unique()

# Define desired order of company sizes for consistent display
unternehmensgroessen_sortiert = [
    "0-10",
    "11-50",
    "51-250",
    "251-500",
    "501-1000",
    "1001-2500",
    "2501-10000",
    "10000+",
    "Keine Angaben"
]

# Filter and keep only available sizes in defined order
vorhandene_groessen = datenrahmen['Unternehmensgröße'].dropna().unique()
unternehmensgroessen = [groesse for groesse in unternehmensgroessen_sortiert
                        if groesse in vorhandene_groessen]

# Initialize Dash application
app = dash.Dash(__name__,
                external_stylesheets=[
                    dbc.themes.BOOTSTRAP,
                    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
                    # Font Awesome for icons
                ],
                suppress_callback_exceptions=True)

# App Layout
app.layout = html.Div([

    # Temporary storage for job titles
    dcc.Store(id='jobtitel-temp-speicher', data=load_job_titles()),

    # Navigation bar at the top
    dbc.Navbar(
        dbc.Container(
            [
                dbc.Row(
                    [
                        # Logo (left-aligned)
                        dbc.Col(
                            html.Img(
                                src=f'data:image/png;base64,{encoded_image}',
                                style={'height': '40px'}
                            ),
                            width="auto",
                            className="me-2"  # Spacing to the title
                        ),

                        # Dashboard title
                        dbc.Col(
                            dbc.NavbarBrand("Dashboard - Job Analyse", className="ms-2"),
                            width="auto"
                        ),
                    ],
                    align="center",
                    className="g-0"
                ),

                # Right-aligned navigation items
                dbc.NavbarToggler(id="navbar-toggler"),
                dbc.Collapse(
                    dbc.Nav(
                        [
                            dbc.NavItem(
                                dbc.NavLink("Allgemeine Analyse der Stellenanzeigen", id="nav-allgemein", href="#")),
                            dbc.NavItem(dbc.NavLink("Vergleich der Stellenanzeigen", id="nav-vergleich", href="#")),
                            dbc.NavItem(dbc.NavLink("Admin Bereich", id="nav-admin", href="#")),
                        ],
                        className="ms-auto",  # Right-align nav items
                        navbar=True
                    ),
                    id="navbar-collapse",
                    navbar=True,
                ),
            ],
            fluid=True,
        ),
        color="#6d6d6d",
        dark=True,
    ),

    # Main container with two-column layout
    html.Div([
        # Left column for filters (20% width) – ID used for visibility toggling
        html.Div(id='filter-spalte', children=[
            # Global filters
            html.Div([

                # Filter: Job Portal
                html.Div([
                    html.Label("Jobportal", style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-job-portal',
                        options=[{'label': opt, 'value': opt} for opt in job_portale if pd.notna(opt)],
                        placeholder="Wähle Jobportal",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Filter: Bundesland
                html.Div([
                    html.Label("Bundesland", style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-bundesland',
                        options=[{'label': opt, 'value': opt} for opt in bundeslaender if pd.notna(opt)],
                        placeholder="Wähle Bundesland",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Filter: date (Month selection)
                html.Div([
                    html.Label("Monat", style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-monat',
                        options=[{'label': pd.to_datetime(monat).strftime('%B %Y'), 'value': monat}
                                 for monat in sorted(datenrahmen['Datum'].dt.strftime('%Y-%m').unique())],
                        placeholder="Wähle Monat",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Filter: Branche
                html.Div([
                    html.Label("Branche", style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-branche',
                        options=[{'label': opt, 'value': opt} for opt in branchen],
                        placeholder="Wähle Branche(n)",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Filter: Position
                html.Div([
                    html.Label("Position", style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-position',
                        options=[{'label': opt, 'value': opt} for opt in positionen if pd.notna(opt)],
                        placeholder="Wähle Position",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Filter: Unternehmensgröße
                html.Div([
                    html.Label("Unternehmensgröße",
                               style={'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='filter-unternehmensgroesse',
                        options=[{'label': opt, 'value': opt} for opt in unternehmensgroessen],
                        # Verwendet die sortierte Liste
                        placeholder="Wähle Unternehmensgröße",
                        multi=True,
                        style={'marginBottom': '15px'}
                    )
                ]),

                # Additional filters: experience, work time model, contract type
                html.Div([

                    # Filter: Berufserfahrung
                    html.Div([
                        html.Label("Berufserfahrung vorausgesetzt?", style={
                            'fontSize': '14px',
                            'marginBottom': '5px',
                            'fontWeight': 'bold',
                            'display': 'block'
                        }),
                        dcc.RadioItems(
                            id='filter-berufserfahrung',
                            options=[
                                {'label': html.Span('Ja', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 1},
                                {'label': html.Span('Nein', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 0}
                            ],
                            value=None,
                            inline=True,
                            style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'top'},
                            labelStyle={'marginRight': '15px', 'display': 'inline-block', 'width': '80px'}
                        )
                    ], style={'marginBottom': '15px'}),

                    # Filter: Zeitmodell
                    html.Div([
                        html.Label("Zeitmodell", style={
                            'fontSize': '14px',
                            'marginBottom': '5px',
                            'fontWeight': 'bold',
                            'display': 'block'
                        }),
                        dcc.RadioItems(
                            id='filter-zeitmodell',
                            options=[
                                {'label': html.Span('Vollzeit', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 'Vollzeit'},
                                {'label': html.Span('Teilzeit', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 'Teilzeit'}
                            ],
                            value=None,
                            inline=True,
                            style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'top'},
                            labelStyle={'marginRight': '15px', 'display': 'inline-block', 'width': '80px'}
                        )
                    ], style={'marginBottom': '15px'}),

                    # Filter: Beschäftigungsart
                    html.Div([
                        html.Label("Beschäftigungsart", style={
                            'fontSize': '14px',
                            'marginBottom': '5px',
                            'fontWeight': 'bold',
                            'display': 'block'
                        }),
                        dcc.RadioItems(
                            id='filter-beschaeftigungsart',
                            options=[
                                {'label': html.Span('befristet', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 'befristet'},
                                {'label': html.Span('unbefristet', style={'width': '80px', 'display': 'inline-block'}),
                                 'value': 'unbefristet'}
                            ],
                            value=None,
                            inline=True,
                            style={'display': 'inline-block', 'marginLeft': '10px', 'verticalAlign': 'top'},
                            labelStyle={'marginRight': '15px', 'display': 'inline-block', 'width': '80px'}
                        )
                    ], style={'marginBottom': '15px'})
                ]),

                # "Alle Filter löschen" Button
                html.Div([
                    dbc.Button(
                        'Alle Filter löschen',
                        id='filter-zuruecksetzen',
                        color='danger',
                        style={'width': '100%'}
                    )
                ])
            ], style={
                'padding': '20px',
                'backgroundColor': '#f8f9fa',
                'borderRadius': '5px',
                'height': '90vh',  # Reduced height to 90vh for better layout on smaller screens
                'overflowY': 'auto'  # Adds scrollbar if content overflows
            })
        ], style={
            'width': '20%',
            'padding': '20px',
            'height': '90vh',
            'boxSizing': 'border-box'  # Ensures padding is included in width calculation
        }),

        # Right column for dynamic dashboard content (takes remaining space)
        html.Div(id='hauptinhalt', style={
            'flex': '1',  # Occupies remaining space
            'padding': '20px',
            'minWidth': '0',  # Prevents overflow issues with flex layout
            'height': '90vh',
            'overflowY': 'auto'   # Adds scrollbar for long content
        })
    ], style={
        'display': 'flex',
        'width': '100%',
        'height': '90vh',
        'margin': '0',
        'padding': '0'
    })
])


# Callback to update the dashboard content based on the navigation bar selection
@app.callback(
    Output('hauptinhalt', 'children'),
    [Input('nav-allgemein', 'n_clicks'),
     Input('nav-vergleich', 'n_clicks'),
     Input('nav-admin', 'n_clicks')],
    prevent_initial_call=False
)

def aktualisiere_dashboard(nav_allgemein, nav_vergleich, nav_admin):
    """
    Dynamically updates the main content area of the dashboard based on the selected navigation item.

    This function reacts to user clicks on the navigation bar and displays the corresponding dashboard section:

    - **Allgemeine Analyse der Stellenanzeigen** loads the general job analysis dashboard.
    - **Vergleich der Stellenanzeigen** loads the comparison dashboard.
    - **Admin Bereich** loads the admin section.

    Parameters:
        nav_allgemein (int or None): Number of clicks on the "General Analysis" nav item.
        nav_vergleich (int or None): Number of clicks on the "Comparison" nav item.
        nav_admin (int or None): Number of clicks on the "Admin" nav item.

    Returns:
        dash.html.Div: The appropriate layout to render in the 'hauptinhalt' div.
    """

    df = load_database()

    # Return error message if data could not be loaded
    if df is None or df.empty:
        return html.Div("Daten konnten nicht geladen werden.", style={"color": "red"})

    # Initialize helper variables based on available dataframe columns
    job_portale = sorted(df['Portal_Name'].unique()) if 'Portal_Name' in df.columns else []
    bundeslaender = sorted(df['Bundesland'].unique()) if 'Bundesland' in df.columns else []
    branchen = sorted(df['Kategorie'].unique()) if 'Kategorie' in df.columns else []
    positionen = sorted(df['Position'].unique()) if 'Position' in df.columns else []
    unternehmensgroessen = sorted(df['Unternehmensgröße'].unique()) if 'Unternehmensgröße' in df.columns else []
    unternehmen = sorted(df['Unternehmen'].unique()) if 'Unternehmen' in df.columns else []

    # Load the general dashboard layout by default or if no button has been clicked
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
        return get_general_dashboard_layout(
            datenrahmen=df,
            encoded_image="",
            job_portale=job_portale,
            bundeslaender=bundeslaender,
            branchen=branchen,
            positionen=positionen,
            unternehmensgroessen=unternehmensgroessen
        )
    # Identify which navigation button was clicked
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Load corresponding dashboard layout based on navigation item
    if button_id == 'nav-allgemein':
        return get_general_dashboard_layout(
            datenrahmen=df,
            encoded_image="",
            job_portale=job_portale,
            bundeslaender=bundeslaender,
            branchen=branchen,
            positionen=positionen,
            unternehmensgroessen=unternehmensgroessen
        )
    elif button_id == 'nav-vergleich':
        return get_comparison_dashboard_layout(
            datenrahmen=df,
            unternehmen=unternehmen
        )
    elif button_id == 'nav-admin':
        return get_admin_dashboard_layout()


# Callback for admin password verification
@app.callback(
    [Output('admin-inhalt', 'style'),
     Output('passwort-modal', 'is_open'),
     Output('passwort-feedback', 'children')],
    [Input('passwort-bestaetigen', 'n_clicks'),
     Input('admin-passwort-eingabe', 'n_submit')],
    [State('admin-passwort-eingabe', 'value')]
)
def passwort_prüfen(n_clicks, n_submit, passwort):
    """
    Verifies the entered password to grant access to the admin section of the dashboard.

    This callback checks whether a user has clicked the "Bestätigen" button or submitted the password field
    via Enter key. If the provided password matches the predefined correct password, the admin section becomes visible.
    Otherwise, the password modal remains open and an error message is shown.

    The correct password is currently hardcoded in the application and can be freely defined by the developer.
    It is strongly recommended to use a more secure and complex password than the placeholder used here,
    especially in production environments.

    Parameters:
        n_clicks (int or None): Number of clicks on the "Confirm Password" button.
        n_submit (int or None): Number of submissions via Enter key from the password input.
        passwort (str or None): The user-entered password string.

    Returns:
        Tuple:
            - dict: CSS style to show/hide the admin content div.
            - bool: Flag to open/close the password modal.
            - str: Feedback message displayed to the user in case of incorrect password.
    """

    ctx = dash.callback_context # Context to identify what triggered the callback

    # Only proceed if the callback was triggered
    if not ctx.triggered:
        return {'display': 'none'}, True, ""

    # Determine the triggering element (button or submit field)
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id not in ['passwort-bestaetigen', 'admin-passwort-eingabe']:
        return {'display': 'none'}, True, ""

    # Define the correct password (replace with more secure logic in production)
    korrektes_passwort = "123"

    # Check if entered password is correct
    if passwort == korrektes_passwort:
        return {'display': 'flex', 'width': '100%'}, False, "" # Show admin section, close modal
    else:
        return {'display': 'none'}, True, "Passwort ist falsch. Bitte erneut versuchen." # Keep modal open, show error


# Callbacks – General Dashboard
# Callback for updating figures and KPIs in the general dashboard
@app.callback(
    [Output('karte', 'figure'),
     Output('unternehmensgroesse-balken', 'figure'),
     Output('trend-linie', 'figure'),
     Output('gesamtanzahl-karte', 'children'),
     Output('anzahl-jobtitel', 'children'),
     Output('anzahl-unternehmen', 'children')],
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-position', 'value'),
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value')]
)
def aktualisiere_allgemeine_diagramme(job_portal, bundesland, beschaeftigungsart, position, zeitmodell,
                                      berufserfahrung, monate, unternehmensgroesse, branche):
    """
    Filters the dataset based on user selections in the dashboard and returns updated visualizations and KPIs.

    This callback function processes multiple user-defined filters and applies them to the underlying job advertisement
    dataset. Based on the filtered data, it generates and returns updated dashboard elements that provide both graphical
    and numerical insights.

    The function produces the following outputs:

    - A **choropleth map** showing the number of job advertisements per German federal state.
      Nationwide advertisements ("bundesweit") are programmatically duplicated across all states.
    - Three **key performance indicators (KPIs)**: total number of unique advertisements, number of unique job titles, and number of unique companies.
    - A **bar chart** displaying the distribution of job advertisements by company size, ordered by defined size categories.
    - A **time-series line chart** illustrating the trend of job advertisements over time, differentiated by portal.

    Parameters:
        job_portal (list[str]): Selected job portals (e.g., 'Stepstone', 'Indeed').
        bundesland (list[str]): Selected German federal states.
        beschaeftigungsart (str): Selected type of employment (e.g., 'befristet', 'unbefristet').
        position (list[str]): Selected job positions.
        zeitmodell (str): Selected working time model (e.g., 'Vollzeit', 'Teilzeit').
        berufserfahrung (bool): Whether the position requires prior work experience.
        monate (list[str]): Selected months (format: 'YYYY-MM').
        unternehmensgroesse (list[str]): Selected company size categories.
        branche (list[str]): Selected industry categories.
    Returns:
        tuple: (map figure, bar chart, line chart, total count, job title count, company count)
    """

    # Create a working copy of the global dataframe
    gefilterter_datenrahmen = datenrahmen.copy()

    # Sequentially apply all filters
    if job_portal:
        gefilterter_datenrahmen = gefilterter_datenrahmen[gefilterter_datenrahmen['Portal_Name'].isin(job_portal)]

    if bundesland:
        gefilterter_datenrahmen = gefilterter_datenrahmen[gefilterter_datenrahmen['Bundesland'].isin(bundesland)]

    if beschaeftigungsart:
        gefilterter_datenrahmen = gefilterter_datenrahmen[
            gefilterter_datenrahmen['Beschäftigungsart'].isin(beschaeftigungsart_mapping.get(beschaeftigungsart, []))]

    if position:
        gefilterter_datenrahmen = gefilterter_datenrahmen[gefilterter_datenrahmen['Position'].isin(position)]

    if zeitmodell:
        gefilterter_datenrahmen = gefilterter_datenrahmen[gefilterter_datenrahmen['Zeitmodell'] == zeitmodell]

    if berufserfahrung is not None:
        gefilterter_datenrahmen = gefilterter_datenrahmen[
            gefilterter_datenrahmen['Berufserfahrung_vorausgesetzt'] == berufserfahrung]

    if monate:
        gefilterter_datenrahmen = gefilterter_datenrahmen[
            gefilterter_datenrahmen['Datum'].dt.strftime('%Y-%m').isin(monate)]

    if unternehmensgroesse:
        gefilterter_datenrahmen = gefilterter_datenrahmen[
            gefilterter_datenrahmen['Unternehmensgröße'].isin(unternehmensgroesse)]

    if branche:
        gefilterter_datenrahmen = gefilterter_datenrahmen[gefilterter_datenrahmen['Kategorie'].isin(branche)]

    # Identify unique job ads using MongoDB_ID
    eindeutige_anzeigen = gefilterter_datenrahmen.drop_duplicates(subset=['MongoDB_ID'])

    # KPIs
    gesamtanzahl = len(eindeutige_anzeigen)
    anzahl_jobtitel = eindeutige_anzeigen['Job_Titel'].nunique()
    anzahl_unternehmen = eindeutige_anzeigen['Unternehmen'].nunique()

    # Handle 'bundesweit' cases by duplicating ads across all states
    #  List of all federal states
    alle_bundeslaender = ['Baden-Württemberg', 'Bayern', 'Berlin', 'Brandenburg', 'Bremen',
                          'Hamburg', 'Hessen', 'Mecklenburg-Vorpommern', 'Niedersachsen',
                          'Nordrhein-Westfalen', 'Rheinland-Pfalz', 'Saarland', 'Sachsen',
                          'Sachsen-Anhalt', 'Schleswig-Holstein', 'Thüringen']

    # Create a copy for the map display only
    karten_daten = gefilterter_datenrahmen.copy()

    # Find nationwide job advertisements
    bundesweite_anzeigen = karten_daten[karten_daten['Bundesland'] == 'bundesweit']

    if not bundesweite_anzeigen.empty:
        # Remove the original nationwide entries
        karten_daten = karten_daten[karten_daten['Bundesland'] != 'bundesweit']

        # For each nationwide job advertisement: Add one entry per federal state
        neue_eintraege = []
        for _, zeile in bundesweite_anzeigen.iterrows():
            for bundesland in alle_bundeslaender:
                neue_zeile = zeile.copy()
                neue_zeile['Bundesland'] = bundesland
                neue_eintraege.append(neue_zeile)

        # Add the new entries to the DataFrame
        if neue_eintraege:
            karten_daten = pd.concat([karten_daten, pd.DataFrame(neue_eintraege)], ignore_index=True)

    # Always generate the job ad map, even if there are no nationwide postings
    karten_figur = px.choropleth(
        karten_daten,
        geojson=deutschland_geojson,
        locations='Bundesland',
        featureidkey='properties.name',
        color=karten_daten.groupby('Bundesland')['Bundesland'].transform('size'),
        color_continuous_scale=[COLOR_1, COLOR_2, COLOR_3, COLOR_4],
    )

    karten_figur.update_geos(
        visible=True,
        resolution=50,
        showcountries=True,
        countrycolor='Black',
        showsubunits=True,
        subunitcolor='Gray',
        center={"lat": 51.1657, "lon": 10.4515},
        projection_type="mercator",
        fitbounds="locations"
    )
    karten_figur.update_coloraxes(cmin=0, cmax=karten_daten.groupby('Bundesland').size().max())
    karten_figur.update_traces(hovertemplate="<b>%{location}</b>: %{z}<extra></extra>")

    # Company Size Bar Chart
    # 1. Prepare and filter data
    unternehmensgroesse_data = (
        eindeutige_anzeigen.groupby('Unternehmensgröße')
        .size()
        .reset_index(name='Anzahl')
        .rename(columns={'Unternehmensgröße': 'Kategorie'})
    )

    # 2. Sorting according to predefined sequence
    vorhandene_kategorien = [
        kategorie for kategorie in unternehmensgroessen_sortiert
        if kategorie in unternehmensgroesse_data['Kategorie'].values
    ]

    # 3. Create data in the desired order
    unternehmensgroesse_data['Kategorie'] = pd.Categorical(
        unternehmensgroesse_data['Kategorie'],
        categories=vorhandene_kategorien,
        ordered=True
    )
    unternehmensgroesse_data = unternehmensgroesse_data.sort_values('Kategorie')

    # 4. Create diagram
    unternehmensgroesse_figur = px.bar(
        unternehmensgroesse_data,
        x='Kategorie',
        y='Anzahl',
        title='',
        labels={'Kategorie': 'Unternehmensgröße', 'Anzahl': 'Anzahl Stellenanzeigen'},
        category_orders={'Kategorie': vorhandene_kategorien}
    )

    # 5. Customize design
    unternehmensgroesse_figur.update_traces(
        marker_color=COLOR_1,
        hovertemplate="Anzahl: %{y}<extra></extra>",
        showlegend=False
    )

    # 6. Optimize layout
    unternehmensgroesse_figur.update_layout(
        xaxis_title='Unternehmensgröße',
        yaxis_title='Anzahl Stellenanzeigen',
        margin={'t': 30, 'b': 100},  # Platz für x-Achsenbeschriftungen
        xaxis={'tickangle': 45}  # Beschriftungen schräg stellen für bessere Lesbarkeit
    )

    # Job Ad Trend Line Char
    trend_data = (
        gefilterter_datenrahmen
        .drop_duplicates(subset=['MongoDB_ID', 'Portal_Name'])
        .groupby(['Datum', 'Portal_Name'])
        .size()
        .reset_index(name='Anzahl')
    )
    trend_figur = px.line(
        trend_data,
        x='Datum',
        y='Anzahl',
        color='Portal_Name',
        color_discrete_map={
            'stepstone': COLOR_1,
            'indeed': COLOR_3
        },
    )

    # Always display points (even for individual data points)
    trend_figur.update_traces(
        mode='lines+markers',  # Always show lines + markers
        marker=dict(size=8),
        hovertemplate='<b>%{fullData.name}</b>: %{y}<extra></extra>'
    )

    # Layout adjustments
    trend_figur.update_layout(
        yaxis_title='Anzahl Stellenanzeigen',
        xaxis_title='Datum',
        yaxis=dict(
            # Automatic tick calculation with nicer intervals
            tickmode='auto',
            autorange=True,
            rangemode='tozero',
            # Do not display decimal places that are too small
            tickformat=',.0f'
        ),
        xaxis=dict(
            tickformat='%d.%m.%Y'
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='white',
            font_color='black'
        ),
        margin=dict(t=30),
        legend_title_text='Jobportal'
    )

    # Hover format
    trend_figur.update_traces(
        hovertemplate='<b>%{fullData.name}</b>: %{y}<extra></extra>'
    )

    return (karten_figur, unternehmensgroesse_figur, trend_figur,
            f"{gesamtanzahl}", f"{anzahl_jobtitel}", f"{anzahl_unternehmen}")


# Callback to reset all filter dropdowns when the reset button is clicked
@app.callback(
    [Output('filter-job-portal', 'value'),
     Output('filter-bundesland', 'value'),
     Output('filter-beschaeftigungsart', 'value'),
     Output('filter-position', 'value'),
     Output('filter-zeitmodell', 'value'),
     Output('filter-berufserfahrung', 'value'),
     Output('filter-monat', 'value'),
     Output('filter-unternehmensgroesse', 'value'),
     Output('filter-branche', 'value')],  # <-- Korrekt integriert
    [Input('filter-zuruecksetzen', 'n_clicks')]
)
def reset_filters(n_clicks):
    """
    Clears all selected global filter values when the "Alle Filter löschen" button is clicked.

    Parameters:
        n_clicks (int or None): Number of times the reset button has been clicked.

    Returns:
        Tuple of default (empty or None) values for all filters to reset the UI state.
    """

    if n_clicks is not None:
        # Return default (empty) values for all filters
        return [], [], None, [], None, None, [], [], []  # 9 Rückgabewerte
    # Also return default values if button hasn't been clicked yet (initial state)
    return [], [], None, [], None, None, [], [], []


# Callback to update the available job portal options based on current filter selections
@app.callback(
    Output('filter-job-portal', 'options'),
    [Input('filter-bundesland', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-position', 'value'),
     Input('filter-unternehmensgroesse', 'value')]
)
def update_job_portal_options(bundesland, monat, branche, position, unternehmensgroesse):
    """
    Dynamically updates the job portal filter options based on other selected filters.

    Only job portals that are present in the currently filtered dataset will be displayed
    as selectable options in the dropdown menu.

    Parameters:
        bundesland (list or None): Selected federal states.
        monat (list or None): Selected months (format 'YYYY-MM').
        branche (list or None): Selected industries/categories.
        position (list or None): Selected job positions.
        unternehmensgroesse (list or None): Selected company size categories.

    Returns:
        list: A list of dictionaries with available job portal options for the dropdown.
    """
    # Start with a copy of the full dataset
    gefiltert = datenrahmen.copy()

    # Apply each filter if selected
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if monat:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monat)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if position:
        gefiltert = gefiltert[gefiltert['Position'].isin(position)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]

    # Extract available job portals after filtering
    verfuegbare_portale = gefiltert['Portal_Name'].unique()
    # Create dropdown option list (excluding missing values)
    optionen = [{'label': portal, 'value': portal} for portal in sorted(verfuegbare_portale) if pd.notna(portal)]
    return optionen


# Callback to update the available federal state (Bundesland) options based on current filter selections
@app.callback(
    Output('filter-bundesland', 'options'),
    [Input('filter-job-portal', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-position', 'value'),
     Input('filter-unternehmensgroesse', 'value')]
)
def update_bundesland_options(job_portal, monat, branche, position, unternehmensgroesse):
    """
    Dynamically updates the federal state (Bundesland) filter options based on other selected filters.

    Only states present in the currently filtered dataset will be shown as options.
    This ensures that users can only select from values relevant to their current context.

    Parameters:
        job_portal (list or None): Selected job portals.
        monat (list or None): Selected months (format 'YYYY-MM').
        branche (list or None): Selected industries/categories.
        position (list or None): Selected job positions.
        unternehmensgroesse (list or None): Selected company size categories.

    Returns:
        list: A list of dictionaries with available federal state options for the dropdown.
    """
    # Start with a full copy of the dataset
    gefiltert = datenrahmen.copy()

    # Apply each selected filter
    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if monat:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monat)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if position:
        gefiltert = gefiltert[gefiltert['Position'].isin(position)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]

    # Only include entries from Germany and extract unique federal states
    verfuegbare_bundeslaender = gefiltert[gefiltert['Land'] == 'Deutschland']['Bundesland'].unique()
    # Create dropdown option list (excluding missing values)
    optionen = [{'label': bundesland, 'value': bundesland} for bundesland in sorted(verfuegbare_bundeslaender) if
                pd.notna(bundesland)]
    return optionen


# Callback to update the available month filter options based on current filter selections
@app.callback(
    Output('filter-monat', 'options'),
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-position', 'value'),
     Input('filter-unternehmensgroesse', 'value')]
)
def update_monat_options(job_portal, bundesland, branche, position, unternehmensgroesse):
    """
    Dynamically updates the month filter options based on other selected filters.

    Only months contained in the filtered results will be offered as selectable options.
    The displayed labels are formatted as 'Month Year' (e.g. May 2025) to ensure clarity and improve user experience.

    This formatting decision was made in consultation with PwC to align with their preferred reporting structure.
    Since day-level granularity was not required for the analysis, a month-based view was intentionally implemented
    to simplify selection and interpretation.

    Parameters:
        job_portal (list or None): Selected job portals.
        bundesland (list or None): Selected federal states.
        branche (list or None): Selected industries/categories.
        position (list or None): Selected job positions.
        unternehmensgroesse (list or None): Selected company size categories.

    Returns:
        list: A list of dictionaries with available month options for the dropdown,
              where 'label' is a formatted month name and 'value' is the 'YYYY-MM' string.
    """
    # Start with a full copy of the dataset
    gefiltert = datenrahmen.copy()

    # Apply each selected filter
    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if position:
        gefiltert = gefiltert[gefiltert['Position'].isin(position)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]

    # Extract unique months in 'YYYY-MM' format and sort them
    verfuegbare_monate = sorted(gefiltert['Datum'].dt.strftime('%Y-%m').unique())
    # Create dropdown option list with formatted month labels
    optionen = [{'label': pd.to_datetime(monat).strftime('%B %Y'), 'value': monat} for monat in verfuegbare_monate]
    return optionen


# Callback to update the available "Branchen"/industry filter options based on current filter selections
@app.callback(
    Output('filter-branche', 'options'),
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-position', 'value'),
     Input('filter-unternehmensgroesse', 'value')]
)
def update_branche_options(job_portal, bundesland, monat, position, unternehmensgroesse):
    """
    Dynamically updates the industry filter options based on other selected filters.

    The list of industries is predefined based on an analysis of the existing dataset.
    Only industries present in the currently filtered dataset will be made available in the dropdown.

    Parameters:
        job_portal (list or None): Selected job portals.
        bundesland (list or None): Selected federal states.
        monat (list or None): Selected months in 'YYYY-MM' format.
        position (list or None): Selected job positions.
        unternehmensgroesse (list or None): Selected company size categories.

    Returns:
        list: A list of dictionaries with available industry/category options for the dropdown,
              where each dictionary contains 'label' and 'value' keys with the industry name.
    """
    # Start with a full copy of the dataset
    gefiltert = datenrahmen.copy()

    # Apply filters based on current selections
    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if monat:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monat)]
    if position:
        gefiltert = gefiltert[gefiltert['Position'].isin(position)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]

    # Extract unique, non-null industry names and sort them
    verfuegbare_branchen = gefiltert['Kategorie'].dropna().unique()
    # Create dropdown option list with industry names
    optionen = [{'label': branche, 'value': branche} for branche in sorted(verfuegbare_branchen)]
    return optionen


# Callback to update the available job position filter options based on current filter selections
@app.callback(
    Output('filter-position', 'options'),
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-unternehmensgroesse', 'value')]
)
def update_position_options(job_portal, bundesland, monat, branche, unternehmensgroesse):
    """
    Dynamically updates the job position filter options based on other selected filters.

    Job positions are shown only if they exist within the current filter selection.

    Parameters:
        job_portal (list or None): Selected job portals.
        bundesland (list or None): Selected federal states.
        monat (list or None): Selected months in 'YYYY-MM' format.
        branche (list or None): Selected industries/categories.
        unternehmensgroesse (list or None): Selected company size categories.

    Returns:
        list: A list of dictionaries with available job position options for the dropdown,
              each containing 'label' and 'value' keys with the position name.
    """
    # Start with a full copy of the dataset
    gefiltert = datenrahmen.copy()

    # Apply filters based on current selections
    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if monat:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monat)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]

    # Extract unique, non-null job positions and sort them
    verfuegbare_positionen = gefiltert['Position'].dropna().unique()
    # Create dropdown option list with job position names
    optionen = [{'label': position, 'value': position} for position in sorted(verfuegbare_positionen)]
    return optionen


# Callback to update the company size filter options based on current filter selections
@app.callback(
    Output('filter-unternehmensgroesse', 'options'),
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-position', 'value')]
)
def update_unternehmensgroesse_options(job_portal, bundesland, monat, branche, position):
    """
    Dynamically updates the available company size options based on other selected filters.

    Displayed company sizes are limited to those included in the active dataset view.

    To maintain a consistent and intuitive user experience, the returned company size options
    follow a predefined logical order - from smallest to largest company sizes - excluding null or non-occurring values in the current filter context.

    Parameters:
        job_portal (list or None): Selected job portals.
        bundesland (list or None): Selected federal states.
        monat (list or None): Selected months in 'YYYY-MM' format.
        branche (list or None): Selected industries/categories.
        position (list or None): Selected job positions.

    Returns:
        list: A list of dictionaries with available company size options for the dropdown,
              each containing 'label' and 'value' keys with the company size name.
    """
    # Start with full dataset copy
    gefiltert = datenrahmen.copy()

    # Apply filters based on current selections
    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if monat:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monat)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if position:
        gefiltert = gefiltert[gefiltert['Position'].isin(position)]

    # Get unique, non-null company sizes from filtered data
    vorhandene_groessen = gefiltert['Unternehmensgröße'].dropna().unique()
    # Keep only company sizes that exist in the filtered data,
    # preserving the predefined order in unternehmensgroessen_sortiert
    unternehmensgroessen = [groesse for groesse in unternehmensgroessen_sortiert if groesse in vorhandene_groessen]
    # Create dropdown option list
    optionen = [{'label': groesse, 'value': groesse} for groesse in unternehmensgroessen]
    return optionen


# Callbacks "Vergleich der Stellenanzeigen"
# Callback for the comparison dashboard
@app.callback(
    [Output('verguetungen-balken-links', 'figure'),
     Output('verguetungen-balken-rechts', 'figure'),
     Output('titel-links', 'children'),
     Output('titel-rechts', 'children')],
    [Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-position', 'value'),  # Hinzugefügt
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value'),
     Input('filter-job-titel-links', 'value'),
     Input('filter-unternehmen-links', 'value'),
     Input('filter-job-titel-rechts', 'value'),
     Input('filter-unternehmen-rechts', 'value')]
)
def aktualisiere_verguetungen(job_portal, bundesland, beschaeftigungsart, position, zeitmodell, berufserfahrung, monate,
                              unternehmensgroesse, branche, job_titel_links, unternehmen_links, job_titel_rechts,
                              unternehmen_rechts):
    """
    Updates the job advertisement comparison section ("Vergleich der Stellenanzeigen") of the dashboard based on selected filters.

    This callback processes user-defined filter selections to dynamically generate two side-by-side
    bar charts, each representing attributes from three predefined compensation-related categories
    for different job titles or companies.

    The function proceeds in several steps:

    1. **Column preparation**:
       It first checks which categories (financial compensation, benefits, and workplace environment)
       are available in the dataset to avoid referencing missing data.

    2. **Label mapping**:
       Technical column names are mapped to readable, user-facing labels for display in the charts.

    3. **Data filtering (left and right)**:
       The dataset is filtered independently for the left and right views using the same filter set.
       This enables the comparison of two targeted market segments.

    4. **Deduplication**:
       Duplicate job advertisements are removed using a unique identifier (`MongoDB_ID`) to ensure
       accurate visualizations and counts.

    5. **Job count calculation**:
       For both sides, the number of unique advertisements is calculated and included in the chart titles.

    The comparison is visualized using bar charts, which were selected for their clarity in presenting
    categorical data. This format allows for intuitive side-by-side comparison and supports a clear visual representation of differences between the two selected job titles or companies.

    Internally, the function contains a dedicated helper function that generates the individual bar charts.
    This helper handles several specific aspects of the visualization:

    - **Percentage calculation**:
      Compensation attributes are expressed as percentages of the total number of matching job advertisements,
      rather than absolute counts. This approach was implemented in consultation with the supervisors and PwC,
      as it enables more meaningful comparisons between groups of different sizes.

    - **Exclusion of zero values**:
      Attributes with 0% occurrence are excluded from the chart to avoid clutter and improve readability.

    - **Fallback logic**:
      If no data matches the selected filter criteria, a placeholder chart is rendered to indicate the absence of results.

    - **Color scheme by category**:
      Each compensation category (financial, work environment, additional benefits) is represented using a specific
      color from the official PwC color palette to ensure visual consistency with corporate branding.

    Parameters:
        job_portal (list or None): Selected job portals.
        bundesland (list or None): Selected federal states.
        beschaeftigungsart (str or None): Selected type of employment (converted internally).
        position (list or None): Selected job positions.
        zeitmodell (str or None): Selected working time model.
        berufserfahrung (int or None): Required professional experience.
        monate (list or None): Selected months in 'YYYY-MM' format.
        unternehmensgroesse (list or None): Selected company sizes.
        branche (list or None): Selected industries.
        job_titel_links (str or None): Selected job title for left comparison.
        unternehmen_links (str or None): Selected company for left comparison.
        job_titel_rechts (str or None): Selected job title for right comparison.
        unternehmen_rechts (str or None): Selected company for right comparison.

    Returns:
        tuple:
            - figure: Left compensation bar chart figure.
            - figure: Right compensation bar chart figure.
            - str: Title text for the left side.
            - str: Title text for the right side.
    """

    # Use only existing columns in the dataframe
    vorhandene_spalten = datenrahmen.columns.tolist()

    # Define categories with filtering on existing columns
    finanzielle_spalten = [col for col in [
        'Gehalt_anhand_von_Tarifklassen',
        'Überstundenvergütung',
        'Gehaltserhöhungen',
        'Aktienoptionen_Gewinnbeteiligung',
        'Boni',
        'Sonderzahlungen',
        '13. Gehalt',
        'Betriebliche_Altersvorsorge'
    ] if col in vorhandene_spalten]

    arbeitsumfeld_spalten = [col for col in [
        'Flexible_Arbeitsmodelle',
        'Homeoffice',
        'Arbeitsumfeld_Ausstattung'
    ] if col in vorhandene_spalten]

    zusatzleistungen_spalten = [col for col in [
        'Weiterbildung_und_Entwicklungsmöglichkeiten',
        'Gesundheit_und_Wohlbefinden',
        'Finanzielle_Vergünstigungen',
        'Mobilitätsangebote',
        'Verpflegung',
        'Zusätzliche_Urlaubstage',
        'Familien_Unterstützung',
        'Onboarding_und_Mentoring_Programme',
        'Teamevents_Firmenfeiern'
    ] if col in vorhandene_spalten]

    # Rreadable labels for compensation types
    verguetungs_labels = {
        'Gehalt_anhand_von_Tarifklassen': 'Gehalt nach Tarifklassen',
        'Überstundenvergütung': 'Überstundenvergütung',
        'Gehaltserhöhungen': 'Gehaltserhöhungen',
        'Aktienoptionen_Gewinnbeteiligung': 'Aktienoptionen/Gewinnbeteiligung',
        'Boni': 'Boni',
        'Sonderzahlungen': 'Sonderzahlungen',
        '13. Gehalt': '13. Gehalt',
        'Betriebliche_Altersvorsorge': 'Betriebliche Altersvorsorge',
        'Flexible_Arbeitsmodelle': 'Flexible Arbeitsmodelle',
        'Homeoffice': 'Homeoffice',
        'Arbeitsumfeld_Ausstattung': 'Arbeitsumfeld Ausstattung',
        'Weiterbildung_und_Entwicklungsmöglichkeiten': 'Weiterbildung',
        'Gesundheit_und_Wohlbefinden': 'Gesundheit & Wohlbefinden',
        'Finanzielle_Vergünstigungen': 'Finanzielle Vergünstigungen',
        'Mobilitätsangebote': 'Mobilitätsangebote',
        'Verpflegung': 'Verpflegung',
        'Zusätzliche_Urlaubstage': 'Zusätzliche Urlaubstage',
        'Familien_Unterstützung': 'Familienunterstützung',
        'Onboarding_und_Mentoring_Programme': 'Onboarding/Mentoring',
        'Teamevents_Firmenfeiern': 'Teamevents/Firmenfeiern'
    }

    # Filter data for left side
    gefiltert_links = datenrahmen.copy()
    if job_portal:
        gefiltert_links = gefiltert_links[gefiltert_links['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert_links = gefiltert_links[gefiltert_links['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        # Convert string to list for filtering
        beschaeftigungsarten = beschaeftigungsart_mapping.get(beschaeftigungsart, [])
        gefiltert_links = gefiltert_links[gefiltert_links['Beschäftigungsart'].isin(beschaeftigungsarten)]
    if position:
        gefiltert_links = gefiltert_links[gefiltert_links['Position'].isin(position)]
    if zeitmodell:
        gefiltert_links = gefiltert_links[gefiltert_links['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert_links = gefiltert_links[gefiltert_links['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert_links = gefiltert_links[gefiltert_links['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert_links = gefiltert_links[gefiltert_links['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert_links = gefiltert_links[gefiltert_links['Kategorie'].isin(branche)]
    if job_titel_links:
        gefiltert_links = gefiltert_links[gefiltert_links['Job_Titel'] == job_titel_links]
    if unternehmen_links:
        gefiltert_links = gefiltert_links[gefiltert_links['Unternehmen'] == unternehmen_links]

    # Filter data for right side
    gefiltert_rechts = datenrahmen.copy()
    if job_portal:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        # Convert string to list for filtering
        beschaeftigungsarten = beschaeftigungsart_mapping.get(beschaeftigungsart, [])
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Beschäftigungsart'].isin(beschaeftigungsarten)]
    if position:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Position'].isin(position)]
    if zeitmodell:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Kategorie'].isin(branche)]
    if job_titel_rechts:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Job_Titel'] == job_titel_rechts]
    if unternehmen_rechts:
        gefiltert_rechts = gefiltert_rechts[gefiltert_rechts['Unternehmen'] == unternehmen_rechts]

    # Remove duplicates based on MongoDB_ID for counting
    eindeutige_links = gefiltert_links.drop_duplicates(subset=['MongoDB_ID'])
    eindeutige_rechts = gefiltert_rechts.drop_duplicates(subset=['MongoDB_ID'])

    anzahl_links = len(eindeutige_links)
    anzahl_rechts = len(eindeutige_rechts)

    # Create titles for both sides
    titel_links = f"Betrifft hier {anzahl_links} Jobs"
    titel_rechts = f"Betrifft hier {anzahl_rechts} Jobs"

    def erstelle_verguetungen_figur(daten, anzahl):
        """
        Helper function to create a horizontal bar chart for compensation types.

        Parameters:
        - daten: filtered DataFrame to use for the plot
        - anzahl: total number of unique jobs in the filtered data for percentage calculation

        Returns:
        - Plotly figure object representing the bar chart
        """
        # Remove duplicates for consistent calculation
        eindeutige_daten = daten.drop_duplicates(subset=['MongoDB_ID'])

        # List for all category data
        alle_kategorien_daten = []

        # 1. Process financial compensations
        if finanzielle_spalten:
            finanzielle_daten = eindeutige_daten[finanzielle_spalten].sum().reset_index()
            finanzielle_daten.columns = ['Vergütungsart', 'Anzahl']
            finanzielle_daten['Anzahl'] = (finanzielle_daten['Anzahl'] / anzahl * 100).round(2)
            finanzielle_daten['Kategorie'] = 'Finanzielle Vergütung'
            finanzielle_daten['Vergütungsart'] = finanzielle_daten['Vergütungsart'].map(verguetungs_labels)
            # Filter out zero values
            finanzielle_daten = finanzielle_daten[finanzielle_daten['Anzahl'] > 0]
            alle_kategorien_daten.append(finanzielle_daten)

        # 2. Process work environment
        if arbeitsumfeld_spalten:
            arbeitsumfeld_daten = eindeutige_daten[arbeitsumfeld_spalten].sum().reset_index()
            arbeitsumfeld_daten.columns = ['Vergütungsart', 'Anzahl']
            arbeitsumfeld_daten['Anzahl'] = (arbeitsumfeld_daten['Anzahl'] / anzahl * 100).round(2)
            arbeitsumfeld_daten['Kategorie'] = 'Arbeitsumfeld'
            arbeitsumfeld_daten['Vergütungsart'] = arbeitsumfeld_daten['Vergütungsart'].map(verguetungs_labels)
            # Filter out zero values
            arbeitsumfeld_daten = arbeitsumfeld_daten[arbeitsumfeld_daten['Anzahl'] > 0]
            alle_kategorien_daten.append(arbeitsumfeld_daten)

        # 3. Process additional benefits
        if zusatzleistungen_spalten:
            zusatzleistungen_daten = eindeutige_daten[zusatzleistungen_spalten].sum().reset_index()
            zusatzleistungen_daten.columns = ['Vergütungsart', 'Anzahl']
            zusatzleistungen_daten['Anzahl'] = (zusatzleistungen_daten['Anzahl'] / anzahl * 100).round(2)
            zusatzleistungen_daten['Kategorie'] = 'Zusatzleistungen'
            zusatzleistungen_daten['Vergütungsart'] = zusatzleistungen_daten['Vergütungsart'].map(verguetungs_labels)
            # Filter out zero values
            zusatzleistungen_daten = zusatzleistungen_daten[zusatzleistungen_daten['Anzahl'] > 0]
            alle_kategorien_daten.append(zusatzleistungen_daten)

        # Combine all categories into one DataFrame
        if alle_kategorien_daten:
            kombiniert = pd.concat(alle_kategorien_daten)
            kombiniert = kombiniert.sort_values('Anzahl', ascending=False)
        else:
            # Fallback: Create empty DataFrame
            kombiniert = pd.DataFrame(columns=['Vergütungsart', 'Anzahl', 'Kategorie'])

        # Define color mapping for each category
        farben = {
            'Finanzielle Vergütung': COLOR_1,
            'Arbeitsumfeld': COLOR_5,
            'Zusatzleistungen': COLOR_4
        }

        # Create the bar chart (only if data is available)
        if not kombiniert.empty:
            figur = px.bar(
                kombiniert,
                y='Vergütungsart',
                x='Anzahl',
                orientation='h',
                color='Kategorie',
                color_discrete_map=farben,
                labels={
                    'Anzahl': 'Anteil der Jobs (%)',
                    'Vergütungsart': 'Art der Vergütung',
                    'Kategorie': 'Kategorie'
                },
                category_orders={"Vergütungsart": kombiniert['Vergütungsart'].tolist()},
                text=kombiniert['Anzahl'].apply(lambda x: f"{x:.2f}%" if x > 0 else "")
            )
        else:
            # Create empty placeholder chart if no data is available
            figur = px.bar(
                pd.DataFrame({'Vergütungsart': ['Keine Daten'], 'Anzahl': [0]}),
                y='Vergütungsart',
                x='Anzahl',
                orientation='h'
            )
        # Update trace styling
        figur.update_traces(
            textfont_size=12,
            textposition='outside',
            cliponaxis=False,
            hovertemplate=None,
            hoverinfo='skip'
        )
        # Update layout for better readability and formatting
        figur.update_layout(
            title_x=0.5,
            yaxis={'categoryorder': 'total ascending'},
            margin={'t': 100, 'l': 150, 'b': 50},  # Add top margin for legend spacing
            showlegend=True,
            legend_title_text='Kategorien',
            plot_bgcolor='#E5ECF6',
            paper_bgcolor='white',
            yaxis_title=None,
            xaxis_title='Anteil der Jobs (%)',
            xaxis=dict(gridcolor='white', showgrid=True),
            uniformtext_minsize=8,
            uniformtext_mode='hide',
            hovermode=False,
            legend=dict(
                orientation='h',      # Horizontal layout
                yanchor='bottom',     # Anchor at bottom
                y=1.02,               # Slightly above the plot
                xanchor='center',     # Center aligned
                x=0.5,                # Position in the middle
                bgcolor='rgba(255,255,255,0.5)',  # Semi-transparent background
            )
        )

        return figur

    # Use filtered datasets (with duplicates removed) to generate bar charts
    figur_links = erstelle_verguetungen_figur(gefiltert_links, anzahl_links)
    figur_rechts = erstelle_verguetungen_figur(gefiltert_rechts, anzahl_rechts)

    return figur_links, figur_rechts, titel_links, titel_rechts


# Callback for the left side
@app.callback(
    Output('filter-unternehmen-links', 'options'),
    [Input('filter-job-titel-links', 'value'),
     Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value')]
)
def update_unternehmen_links(job_titel, job_portal, bundesland, beschaeftigungsart, zeitmodell,
                              berufserfahrung, monate, unternehmensgroesse, branche):
    """
    Updates the list of available companies in the dropdown menu on the left side of the
    "Vergleich der Stellenanzeigen" section of the dashboard.

    The update is based on both the global filter selections and the selected job title for the left comparison view.

    This ensures that the dropdown only displays companies relevant to the specific combination
    of filters currently applied by the user.

    Parameters:
        job_titel (str): Selected job title.
        job_portal (list): List of selected job portals.
        bundesland (list): List of selected federal states.
        beschaeftigungsart (str): Selected type of employment.
        zeitmodell (str): Selected work time model.
        berufserfahrung (bool): Whether professional experience is required.
        monate (list): List of selected months (format 'YYYY-MM').
        unternehmensgroesse (list): List of selected company sizes.
        branche (list): List of selected industry categories.

    Returns:
        list: List of dictionaries with 'label' and 'value' for each available company.
    """
    # Create a copy of the dataset to apply filters
    gefiltert = datenrahmen.copy()

    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        gefiltert = gefiltert[
            gefiltert['Beschäftigungsart'].isin(beschaeftigungsart_mapping.get(beschaeftigungsart, []))]
    if zeitmodell:
        gefiltert = gefiltert[gefiltert['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert = gefiltert[gefiltert['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if job_titel:
        gefiltert = gefiltert[gefiltert['Job_Titel'] == job_titel]

    # Extract available companies
    verfuegbare_unternehmen = gefiltert['Unternehmen'].unique()

    # Create options for dropdown
    optionen = [{'label': unternehmen, 'value': unternehmen}
                for unternehmen in sorted(verfuegbare_unternehmen) if pd.notna(unternehmen)]

    return optionen


# Callback for the right side
@app.callback(
    Output('filter-unternehmen-rechts', 'options'),
    [Input('filter-job-titel-rechts', 'value'),
     Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value')]
)
def update_unternehmen_rechts(job_titel, job_portal, bundesland, beschaeftigungsart, zeitmodell,
                               berufserfahrung, monate, unternehmensgroesse, branche):
    """
    Updates the list of available companies in the dropdown menu on the right side of the
    "Vergleich der Stellenanzeigen" section of the dashboard.

    The update is based on both the global filter selections and the selected job title for the right comparison view.

    Parameters:
        job_titel (str): Selected job title.
        job_portal (list): List of selected job portals.
        bundesland (list): List of selected federal states.
        beschaeftigungsart (str): Selected type of employment.
        zeitmodell (str): Selected work time model.
        berufserfahrung (bool): Whether professional experience is required.
        monate (list): List of selected months (format 'YYYY-MM').
        unternehmensgroesse (list): List of selected company sizes.
        branche (list): List of selected industry categories.

    Returns:
        list: List of dictionaries with 'label' and 'value' for each available company.
    """
    # Create a copy of the dataset to apply filters
    gefiltert = datenrahmen.copy()

    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        gefiltert = gefiltert[
            gefiltert['Beschäftigungsart'].isin(beschaeftigungsart_mapping.get(beschaeftigungsart, []))]
    if zeitmodell:
        gefiltert = gefiltert[gefiltert['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert = gefiltert[gefiltert['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if job_titel:
        gefiltert = gefiltert[gefiltert['Job_Titel'] == job_titel]

    # Extract available companies
    verfuegbare_unternehmen = gefiltert['Unternehmen'].unique()

    # Create options for dropdown
    optionen = [{'label': unternehmen, 'value': unternehmen}
                for unternehmen in sorted(verfuegbare_unternehmen) if pd.notna(unternehmen)]

    return optionen


# Callback for the job title filter on the left side (filters by company and global filters)
@app.callback(
    Output('filter-job-titel-links', 'options'),
    [Input('filter-unternehmen-links', 'value'),
     Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value')]
)
def update_job_titel_links(unternehmen, job_portal, bundesland, beschaeftigungsart, zeitmodell,
                           berufserfahrung, monate, unternehmensgroesse, branche):
    """
    Updates the list of available job titles in the dropdown menu on the left side of the
    "Vergleich der Stellenanzeigen" section of the dashboard.

    The update is based on both the global filter selections and the optionally selected company
    for the left comparison view.

    This ensures that the dropdown only displays job titles relevant to the specific combination
    of filters currently applied by the user.

    Parameters:
        unternehmen (str): Selected company.
        job_portal (list): List of selected job portals.
        bundesland (list): List of selected federal states.
        beschaeftigungsart (str): Selected type of employment.
        zeitmodell (str): Selected work time model.
        berufserfahrung (bool): Whether professional experience is required.
        monate (list): List of selected months (format 'YYYY-MM').
        unternehmensgroesse (list): List of selected company sizes.
        branche (list): List of selected industry categories.

    Returns:
        list: List of dictionaries with 'label' and 'value' for each available job title.
    """
    # Create a copy of the dataset to apply filters
    gefiltert = datenrahmen.copy()

    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        gefiltert = gefiltert[
            gefiltert['Beschäftigungsart'].isin(beschaeftigungsart_mapping.get(beschaeftigungsart, []))]
    if zeitmodell:
        gefiltert = gefiltert[gefiltert['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert = gefiltert[gefiltert['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if unternehmen:
        gefiltert = gefiltert[gefiltert['Unternehmen'] == unternehmen]

    # Extract available job titles
    verfuegbare_job_titel = gefiltert['Job_Titel'].unique()

    # Create options for dropdown
    optionen = [{'label': job_titel, 'value': job_titel}
                for job_titel in sorted(verfuegbare_job_titel) if pd.notna(job_titel)]

    return optionen


# Callback for the job title filter on the right side (filters by company and global filters)
@app.callback(
    Output('filter-job-titel-rechts', 'options'),
    [Input('filter-unternehmen-rechts', 'value'),
     Input('filter-job-portal', 'value'),
     Input('filter-bundesland', 'value'),
     Input('filter-beschaeftigungsart', 'value'),
     Input('filter-zeitmodell', 'value'),
     Input('filter-berufserfahrung', 'value'),
     Input('filter-monat', 'value'),
     Input('filter-unternehmensgroesse', 'value'),
     Input('filter-branche', 'value')]
)
def update_job_titel_rechts(unternehmen, job_portal, bundesland, beschaeftigungsart, zeitmodell,
                            berufserfahrung, monate, unternehmensgroesse, branche):
    """
    Updates the list of available job titles in the dropdown menu on the right side of the
    "Vergleich der Stellenanzeigen" section of the dashboard.

    The update is based on both the global filter selections and the optionally selected company
    for the right comparison view.

    Parameters:
        unternehmen (str): Selected company.
        job_portal (list): List of selected job portals.
        bundesland (list): List of selected federal states.
        beschaeftigungsart (str): Selected type of employment.
        zeitmodell (str): Selected work time model.
        berufserfahrung (bool): Whether professional experience is required.
        monate (list): List of selected months (format 'YYYY-MM').
        unternehmensgroesse (list): List of selected company sizes.
        branche (list): List of selected industry categories.

    Returns:
        list: List of dictionaries with 'label' and 'value' for each available job title.
    """
    # Create a copy of the dataset to apply filters
    gefiltert = datenrahmen.copy()

    if job_portal:
        gefiltert = gefiltert[gefiltert['Portal_Name'].isin(job_portal)]
    if bundesland:
        gefiltert = gefiltert[gefiltert['Bundesland'].isin(bundesland)]
    if beschaeftigungsart:
        gefiltert = gefiltert[
            gefiltert['Beschäftigungsart'].isin(beschaeftigungsart_mapping.get(beschaeftigungsart, []))]
    if zeitmodell:
        gefiltert = gefiltert[gefiltert['Zeitmodell'] == zeitmodell]
    if berufserfahrung is not None:
        gefiltert = gefiltert[gefiltert['Berufserfahrung_vorausgesetzt'] == berufserfahrung]
    if monate:
        gefiltert = gefiltert[gefiltert['Datum'].dt.strftime('%Y-%m').isin(monate)]
    if unternehmensgroesse:
        gefiltert = gefiltert[gefiltert['Unternehmensgröße'].isin(unternehmensgroesse)]
    if branche:
        gefiltert = gefiltert[gefiltert['Kategorie'].isin(branche)]
    if unternehmen:
        gefiltert = gefiltert[gefiltert['Unternehmen'] == unternehmen]

    # Extract available job titles
    verfuegbare_job_titel = gefiltert['Job_Titel'].unique()

    # Create dropdown options
    optionen = [{'label': job_titel, 'value': job_titel}
                for job_titel in sorted(verfuegbare_job_titel) if pd.notna(job_titel)]

    return optionen


# Admin-Section Callbacks
# Callback to add a new job title by pressing Enter
@app.callback(
    [Output('jobtitel-temp-speicher', 'data', allow_duplicate=True),
     Output('jobtitel-eingabe', 'value')],
    [Input('jobtitel-eingabe', 'n_submit')],
    [State('jobtitel-eingabe', 'value'),
     State('jobtitel-temp-speicher', 'data')],
    prevent_initial_call=True
)
def jobtitel_hinzufuegen(n_submit, neuer_jobtitel, aktuelle_liste):
    """
    Adds a new job title to the temporary list when the user presses Enter in the input field.

    Parameters:
        n_submit (int): Triggered when the Enter key is pressed in the input field.
        neuer_jobtitel (str): The new job title entered by the user.
        aktuelle_liste (list): The current temporary list of job titles.

    Returns:
        list: Updated list of job titles if the new entry is valid and not a duplicate.
        str: Clears the input field after a valid submission.
    """
    # Check if Enter was pressed, and the input is not empty
    if n_submit and neuer_jobtitel and neuer_jobtitel.strip():
        # Avoid adding duplicates
        if neuer_jobtitel not in aktuelle_liste:
            aktuelle_liste.append(neuer_jobtitel)
            return aktuelle_liste, "" # Clear input field after adding
    return no_update, no_update # Do nothing if input is invalid or duplicate


# Callback to update the list of job titles in the admin interface
@app.callback(
    Output('jobtitel-liste-container', 'children'),
    [Input('jobtitel-temp-speicher', 'data')]
)
def jobtitel_liste_aktualisieren(jobtitel_liste):
    """
    Updates the visual list of job titles based on the current temporary storage.

    This function generates a list of rows, each containing a job title and an associated delete button.
    The delete buttons use Dash pattern-matching IDs to support dynamic interaction.

    If the list is empty, a placeholder message is displayed instead.

    Parameters:
        jobtitel_liste (list): A list of job titles stored temporarily.

    Returns:
        list of html.Div: A list of rows containing job titles and corresponding delete buttons.
                          If the list is empty, a message is shown instead.
    """
    # If no job titles are present, display a placeholder message
    if not jobtitel_liste:
        return html.P("Keine Job-Titel vorhanden.")

    zeilen = []
    # Generate one row per job title with a delete button
    for index, jobtitel in enumerate(jobtitel_liste):
        zeile = dbc.Row(
            [
                dbc.Col(jobtitel, width=10), # Display job title text
                dbc.Col(
                    dbc.Button(
                        html.I(className="fas fa-trash"), # Trash icon
                        id={'type': 'jobtitel-loeschen', 'index': index}, # Pattern-matching ID
                        color="link",
                        className="p-0"
                    ),
                    width=2,
                    className="text-end" # Align delete button to the right
                )
            ],
            className="border-bottom py-2" # Row styling
        )
        zeilen.append(zeile)

    return zeilen


# Callback to delete individual job titles from the temporary list
@app.callback(
    Output('jobtitel-temp-speicher', 'data', allow_duplicate=True),
    [Input({'type': 'jobtitel-loeschen', 'index': ALL}, 'n_clicks')],
    [State('jobtitel-temp-speicher', 'data')],
    prevent_initial_call=True
)
def jobtitel_loeschen(clicks, jobtitel_liste):
    """
    Deletes a specific job title from the temporary job title list when its corresponding delete button is clicked.

    Parameters:
        clicks (list): List of click counts from dynamically generated delete buttons.
        jobtitel_liste (list): The current list of job titles stored temporarily.

    Returns:
        list: The updated job title list with the selected entry removed.
    """
    # If no delete buttons were clicked, do nothing
    if not any(clicks):
        return no_update

    # Get information about which button triggered the callback
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    # Extract the index of the button that was clicked
    button_id = ctx.triggered[0]['prop_id']
    index = json.loads(button_id.split('.')[0])['index']

    # Remove the job title at the given index
    neue_liste = jobtitel_liste.copy()
    neue_liste.pop(index)

    return neue_liste


# Callback to control the visibility of the confirmation modal for clearing the job title list
@app.callback(
    Output('bestätigen-liste-leeren-modal', 'is_open'),
    [Input('liste-leeren', 'n_clicks'),
     Input('bestätigen-liste-leeren-ja', 'n_clicks'),
     Input('bestätigen-liste-leeren-nein', 'n_clicks')],
    prevent_initial_call=True
)
def steuere_loeschen_modal(open_clicks, confirm_clicks, cancel_clicks):
    """
    Controls the visibility of the confirmation modal that appears when the user attempts to clear
    the job title list in the dashboard's admin section.

    This callback determines whether the modal should be shown or hidden, based on which button
    triggered the action. It listens to three buttons: the initial "Job Titel Liste leeren" button, the
    "Ja, alle entfernen" (Yes) button inside the modal, and the "Abbrechen" (No) button.

    - If the user clicks the "Job Titel Liste leeren" button, the modal is opened.
    - If the user clicks either "Yes" or "No" inside the modal, it is closed.

    Parameters:
        open_clicks (int): Clicks on the "clear list" button.
        confirm_clicks (int): Clicks on the confirmation ("Yes") button inside the modal.
        cancel_clicks (int): Clicks on the cancel ("No") button inside the modal.

    Returns:
        bool: True if the modal should be opened, False if it should be closed.
    """
    # Get the ID of the button that triggered the callback
    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Open modal if "clear list" button was clicked
    if button_id == 'liste-leeren':
        return True
    # Close modal if either "Yes" or "No" button was clicked
    else:
        return False


# Callback to delete all job titles when confirmed via the modal
@app.callback(
    Output('jobtitel-temp-speicher', 'data', allow_duplicate=True),
    [Input('bestätigen-liste-leeren-ja', 'n_clicks')],
    prevent_initial_call=True
)
def alle_jobtitel_loeschen(n_clicks):
    """
    Clears all job titles from the temporary storage when the user confirms the action in the modal.

    Parameters:
        n_clicks (int): Number of clicks on the confirmation ("Yes") button.

    Returns:
        list or no_update: An empty list to clear the job title storage or no_update if no action is needed.
    """
    # If the "Yes" button was clicked, clear the list
    if n_clicks:
        return []
    return no_update


# Callback to upload the job title list to MongoDB when button is clicked
@app.callback(
    Output('erfolg-modal', 'is_open'),
    [Input('liste-hochladen', 'n_clicks')],
    [State('jobtitel-temp-speicher', 'data')],
    prevent_initial_call=True
)
def jobtitel_hochladen(n_clicks, jobtitel_liste):
    """
    Uploads the current job title list to MongoDB when the upload button is clicked,
    and opens a confirmation modal upon success.

    This callback is triggered by the user clicking the "Liste der Job Titel hochladen" button. It performs two actions:

    1. Saves the current job title list locally using a predefined helper function.
    2. Attempts to upload the list to MongoDB via a dedicated database interface function.

    Parameters:
        n_clicks (int): Number of clicks on the upload button.
        jobtitel_liste (list): The current list of job titles stored temporarily.

    Returns:
        bool: True to open the success modal, False otherwise.
    """
    # Trigger upload only if button was clicked
    if n_clicks:
        # Save job titles locally
        save_job_titles(jobtitel_liste)

        # Try uploading to MongoDB
        try:
            from MongoDB import upload_job_titles_to_mongodb
            if upload_job_titles_to_mongodb():
                print("Erfolgreich in MongoDB hochgeladen!")
            else:
                print("MongoDB-Upload fehlgeschlagen!")
        except Exception as e:
            print(f"Kritischer MongoDB-Fehler: {e}")

        # Open the success modal
        return True

    # Do not open modal if no click
    return False


# Callback to close the success modal when the close button is clicked
@app.callback(
    Output('erfolg-modal', 'is_open', allow_duplicate=True),
    [Input('erfolg-modal-schliessen', 'n_clicks')],
    prevent_initial_call=True
)
def schliesse_erfolgsmodal(n_clicks):
    """
    Closes the success modal when the user clicks the close button.

    The modal can be closed either via the "X" icon in the upper corner or via the "Schließen" button within the modal.

    If no interaction occurs, the modal remains unchanged.

    Parameters:
        n_clicks (int): Number of clicks on the modal close button.

    Returns:
        bool or no_update: Returns False to close the modal, or no_update if no clicks.
    """
    # Close modal only if button was clicked
    if n_clicks:
        return False

    # Otherwise, do not update modal state
    return no_update


# Callback to hide the left filter column when the Admin area is active
@app.callback(
    [Output('hauptinhalt', 'style'),
     Output('filter-spalte', 'style')],
    [Input('nav-allgemein', 'n_clicks'),
     Input('nav-vergleich', 'n_clicks'),
     Input('nav-admin', 'n_clicks'),
     Input('hauptinhalt', 'children')],
    prevent_initial_call=True
)
def steuere_layout_und_filter(nav_allgemein, nav_vergleich, nav_admin, aktueller_inhalt):
    """
    Controls the layout of the dashboard and the visibility of the left-side global filter section
    based on the selected navigation bar section.

    When the user navigates to the Admin section, the global filter column is hidden, and the
    main content area expands to full width.

    The function considers both the most recently clicked navigation button and the currently
    rendered content to determine the active section.

    Parameters:
        nav_allgemein (int): Clicks on the 'Allgemein' navigation button.
        nav_vergleich (int): Clicks on the 'Vergleich' navigation button.
        nav_admin (int): Clicks on the 'Admin' navigation button.
        aktueller_inhalt (component): The current content component displayed.

    Returns:
        tuple: Styles for main content and filter column:
            - Main content style (dict): Adjusted for full width in admin or normal width otherwise.
            - Filter column style (dict): Hidden in admin view, shown otherwise.
    """
    ctx = dash.callback_context

    # Determine which navigation button was clicked
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Check if the admin area is currently active by inspecting the main content's id
    is_admin = False
    if (hasattr(aktueller_inhalt, 'props') and
            'id' in aktueller_inhalt.props and
            aktueller_inhalt.props['id'] == 'admin-inhalt'):
        is_admin = True

    # If admin nav clicked or admin content active, show main content full width and hide filter column
    if button_id == 'nav-admin' or is_admin:
        return (
            {'flex': '1', 'padding': '20px', 'width': '100%'},  # Main content - full width
            {'display': 'none'}  # Hide global filter column
        )
    # For other navs, show normal layout with filter column visible
    else:
        return (
            {'flex': '1', 'padding': '20px', 'minWidth': '0'},  # Main content - normal width
            {'width': '20%', 'padding': '20px', 'display': 'block'}  # Show filter column
        )
