import os
import time
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import dash
from dash_table import DataTable
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from dash_extensions.enrich import ServersideOutput, Trigger, FileSystemStore

from data_utils import CallbackUtils
from data_utils import LoadS3

# -----------------------------------------------------------------------------

FILES_DIR = Path(__file__).parent / "files"

MB_TOKEN = os.getenv("MB_TOKEN")

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

cb = CallbackUtils()
s3 = LoadS3()
df = s3.etl_pipeline()

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
PORT = int(os.getenv("PORT"))
app.title = "#MDVaccineWatch"

def serve_layout():
    return html.Div(
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
                                    id="selected-date-index"
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
                    className="coropleth-container",
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
        html.Button(id='btn', style={'display': 'none'})
    ],
)

app.layout = serve_layout

# -----------------------------------------------------------------------------
# Connect Plotly graphs with Dash components
# Callback functions


@app.callback(
    [
        Output('selected-date-index', 'min'),
        Output('selected-date-index', 'max'),
        Output('selected-date-index', 'value'),
        Output('selected-date-index', 'marks'),
    ],
    Trigger('btn', 'n_clicks')
)
def render_slider(_):
    numdate = s3.get_numdate(df)
    slider_min=numdate[0]
    slider_max=numdate[-1]
    slider_value=numdate[-1]
    slider_marks={
        "label": "date",
        numdate[0]: min(df["date"]).strftime(
            "%m/%d/%Y"
        ),
        numdate[-1]: max(df["date"]).strftime(
            "%m/%d/%Y"
        )
    }
    return slider_min, slider_max, slider_value, slider_marks


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

    slider_date = cb.get_slider_date(df, selected_date)

    dff1 = cb.filter_by_date(df, slider_date)

    p = False
    tick_format = ","
    if selected_button == "Relative":
        # Covert to percent
        p = True
        tick_format = "%"

    dff1 = cb.get_county_stats(dff=dff1, percent=p)

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

    slider_date = cb.get_slider_date(df, selected_date_index)
    dt_slider_date = pd.to_datetime(str(slider_date))
    dff2 = cb.filter_by_date(df, slider_date)

    output_date_location = f"Date selected: **{dt_slider_date.strftime('%B %-d, %Y')}**"

    p = False
    if selected_button == "Relative":
        p = True

    # Get total state sums before filtering by County
    atleast1_sum_s, fully_sum_s = cb.get_state_stats(dff=dff2, percent=p)

    pop_est_state = cb.get_county_pop("State")

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
    county_click = clickData.get("points")[0].get("location")

    output_date_location += f"  |  County Selected: **{county_click}**"
    pop_est = cb.get_county_pop(county_click)
    output_date_location += f"  |  County Estimated Population: **{pop_est:{','}}**"

    dff2 = cb.get_county_stats(dff=dff2, percent=p)

    # Filter by county
    stats_df = cb.filter_by_county(dff2, county_click)

    table_cols = [
        {
            "id": col,
            "name": col,
            "type": "numeric",
            "format": cb.format_table(percent=p),
        }
        for col in stats_df.columns
    ]

    table_data = stats_df.to_dict("records")

    return state_stats, output_date_location, table_cols, table_data


if __name__ == "__main__":
    app.run_server(host="0.0.0.0", port=PORT, debug=True)
