# MDVaccineWatch
Tracking Maryland COVID-19 vaccine data by county in real time with Plotly Dash.

# Process Overview
COVID-19 Vaccine data is sourced from maryland.gov open databases. The data is retrieved once daily at 12:00PM EST and plotted to map box and tabular data visualizations that can be filtered with interactive components on the site. The app's general structure consists of a *scheduler process* and a *web process*, each separated into their own Docker containers.

# Scheduler (/scheduler)
The scheduler process is triggered externally by the Heroku Process Scheduler add-on (pet-project tier), which runs the process once a day.
Scheduler Roles:
1. Fetch the source data via a statically hosted CSV file and database queries
2. Transform and clean the data
3. Upload and overwrite the CSV data to an S3 for asset hosting and OLTP
4. Append the queried data to a PotgreSQL Database for archival and theoretical OLAP

## helpers/helpers.py
A small library of 3 helper functions for loading and transforming data

### clean_df function
This function is called within the other helper functions that retrieve and write the data to storage. Its goal is to reformat each data pull to be consistent:
- All of the unneeded "Daily" columns are dropped
- Some entries in the vaccine data were blank, indicating there were no vaccines in the given county on that day. Each blank entry is replaced with a 0.
- Try/Except blocks wrap much of the data as some of it only pertains to one method of retrieval and not both (CSV dump vs JSON updating queries)

### update_db function
A dynamic query is generated using datetime and f-string formatting to get the data from *yesterday* to *today*, at a specified time. The query returns a JSON response that is loaded into a Pandas DataFrame, transformed, and appended to a Postgres database.

### update_s3 function
The vaccine data is retrieved directly via HTTP using `pd.read_csv(url)`. It is transformed and uploaded to an AWS S3 bucket.

## helpers/csv_to_db.py
A simple script that uploads a local CSV copy of the data to the connected PostgreSQL database via Pandas via command line argument.

## main.py
The entry point for execution, calling both `update_db` and `update_s3` in the `main` function call.
Due to the implementation of the scheduler that triggers this process, after the main function is invoked, the script will loop on `time.sleep(1)` until the function is closed by the Heroku Process Scheduler (the regular Heroku Scheduler add-on does not support processes other than the **web** type when running docker containers).

# Web (/app)
The web process uses a gunicorn wsgi server.
Web Roles:
1. Read csv data from the configured S3 bucket into Pandas DataFrame
2. Plot the data to a map box and data table using the Plotly Dash framework
3. Render the site's layout using Dash's html components
4. Configure the data with callback functions to create a dynamic interface

## /files/
- maryland-counties.geojson allows the `plotly.express.choropleth_mapbox` to create a mask layer that is superimposed on the map. This creates interactive elements for each county.
- Population_Estimates_by_County.csv is locally stored for calculating relative percentages dynamically.

## /assets/
This folder stores the css and favicon.ico, it is automatically recognized and loaded into the app on initialization.

## gunicorn_starter.sh
A shell script that acts as the entry point for the application to run on the wsgi server when the container is spun-up with Docker. 

## app.py
The main component of the application which runs on the gunicorn wsgi server.

### ETL
The local and S3 data is loaded into the session for use. Optionally, the data can be read in directly from the PostgreSQL db. After entries are sorted by date, `numdate` creates a unique index of each date in in the dataframe to make it easier to interface with interactive `dash.dcc` dash core components. This will be evident in the `get_slider_date` helper function.

### Dash Core Components
The `dash.html_components` allow for generation of HTML with Python. This allows for easy integration with `dcc.Graph` objects and other interface options.

`select-dose` (`dcc.Dropdown`) filters the map display (not the text) by type of dose, acting as an input to the callback. This includes the aggregate values created in preprocessing the dataframe. It filters by the column selected in this dataframe.

`select-absolute-relative` (`dcc.Radioitems`) displays the information as either absolute numbers (directly from the Vaccine data df) or as relative percentages (Vaccine data divided by its county's estimated total population). This switch reflects both the text-based tabular stats and the choropleth map's representation of the data. It uses the `get_county_stats` function to compute its input (date-filtered data).

`select-date` (`dcc.Slider`) also affects both the map and the text-based stats. It does this by using the `filter_by_date` function. Since its values can only be numeric, the dates are each assigned a unique number that is used as an index. The `min` and `max` are set to the minimum and maximum of this index, which accesses the dates in the `VACCINATION_DATE` column of the Vaccine dataframe.

### Callback functions
`display_choropleth` takes the values from the dcc components (`selected-date-index`, `selected-dose`, and `select-absolute-relative`). When their values are changed, the function updates the choropleth map based on the data they filter from the vaccine dataframe.

`maryland-counties` is directly ingested into the Plotly figure (`fig`) and paired with the data using the `featureidkey="properties.name"` argument. The `locations="Counties"` argument allows the function to assign the data to each of the respective counties in the GeoJSON.

For the style, a Mapbox account and a `mapbox_accesstoken` was needed to use the "dark" setting. For more information visit the Plotly documentation: https://dash.plotly.com


`display_stats` takes in two of the input properties as the above function (`select_date` and `select-absolute-relative`). It also accept as input the `ClickData` generated when an object on the `choropleth_mapbox` is clicked.

From this data, the name of the desired selected county can be accessed, allowing to lookup that county by name on the (date-filtered) dataframe using `filter_by_county`. When triggering the function, the boolean parameter `percent=False` allows users to use the state of `select-absolute-relative` to choose how the data should be represented in the stats. This is the same data being accessed when updating the mapbox figure.

In a `dash_table` `DataTable`, cells are formatted based on their respective columns `format` parameter. This parameter accepts different `dash_table` objects from modules such as `dash_table.FormatTemplate` and `dash_table.Format` The helper function `format_table` allows the conditional formatting of absolute or relative data. It accepts a boolean argument that should indicate the format of the table column it is called upon, returning the respective `dash_table` object.


## Credits
The GeoJSON mask of Maryland counties is provided courtesy of @frankrowe (https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson).

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).

The favicon was generated using the following graphics from Twitter Twemoji:

- Graphics Title: 1f489.svg
- Graphics Author: Copyright 2020 Twitter, Inc and other contributors (https://github.com/twitter/twemoji)
- Graphics Source: https://github.com/twitter/twemoji/blob/master/assets/svg/1f489.svg
- Graphics License: CC-BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
