from urllib.error import HTTPError
from urllib.request import urlopen
import json
from pathlib import Path

import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------

MAPBOX_TOKEN = open(".mapbox_token").read()

HERE = Path(__file__).parent
DATA_FOLDER = HERE / "data"

# Get Maryland counties layer as geojson
# source: frankrowe GH (see README)
GEOJSON_PATH = DATA_FOLDER / "maryland-counties.geojson"

# Total population by county
POP_EST_PATH = DATA_FOLDER / "Population_Estimates_by_County.csv"

# COVID-19 Data
LOCAL_DATA_PATH = list(DATA_FOLDER.glob("MD_COVID19_*"))[0]

# Get updated COVID-19 data from https://data.imap.maryland.gov/
DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"

# Load GeoJSON from local data file
with open(GEOJSON_PATH.resolve()) as f:
    counties = json.load(f)

# Build dataframe of all county population to get percentages
# Source: https://www.census.gov/
pop_est_by_county = pd.read_csv(POP_EST_PATH.resolve(), dtype={"Population": int})

# Attempt to get updated csv from URL, default to most recent local copy if request fails
try:
    df = pd.read_csv(DATA_URL, dtype={"County": str})  # Pandas reads directly from URL input
    print("SUCCESS: DATA URL Working")

except HTTPError as e:
    print("ERROR: There was a problem accessing the maryland.gov data.")
    print(e)  # TODO: Implement logging
    print("Reading from backup...")
    df = pd.read_csv(LOCAL_DATA_PATH.resolve(), dtype={"County": str})  # Read csv from local backup
    print("SUCCESS: Read local copy from backup")

else:
    # Replace the file locally as backup
    df.to_csv(
        (DATA_FOLDER / "MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose.csv").resolve(),
        index=False,
    )
    print("SUCCESS: Updated local backup (overwrite)")

# Drop daily columns
df.drop(columns=["FirstDoseDaily", "SecondDoseDaily", "SingleDoseDaily"], inplace=True)

# Strip trailing whitespace from end of County names
df["County"] = df["County"].str.rstrip()

# Convert to datetime
df["VACCINATION_DATE"] = pd.to_datetime(df["VACCINATION_DATE"], format="%Y-%m-%d")

df = df[~(df["VACCINATION_DATE"] <= "2020-12-01")]  # Get rid of data before this date

df.fillna(0, inplace=True)  # Fill missing entries with 0

#Compute and store aggregates in df to save on load time
# Get county total of at least 1 vaccination and full vaccinations
df["AtLeastOneVaccine"] = df["FirstDoseCumulative"] + df["SingleDoseCumulative"]
df["FullyVaccinated"] = df["SecondDoseCumulative"] + df["SingleDoseCumulative"]

# Sort by date ad create numeric representation for each unique date for numeric Slider input
df.sort_values(by="VACCINATION_DATE", inplace=True)
numdate = [x for x in range(len(df["VACCINATION_DATE"].unique()))]

col_list = [            
    "County",
    "FirstDoseCumulative",
    "SecondDoseCumulative",
    "SingleDoseCumulative",
    "AtLeastOneVaccine",
    "FullyVaccinated"
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
                # Ouput county stats triggered from choropleth clickData
                dcc.Markdown(id="county-stats"),
                dcc.Markdown(id="dose-stats"),
                # Create Choropleth Mapbox
                html.Div(
                    [
                        html.Div(  # Dopdown menu
                            [
                                html.P(
                                    "Filter map for type of dose:",
                                    style={"color": "#ffffff"},
                                ),
                                dcc.Dropdown(
                                    id="select_dose",
                                    options=[
                                        {
                                            "label": "Total at least one vaccine",
                                            "value": "AtLeastOneVaccine"
                                        },
                                        {
                                            "label": "Total fully vaccinated",
                                            "value": "FullyVaccinated"
                                        },
                                        {
                                            "label": "Partially vaccinated (First Dose Only)",
                                            "value": "FirstDoseCumulative",
                                        },
                                        {
                                            "label": "Fully vaccinated (Second Dose Only)",
                                            "value": "SecondDoseCumulative",
                                        },
                                        {
                                            "label": "Fully vaccinated (Single Dose Only)",
                                            "value": "SingleDoseCumulative",
                                        }
                                    ],
                                    searchable=False,
                                    clearable=False,
                                    value="AtLeastOneVaccine",
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
                                html.P(
                                    "Adjust the timeline slider:"
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
    Output("choropleth", "figure"),
    [Input("select_date", "value"), Input("select_dose", "value"), Input("select-absolute-relative", "value")],
)
def display_choropleth(selected_date, selected_dose, selected_button):  # Callback function
    """Diplay updated mapbox choropleth graph and date text when parameters are changed"""

    print(selected_date)
    print(type(selected_date))

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
        geojson=counties,
        locations="County",
        featureidkey="properties.name",
        zoom=6.8,
        center={"lat": 38.8500, "lon": -77.3213},
        # Configure Colorbar
        color=selected_dose,
        color_continuous_scale="Viridis",
        range_color=(0, mx),
        opacity=0.7
    )
    # mapbox theme & layout
    fig.update_layout(mapbox_style="dark", mapbox_accesstoken=MAPBOX_TOKEN)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # Update Colorbar style
    fig.update_layout(
        coloraxis={
            "colorbar_x": 0.05,
            "colorbar_y": 0.5,
            "colorbar_len": 0.9,
            "colorbar_thickness": 20,
            "colorbar_tickfont_color": "#ffffff",
            "colorbar_tickformat": tick_format
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
        Output("county-stats", "children"),
        Output("dose-stats", "children"),
    ],
    [
        Input("select_date", "value"),
        Input("choropleth", "clickData"),
        Input("select-absolute-relative", "value"),
    ],
)
def display_stats(selected_date, clickData, selected_button):
    """Display additional data on county that is selected via click on the map"""

    print(clickData)
    print(type(clickData))

    slider_date = get_slider_date(df, selected_date)
    dff2 = filter_by_date(df, slider_date)

    output_date_location = f"Date selected: **{slider_date.strftime('%B %-d, %Y')}**"

    p = False
    if selected_button == "Relative":
        p = True

    # Get total state sums before filtering by County
    atleast1_sum_s, fully_sum_s = get_state_stats(dff2, percent=p)

    if not clickData:
        return (
            output_date_location,
            ".",
            "Select a location on the map below to see more info.",
            ".",
        )

    # Get selected county
    # Make sure to return 4 items in the callback!!!!
    county_name = clickData.get("points")[0].get("location")

    output_date_location += f"  |  County selected: **{county_name}**"
    pop_est = int(pop_est_by_county.loc[pop_est_by_county['County'] == county_name, 'Population'].values)
    output_date_location += f"  |  County Estimated Population: **{pop_est:{','}}**"

    pop_est_state = int(pop_est_by_county.Population.sum())

    dff2 = get_county_stats(dff2, percent=p)

    # Filter by county
    stats_df = filter_by_county(dff2, county_name)

    stats_df.fillna(0)

    stats_dict = {}

    # Move averages into dict
    try:
        stats_dict = stats_df.to_dict("records")[0]  # Only returns one item after filter_by_county
        print(stats_dict)
    except IndexError:
        print("ERROR: Missing data for date, returning 0")
        # TODO: Log output
        for col in col_list:
            if col != "County":
                stats_dict[col] = 0

    # The btn_state helper function provides a format specifier for percentages if the ouput is relative
    dose_stats = [
        f"First Dose: **{stats_dict['FirstDoseCumulative']:{btn_state(selected_button)}}**",
        f"Second Dose: **{stats_dict['SecondDoseCumulative']:{btn_state(selected_button)}}**",
        f"Single Dose: **{stats_dict['SingleDoseCumulative']:{btn_state(selected_button)}}**",
    ]

    county_stats = [
        f"County at least one vaccine: **{stats_dict['AtLeastOneVaccine']:{btn_state(selected_button)}}**",
        f"County fully vaccinated: **{stats_dict['FullyVaccinated']:{btn_state(selected_button)}}**",
    ]

    state_stats = [
        f"State at least one vaccine: **{atleast1_sum_s:{btn_state(selected_button)}}**",
        f"State fully vaccinated: **{fully_sum_s:{btn_state(selected_button)}}**",
        f"State Estimated Population: **{pop_est_state:{','}}**",
    ]

    return (
        "  |  ".join(state_stats),
        output_date_location,
        "  |  ".join(county_stats),
        "  |  ".join(dose_stats)
    )

    #TODO: Return stats_dict values to graph_object table instead of plaintext

def get_slider_date(df, selected_date):
    """Return timestamp based on numerical index provided by slider"""
    return df["VACCINATION_DATE"].unique()[selected_date]


def filter_by_date(df, slider_date):
    """
    Make a deep copy of the Pandas dataframe.
    Filter the dataframe based on the date entered
    Return filtered dataframe
    """
    dff = df.copy(deep=True)
    return dff[dff["VACCINATION_DATE"] == slider_date]


def filter_by_county(df, county_name):
    return df.loc[
        df["County"] == county_name, col_list
    ]

def get_county_stats(dff, percent=False):
    """
    Input date filtered dataframe, percent Bool (optional)
    Return a DataFrame with 3 cols: 
    "FirstDoseCumulative", "SecondDoseCumulative", & "SingleDoseCumulative"
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
            merged_df.Population,
            axis=0
        )

        # Return the percent of the population vaccinated for 
        return merged_df

    print(dff.columns)
    # Otherwise, just use absolute numbers
    return dff


def get_state_stats(dff, percent=False):
    """Compute date-filtered dataframe totals"""
    # dataframe filterd to single day
    dff.copy()  # Shallow copy

    atleast1_sum_state = dff["FirstDoseCumulative"].sum()
    fully_sum_state = (
        dff["SecondDoseCumulative"].sum() + dff["SingleDoseCumulative"].sum()
    )

    if percent == True:
        state_pop = pop_est_by_county["Population"].sum()
        atleast1_sum_state /= state_pop
        fully_sum_state /= state_pop

    return atleast1_sum_state, fully_sum_state


def btn_state(selected_button):
    """Returns string formatting based on arg"""
    return ".2%" if selected_button == "Relative" else ","


if __name__ == "__main__":
    app.run_server(debug=True)
