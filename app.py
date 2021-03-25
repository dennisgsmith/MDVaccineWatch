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
    df = pd.read_csv(
        DATA_URL,
        dtype={"County": str}
    )
    print("SUCCESS: DATA URL Working")
except HTTPError as e:
    print("ERROR: There was a problem accessing the maryland.gov data.")
    print(e)  # TODO: Implement logging
    
    print("Reading from backup...")
    # Read csv from local backup
    df = pd.read_csv(
        LOCAL_DATA_PATH.resolve(),
        dtype={"County": str}
    )
    print("SUCCESS: Read local copy from backup")
else:
    # Replace the file locally as backup
    df.to_csv(
        "./data/MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose.csv", 
        index=False
    )
    print("SUCCESS: UPDATED Pandas DataFram")

# Strip trailing whitespace from end of County names
df ["County"] = df["County"].str.rstrip()

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
print(total_pop_by_county)

# -----------------------------------------------------------------------------

# Import CSS-referenced font
external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?" "family=Lora&display=swap",
        "rel": "stylesheet",
    },
]
# Compose app and generate HTML
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "#MDVaccineWatch"

app.layout = html.Div(
    children=[
        html.Div(
            children=[
                html.H1(
                    children=[
                        html.Span("#MD", id="header-title1"),
                        html.Span("Vaccine", id="header-title2"),
                        html.Span("Watch", id="header-title3"),
                    ],
                    className="header-title",
                ),
                html.P(
                    children="Vaccine Data by County",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        html.Div(
            children=[
                html.P(
                    "Select one of the options below to filter for cumulative or daily data."
                ),
                dcc.RadioItems(
                    id="select_dose",
                    options=[
                        # TODO: {"label": "Total Fully Vaccinated", "value": "TOTAL"},
                        {"label": "First Dose Daily", "value": "FirstDoseDaily"},
                        {"label": "First Dose Cumulative", "value": "FirstDoseCumulative"},
                        {"label": "Second Dose Daily", "value": "SecondDoseDaily"},
                        {"label": "Second Dose Cumulative", "value": "SecondDoseCumulative"},
                        {"label": "Single Dose Daily", "value": "SingleDoseDaily"},
                        {"label": "Single Dose Cumulative", "value": "SingleDoseCumulative"},
                    ],
                    value="SecondDoseCumulative",
                    labelStyle={"display": "inline-block"},
                ),
                dcc.Slider(
                    id="select_date",
                    min=numdate[0],
                    max=numdate[-1],
                    value=numdate[-1],
                    tooltip={
                        "always_visible": True,
                        "placement": "top",
                    },
                    marks={
                        "label": "VACCINATION_DATE",
                        numdate[0]: min(df["VACCINATION_DATE"]).strftime("%m/%d/%Y"),
                        numdate[-1]: max(df["VACCINATION_DATE"]).strftime("%m/%d/%Y"),
                    },
                ),
                html.P("Use the slider above to adjust the selected date."),

                # Display date selected
                html.P(id="output_container"),

                # Ouput county stats triggered from choropleth clickData
                html.P(id="stats_container"),

                # Create Choropleth Mapbox
                dcc.Graph(id="choropleth", className="coropleth-container")
            ]
        )
    ],
    className="wrapper"
)

# -----------------------------------------------------------------------------
# Connect Plotly graphs with Dash components
# Callback functions


@app.callback(
    [Output("output_container", "children"), Output("choropleth", "figure")],
    [Input("select_date", "value"), Input("select_dose", "value")],
)
def display_choropleth(selected_date, selected_dose):  # Callback function
    '''Diplay updated mapbox choropleth graph and date text when parameters are changed'''

    print(selected_date)
    print(type(selected_date))

    slider_date = get_slider_date(df, selected_date)
    container = f"The date selected is: {slider_date.strftime('%B %-d, %Y')}"

    dff1 = filter_by_date(df, slider_date)

    # Create Plotly mapbox figure
    fig = px.choropleth_mapbox(
        dff1,
        geojson=counties,
        locations="County",
        color=selected_dose,
        featureidkey="properties.name",
        color_continuous_scale="Viridis",
        range_color=(0, max(df[selected_dose])),
        mapbox_style="white-bg",
        zoom=6.55,
        center={"lat": 38.5500, "lon": -77.3213},
        opacity=0.7,
        labels={selected_dose: "Vaccinated"},
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    fig.update_layout(
        coloraxis={
            "colorbar_x": 0.05,
            "colorbar_y": 0.5,
            "colorbar_len": 0.51,
            "colorbar_thickness": 20
        }
    )
    return container, fig


@app.callback(
    Output("stats_container", "children"),
    [Input("select_date", "value"), Input("choropleth", "clickData")]
)
def display_stats(selected_date, clickData):
    '''Display additional data on county that is selected via click on the map'''

    print(clickData)
    print(type(clickData))

    slider_date = get_slider_date(df, selected_date)
    dff2 = filter_by_date(df, slider_date)

    if not clickData:
        return [""]

    # Get selected county
    county_name = clickData.get("points")[0].get("location")

    # Filter by county
    dff2 = dff2.loc[dff2.County == county_name, ["FirstDoseCumulative", "SecondDoseCumulative", "SingleDoseCumulative"]]

    # Get rid of index for computation
    dff2.reset_index(drop=True, inplace=True)

    # Filter for selected location
    county_total_pop = total_pop_by_county.loc[total_pop_by_county.County == county_name, "Population"]

    if county_total_pop.empty:
        return [""]

    county_total_pop = int(county_total_pop)

    # Get percent of total population vaccinated for each column
    pc_dff2 = dff2 / county_total_pop

    stats_container = pc_dff2.values.flatten()

    stats = "First Dose Perc: %{:.2f}, Second Dose Perc: %{:.2f}, Single Dose Perc: %{:.2f}".format(
        stats_container[0], stats_container[1], stats_container[2]
    )

    return stats

# -----------------------------------------------------------------------------
# Helper Functions


def get_slider_date(df, selected_date):
    '''Return timestamp based on numerical index provided by slider'''
    return df["VACCINATION_DATE"].unique()[selected_date]


def filter_by_date(df, slider_date):
    '''Make a shallow copy of the Pandas dataframe.
    Filter the dataframe based on the date entered
    Return filtered dataframe'''
    dff = df.copy(deep=True)
    return dff[dff["VACCINATION_DATE"] == slider_date]


if __name__ == "__main__":
    app.run_server(debug=True)
