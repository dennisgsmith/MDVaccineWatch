import os
import io
import json
from pathlib import Path

import pandas as pd
import dash
from dash_table import DataTable, FormatTemplate
from dash_table.Format import Format
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

import boto3

# -----------------------------------------------------------------------------

FILES_DIR = Path(__file__).parent / "files"
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
MB_TOKEN = os.getenv("MB_TOKEN")

# Load data from S3 bucket
s3_resource = boto3.resource('s3')

# S3: Optional mapbox token for styling


if MB_TOKEN:
    MB_STYLE = "dark"
else:
    print("Using mapbox theme that does not require token")
    MB_TOKEN = None
    MB_STYLE = "carto-darkmatter"

# Get Maryland counties layer as geojson
# source: frankrowe GH (see README)
GEOJSON_PATH = FILES_DIR / "maryland-counties.geojson"

# Load GeoJSON from local data file
with open(GEOJSON_PATH.resolve()) as f:
    geojson_counties = json.load(f)

# Total population by county
POP_EST_PATH = FILES_DIR / "Population_Estimates_by_County.csv"

# Build dataframe of all county population to get percentages
# Source: https://www.census.gov/
pop_est_by_county = pd.read_csv(POP_EST_PATH.resolve(), dtype={"Population": int})

# Get vaccine data written to S3 by scheduler job
vaccine_data_obj = s3_resource.meta.client.get_object(
    Bucket=AWS_S3_BUCKET,
    Key='scheduled_data/MD_Vax_Data.csv'
)
df = pd.read_csv(io.BytesIO(vaccine_data_obj['Body'].read()))  # Read csv from S3

#----------------------------------CLEAN UP DATA--------------------------------

# Convert to datetime
df["VACCINATION_DATE"] = pd.to_datetime(df["VACCINATION_DATE"], format="%Y-%m-%d")

# Sort by date ad create numeric representation for each unique date for numeric Slider input
df.sort_values(by="VACCINATION_DATE", inplace=True)

numdate = [x for x in range(len(df["VACCINATION_DATE"].unique()))]

# Define the columns to subset globally to make it easier to reference them
col_list = [
    "County",
    "First Dose",
    "Second Dose",
    "Single Dose",
    "At Least One Vaccine",
    "Fully Vaccinated",
]

# -----------------------------------------------------------------------------

# Import CSS-referenced font
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?family=Open+Sans:wght@300&display=swap",
        "rel": "stylesheet",
    },
]
# Compose app and generate HTML
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
PORT = int(os.environ.get("PORT", 8050))
app.title = "#MDVaccineWatch"

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1(
                    [
                        html.Span("#MD", id="header-title1"),
                        html.Span("Vaccine", id="header-title2"),
                        html.Span("Watch", id="header-title3"),
                    ],
                    className="header-title",
                ),
                html.P(
                    ["Vaccine Data by County"],
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            [
                html.Div(
                    "For more information on the current phase of Maryland's vaccination plan,"
                ),
                html.A(
                    "visit covidLINK.maryland.gov",
                    href="https://covidlink.maryland.gov/content/vaccine/",
                    target="_blank",
                    className="covidLINK",
                ),
                # State stats
                dcc.Markdown(id="state-stats"),
                # Display date selected
                dcc.Markdown(id="output-date-location"),
                html.Div(
                    DataTable(
                        id="output-table",
                        columns=[],
                        data=[],
                        column_selectable=False,
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "backgroundColor": "black",
                            "color": "#ffffff",
                            "textAlign": "center",
                            "fontFamily": "'Open sans', sans-serif",
                            "whiteSpace": "normal",
                            "height": "auto",
                        },
                        style_header={"color": "#f1ba20", "font-weight": "bold"},
                        style_data_conditional=[
                            {  # override hot pink selected color
                                "if": {"state": "active"},
                                "backgroundColor": "black",
                                "border": "3px solid white",
                                "color": "white",
                            }
                        ],
                    ),
                    className="table-container",
                ),
                html.Div(
                    [
                        html.Div(  # Dopdown menu
                            [
                                html.P(
                                    "Filter map for type of dose:",
                                    style={"color": "#ffffff"},
                                ),
                                dcc.Dropdown(
                                    id="selected-dose",
                                    options=[
                                        {
                                            "label": "Total at least one vaccine",
                                            "value": "At Least One Vaccine",
                                        },
                                        {
                                            "label": "Total fully vaccinated",
                                            "value": "Fully Vaccinated",
                                        },
                                        {
                                            "label": "Partially vaccinated (First Dose Only)",
                                            "value": "First Dose",
                                        },
                                        {
                                            "label": "Fully vaccinated (Second Dose Only)",
                                            "value": "Second Dose",
                                        },
                                        {
                                            "label": "Fully vaccinated (Single Dose Only)",
                                            "value": "Single Dose",
                                        },
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="At Least One Vaccine",
                                    optionHeight=25,
                                ),
                            ],
                            className="dropdown-container",
                        ),
                        html.Div(  # Radio buttons
                            [
                                html.P(
                                    "Choose between absolute (population) and relative (percent of population):"
                                ),
                                dcc.RadioItems(
                                    id="select-absolute-relative",
                                    options=[
                                        {"label": "Absolute\t", "value": "Absolute"},
                                        {"label": "Relative", "value": "Relative"},
                                    ],
                                    value="Absolute",
                                    persistence=True,
                                ),
                            ],
                            className="radio-button-container",
                        ),
                        html.Div(  # Date Slider
                            [
                                html.P("Adjust the timeline slider:"),
                                dcc.Slider(
                                    id="selected-date-index",
                                    min=numdate[0],
                                    max=numdate[-1],
                                    value=numdate[-1],
                                    marks={
                                        "label": "VACCINATION_DATE",
                                        numdate[0]: min(
                                            df["VACCINATION_DATE"]
                                        ).strftime("%m/%d/%Y"),
                                        numdate[-1]: max(
                                            df["VACCINATION_DATE"]
                                        ).strftime("%m/%d/%Y"),
                                    },
                                ),
                            ],
                            className="slider-container",
                        ),
                    ],
                    className="flex-container",
                ),  # Create Choropleth Mapbox
                dcc.Graph(
                    id="choropleth",
                    config={"scrollZoom": False},
                    className="coropleth-container"
                ),
                html.Div(
                    [
                        html.A("Sources:"),
                        html.A(
                            "GoeJSON",
                            href="https://github.com/frankrowe/maryland-geojson/",
                            target="_blank",
                        ),
                        html.A(
                            "Maryland Vaccine Data",
                            href="https://data.imap.maryland.gov/",
                            target="_blank",
                        ),
                        html.A(
                            "Maryland Census Data",
                            href="https://www.census.gov/",
                            target="_blank",
                        ),
                    ],
                    className="sources",
                ),
            ],
            className="wrapper",
        ),
    ],
)

# -----------------------------------------------------------------------------
# Connect Plotly graphs with Dash components
# Callback functions


@app.callback(
    Output("choropleth", "figure"),
    [
        Input("selected-date-index", "value"),
        Input("selected-dose", "value"),
        Input("select-absolute-relative", "value"),
    ],
)
def display_choropleth(
    selected_date, selected_dose, selected_button
):  # Callback function
    """Diplay updated mapbox choropleth graph and date text when parameters are changed"""

    print(selected_date, type(selected_date))
    print(selected_dose, type(selected_dose))
    print(selected_button, type(selected_button))

    slider_date = get_slider_date(df, selected_date)

    dff1 = filter_by_date(df, slider_date)

    p = False
    tick_format = ","
    if selected_button == "Relative":
        # Covert to percent
        p = True
        tick_format = "%"

    dff1 = get_county_stats(dff1, percent=p)

    # Get max of aggregates returned by get_county_stats
    mx = max(dff1[selected_dose])

    # Create Plotly mapbox figure
    fig = px.choropleth_mapbox(
        dff1,
        geojson=geojson_counties,
        locations="County",
        featureidkey="properties.name",
        zoom=6.8,
        center={"lat": 38.8500, "lon": -77.3213},
        # Configure Colorbar
        color=selected_dose,
        color_continuous_scale="Viridis",
        range_color=(0, mx),
        opacity=0.7,
    )
    # mapbox theme & layout
    fig.update_layout(mapbox_style=MB_STYLE, mapbox_accesstoken=MB_TOKEN)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Update Colorbar style
    fig.update_layout(
        coloraxis={
            "colorbar_x": 0.05,
            "colorbar_y": 0.5,
            "colorbar_len": 0.9,
            "colorbar_thickness": 20,
            "colorbar_tickfont_color": "#ffffff",
            "colorbar_tickformat": tick_format,
        }
    )
    # Update Colorbar labels
    fig.update_coloraxes(
        colorbar_title_text="Vaccinated", colorbar_title_font_color="#ffffff"
    )
    return fig


@app.callback(
    [
        Output("state-stats", "children"),
        Output("output-date-location", "children"),
        Output("output-table", "columns"),
        Output("output-table", "data"),
    ],
    [
        Input("selected-date-index", "value"),
        Input("choropleth", "clickData"),
        Input("select-absolute-relative", "value"),
    ],
)
def display_stats(selected_date_index, clickData, selected_button):
    """Display additional data on county that is selected via click on the map"""

    print(clickData)
    print(type(clickData))

    slider_date = get_slider_date(df, selected_date_index)
    dff2 = filter_by_date(df, slider_date)

    output_date_location = f"Date selected: **{slider_date.strftime('%B %-d, %Y')}**"

    p = False
    if selected_button == "Relative":
        p = True

    # Get total state sums before filtering by County
    atleast1_sum_s, fully_sum_s = get_state_stats(dff2, percent=p)

    pop_est_state = int(pop_est_by_county.Population.sum())

    state_stats = "  |  ".join(
        [
            f"State At Least One Vaccine: **{atleast1_sum_s:{'.2%' if p else ','}}**",
            f"State Fully Vaccinated: **{fully_sum_s:{'.2%' if p else ','}}**",
            f"State Estimated Population: **{pop_est_state:{','}}**",
        ]
    )

    if not clickData:
        placeholder = "Select a county on the map for more details"
        return (
            state_stats,
            output_date_location,
            [{"id": "placeholder", "name": placeholder}],
            [
                {
                    "placeholder": "⬇️ Customize and filter the information with the tools below ⬇️"
                }
            ],
        )

    # Get selected county
    # Make sure to return 4 items in the callback!!!!
    county_name = clickData.get("points")[0].get("location")

    output_date_location += f"  |  County Selected: **{county_name}**"
    pop_est = int(
        pop_est_by_county.loc[
            pop_est_by_county["County"] == county_name, "Population"
        ].values
    )
    output_date_location += f"  |  County Estimated Population: **{pop_est:{','}}**"

    dff2 = get_county_stats(dff2, percent=p)

    # Filter by county
    stats_df = filter_by_county(dff2, county_name)
    stats_df.fillna(0)
    stats_df.drop(columns="County", inplace=True)

    table_cols = [
        {"id": col, "name": col, "type": "numeric", "format": format_table(p)}
        for col in stats_df.columns
    ]
    table_data = stats_df.to_dict("records")

    return state_stats, output_date_location, table_cols, table_data


# -----------------------------------------------------------------------------
# Helper Functions


def get_slider_date(df, selected_date_index):
    """Return timestamp based on numerical index provided by slider"""
    return df["VACCINATION_DATE"].unique()[selected_date_index]


def filter_by_date(df, slider_date):
    """
    Filter the dataframe based on the date entered
    Return filtered dataframe
    """
    dff = df.copy(deep=True)
    return dff[dff["VACCINATION_DATE"] == slider_date]


def filter_by_county(df, county_name):
    """Use Pandas boolean indexing to return a county-filtered dataframe"""
    return df.loc[df["County"] == county_name, col_list]


def get_county_stats(dff, percent=False):
    """
    Input date filtered dataframe, percent Bool (optional)
    Return a DataFrame with 3 cols:
    "First Dose", "Second Dose", & "Single Dose"
    Values (percent=False(default)):absolute people vacciated in county_name OR
    Values (percent=True): relative people vaccinated in county_name
    """
    # Get rid of index
    dff.reset_index(drop=True, inplace=True)

    if percent == True:
        # Copy estimated pop by county
        county_pops = pop_est_by_county.copy(deep=True)

        # Filter for selected location
        merged_df = pd.merge(county_pops, dff, how="left", on="County")

        # Create list of columns to calculate percentage on
        county_stats_col_list = [col for col in col_list if col != "County"]

        # Get percent of total population vaccinated for numeric columns
        merged_df[county_stats_col_list] = merged_df[county_stats_col_list].div(
            merged_df.Population, axis=0
        )

        # Return the percent of the population vaccinated for
        return merged_df

    # Otherwise, just use absolute numbers
    return dff


def get_state_stats(dff, percent=False):
    """Compute date-filtered dataframe totals"""
    # dataframe filterd to single day
    dff.copy()  # Shallow copy

    atleast1_sum_state = dff["First Dose"].sum()
    fully_sum_state = dff["Second Dose"].sum() + dff["Single Dose"].sum()

    if percent == True:
        state_pop = pop_est_by_county["Population"].sum()
        atleast1_sum_state /= state_pop
        fully_sum_state /= state_pop

    return atleast1_sum_state, fully_sum_state


def format_table(percent=False):
    """Return dash_table formatting string based on boolean arg"""
    if not percent:
        return Format().group(True)
    else:
        return FormatTemplate.percentage(2)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=PORT)
