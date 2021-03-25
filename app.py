from urllib.error import HTTPError
from urllib.request import urlopen
import json
from pathlib import Path

import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

# -----------------------------------------------------------------------------

MAPBOX_TOKEN = open(".mapbox_token").read()

HERE = Path(__file__).parent
DATA_FOLDER = HERE / "data"

# Get Maryland counties layer as geojson
# source: frankrowe GH (see README)
GEOJSON_PATH = DATA_FOLDER / "maryland-counties.geojson"

# Total population by county
TOTAL_POP_PATH = DATA_FOLDER / "Population_Estimates_by_County.csv"

# COVID-19 Data
LOCAL_DATA_PATH = list(DATA_FOLDER.glob("MD_COVID19_*"))[0]

# Get updated COVID-19 data from maryland.gov
DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"


with open(GEOJSON_PATH.resolve()) as f:
    counties = json.load(f)

# Attempt to get updated csv from URL, default to most recent local copy if request fails
try:
    # Pandas reads URL input
    df = pd.read_csv(DATA_URL, dtype={"County": str})
    print("SUCCESS: DATA URL Working")

except HTTPError as e:
    print("ERROR: There was a problem accessing the maryland.gov data.")
    print(e)  # TODO: Implement logging
    print("Reading from backup...")
    # Read csv from local backup
    df = pd.read_csv(LOCAL_DATA_PATH.resolve(), dtype={"County": str})
    print("SUCCESS: Read local copy from backup")

else:
    # Replace the file locally as backup
    df.to_csv(
        "./data/MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose.csv",
        index=False,
    )
    print("SUCCESS: Updated local backup")

# Strip trailing whitespace from end of County names
df["County"] = df["County"].str.rstrip()

# Convert to datetime
df["VACCINATION_DATE"] = pd.to_datetime(df["VACCINATION_DATE"], format="%Y-%m-%d")

df = df[~(df["VACCINATION_DATE"] <= "2020-12-01")]  # Get rid of data before this date

df.fillna(0, inplace=True)  # Fill missing entries with 0

# Sort by date ad create numeric representation for each unique date for numeric Slider input
df.sort_values(by="VACCINATION_DATE", inplace=True)
numdate = [x for x in range(len(df["VACCINATION_DATE"].unique()))]

# Build dataframe of all county population to get percentages
# Link: https://www.census.gov/search-results.html?q=maryland+population+by+county&page=1&stateGeo=none&searchtype=web&cssp=SERP&_charset_=UTF-8
total_pop_by_county = pd.read_csv(TOTAL_POP_PATH.resolve())

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
                # Display date selected
                dcc.Markdown(id="output_container"),
                # Ouput county stats triggered from choropleth clickData
                dcc.Markdown(id="stats-container1"),
                dcc.Markdown(id="stats-container2"),
                # Create Choropleth Mapbox
                html.Div(
                    [
                        html.Div(  # Dopdown menu
                            [
                                html.P(
                                    "Filter for cumulative or daily data.",
                                    style={"color": "#ffffff"},
                                ),
                                dcc.Dropdown(
                                    id="select_dose",
                                    options=[
                                        {
                                            "label": "First Dose Daily",
                                            "value": "FirstDoseDaily",
                                        },
                                        {
                                            "label": "First Dose Cumulative",
                                            "value": "FirstDoseCumulative",
                                        },
                                        {
                                            "label": "Second Dose Daily",
                                            "value": "SecondDoseDaily",
                                        },
                                        {
                                            "label": "Second Dose Cumulative",
                                            "value": "SecondDoseCumulative",
                                        },
                                        {
                                            "label": "Single Dose Daily",
                                            "value": "SingleDoseDaily",
                                        },
                                        {
                                            "label": "Single Dose Cumulative",
                                            "value": "SingleDoseCumulative",
                                        },
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="SecondDoseCumulative",
                                    optionHeight=25,
                                ),
                            ],
                            className="dropdown-container",
                        ),
                        html.Div(  # Radio buttons
                            [
                                html.P(
                                    "Choose between absolute (population) and relative (percent of population)"
                                ),
                                dcc.RadioItems(
                                    id="select-absolute-relative",
                                    options=[
                                        {
                                            "label": "Absolute\t",
                                            "value": "Absolute"
                                        },
                                        {
                                            "label": "Relative",
                                            "value": "Relative"
                                        }
                                    ],
                                    value="Absolute",
                                    persistence=True
                                )
                            ],
                            className="radio-button-container",
                        ),
                        html.Div(  # Date Slider
                            [
                                html.P(
                                    "Use the Timeline Slider to adjust the selected date."
                                ),
                                dcc.Slider(
                                    id="select_date",
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
                ),
                dcc.Graph(id="choropleth", className="coropleth-container"),
            ],
            className="wrapper",
        ),
    ],
)

# -----------------------------------------------------------------------------
# Connect Plotly graphs with Dash components
# Callback functions


@app.callback(
    [Output("output_container", "children"), Output("choropleth", "figure")],
    [Input("select_date", "value"), Input("select_dose", "value")],
)
def display_choropleth(selected_date, selected_dose):  # Callback function
    """Diplay updated mapbox choropleth graph and date text when parameters are changed"""

    print(selected_date)
    print(type(selected_date))

    slider_date = get_slider_date(df, selected_date)
    container = f"**The date selected is: {slider_date.strftime('%B %-d, %Y')}**"

    dff1 = filter_by_date(df, slider_date)

    # Create Plotly mapbox figure
    fig = px.choropleth_mapbox(
        dff1,
        geojson=counties,
        locations="County",
        featureidkey="properties.name",
        zoom=6.8,
        center={"lat": 38.8500, "lon": -77.3213},
        # Configure Colorbar
        color=selected_dose,
        color_continuous_scale="Viridis",
        range_color=(0, max(df[selected_dose])),
        opacity=0.7,
    )
    # mapbox theme & layout
    fig.update_layout(mapbox_style="dark", mapbox_accesstoken=MAPBOX_TOKEN)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Update Colorbar style
    fig.update_layout(
        coloraxis={
            "colorbar_x": 0.05,
            "colorbar_y": 0.5,
            "colorbar_len": 0.51,
            "colorbar_thickness": 20,
            "colorbar_tickfont_color": "#ffffff",
        }
    )
    # Update Colorbar labels
    fig.update_coloraxes(
        colorbar_title_text="Vaccinated", colorbar_title_font_color="#ffffff"
    )
    return container, fig


@app.callback(
    [Output("stats-container1", "children"), Output("stats-container2", "children")],
    [Input("select_date", "value"), Input("choropleth", "clickData")],
)
def display_stats(selected_date, clickData):
    """Display additional data on county that is selected via click on the map"""

    print(clickData)
    print(type(clickData))

    slider_date = get_slider_date(df, selected_date)
    dff2 = filter_by_date(df, slider_date)

    if not clickData:
        return "Select a county on the map for additional information.", ""

    # Get selected county
    county_name = clickData.get("points")[0].get("location")

    # Filter by county
    dff2 = dff2.loc[
        dff2.County == county_name,
        ["FirstDoseCumulative", "SecondDoseCumulative", "SingleDoseCumulative"],
    ]

    stats_dict = get_county_avg(dff2, county_name)

    stats1 = "**First Dose Perc: {:.2f}%  |  Second Dose Perc: {:.2f}%  |  Single Dose Perc: {:.2f}%**".format(
        stats_dict["FirstDoseCumulative"],
        stats_dict["SecondDoseCumulative"],
        stats_dict["SingleDoseCumulative"]
    )
    stats2 = "**{} County partially vaccinated: {:.2f}%  |  {} County fully vaccinated: {:.2f}%**".format(
        county_name,
        (stats_dict["FirstDoseCumulative"] + stats_dict["SingleDoseCumulative"]),
        county_name,
        (stats_dict["SecondDoseCumulative"] + stats_dict["SingleDoseCumulative"])
    )
    return stats1, stats2


# @app.callback(
#     Output("", ""),
#     Input("select-absolute-relative", "value")
# )
# def absolute_relative_switch(selected_button):
#     '''Switch between viewing absolute (population) and relative (percent of population)
#     on the choropleth map'''
#     pass

# -----------------------------------------------------------------------------
# Helper Functions


def get_slider_date(df, selected_date):
    """Return timestamp based on numerical index provided by slider"""
    return df["VACCINATION_DATE"].unique()[selected_date]


def filter_by_date(df, slider_date):
    """Make a shallow copy of the Pandas dataframe.
    Filter the dataframe based on the date entered
    Return filtered dataframe"""
    dff = df.copy(deep=True)
    return dff[dff["VACCINATION_DATE"] == slider_date]


def get_county_avg(dff, county_name):
    # Get rid of index for computation
    dff.reset_index(drop=True, inplace=True)

    # Filter for selected location
    county_total_pop = total_pop_by_county.loc[
        total_pop_by_county.County == county_name, "Population"
    ]

    if county_total_pop.empty:
        return "Data for this county is unavailable at the selected date."

    county_total_pop = int(county_total_pop)

    # Get percent of total population vaccinated for each column
    perc = (dff / county_total_pop) * 100

    # Move averages into dict
    try:
        return perc.to_dict("records")[0]

    except IndexError:
        print("ERROR: Missing data for date, returning 0")
        # TODO: Log output
        return {
            'FirstDoseCumulative': 0,
            'SecondDoseCumulative': 0,
            'SingleDoseCumulative': 0
        }


if __name__ == "__main__":
    app.run_server(debug=True)
