from urllib.request import urlopen
import json

import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px

# -----------------------------------------------------------------------------

# Get Maryland counties layer as geojson
# GH credit: frankrowe
# source: https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson
URL = "https://raw.githubusercontent.com/frankrowe/maryland-geojson/master/maryland-counties.geojson"

# features -> properties -> name -> county name
with urlopen(URL) as response:
    counties = json.load(response)

# Pandas reads URL input
df = pd.read_csv(
    "https://opendata.arcgis.com/datasets/da3ecc5aef8e4b328abd01c001f54010_0.csv",
    dtype={"County": str},
)
# Convert to datetime
df["VACCINATION_DATE"] = pd.to_datetime(df["VACCINATION_DATE"], format="%Y-%m-%d")

df = df[~(df["VACCINATION_DATE"] <= "2020-12-01")]  # Get rid of data before this date

df.fillna(0, inplace=True)  # Fill missing entries with 0

# Create numeric representation for each unique date for numeric Slider input
numdate = [x for x in range(len(df["VACCINATION_DATE"].unique()))]

# Build dataframe of all county population to get percentages
# Source: U.S. Census Bureau, Vintage 2019 Population Estimates
# Link: https://www.census.gov/search-results.html?q=maryland+population+by+county&page=1&stateGeo=none&searchtype=web&cssp=SERP&_charset_=UTF-8
total_pop_by_county = pd.read_csv("data/Population_Estimates_by_County.csv")

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
        html.P(
            "Select one of the options below to filter for cumulative or daily data."
        ),
        dcc.RadioItems(
            id="select_dose",
            options=[
                {"label": "Cumulative First Dose   ", "value": "CumulativeFirstDose"},
                {"label": "Cumulative Second Dose   ", "value": "CumulativeSecondDose"},
                {"label": "Daily First Dose   ", "value": "DailyFirstDose"},
                {"label": "Daily Second Dose   ", "value": "DailySecondDose"},
            ],
            value="CumulativeFirstDose",
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
                numdate[0]: "2020-12-01",
                numdate[-1]: max(df["VACCINATION_DATE"]).strftime("%Y-%m-%d"),
            },
        ),
        html.P("Use the slider above to adjust the selected date."),
        # Display date selected
        html.Div(id="output_container"),
        # Create Choropleth Mapbox
        dcc.Graph(id="choropleth"),
    ]
)

# -----------------------------------------------------------------------------

# Connect Plotly graphs with Dash components
@app.callback(
    [Output("output_container", "children"), Output("choropleth", "figure")],
    [Input("select_date", "value"), Input("select_dose", "value")],
)
def display_choropleth(selected_date, selected_dose):  # Callback function
    print(selected_date)
    print(type(selected_date))

    slider_date = df["VACCINATION_DATE"].unique()[selected_date]
    container = f"The date selected is: {slider_date.strftime('%Y-%m-%d')}"

    dff = df.copy()
    dff = dff[dff["VACCINATION_DATE"] == slider_date]

    # Create Plotly mapbox figure
    fig = px.choropleth_mapbox(
        dff,
        geojson=counties,
        locations="County",
        color=selected_dose,
        featureidkey="properties.name",
        color_continuous_scale="Viridis",
        range_color=(0, max(df[selected_dose])),
        mapbox_style="white-bg",
        zoom=6.8,
        center={"lat": 38.8500, "lon": -76.6413},
        opacity=0.7,
        labels={selected_dose: "People Vaccinated"},
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return container, fig


if __name__ == "__main__":
    app.run_server(debug=True)
