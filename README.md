# MDVaccineWatch
Tracking Maryland COVID-19 vaccine data by county in real time with Plotly Dash.


## ETL
The Maryland county GeoJSON data allows to create a mask layer that is superimposed on the `mapbox` object. This creates interactive elements for each county. `maryland-counties.geojson` is stored locally in the data folder.

`pandas` loads, queries, cleans and transforms vaccine data from maryland.gov and population data census.gov. The vaccine data (`MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose.csv`) automatically updates when the program is run by passing the cav query direcly into `pd.read_csv(url)`. If the request is successful, the file is saved locally in the data folder (and overwrites older version if one exists). If an `HTTPError` is raised, a dataframe will be created from the local csv. The population data (`Population_Estimates_by_County.csv`) is loacally stored in the data folder.

All of the unneeded "Daily" columns are dropped to improve performace of aggragate functions.

Some entries in the vaccine data were blank, indicating there were no vaccines in the given county on that day. Each blank entry was replaced with a 0.

Some etries occasionally have erronius dates entered that are later corrected. To minimize plotting error, any entries with dates before December 1, 2020 are dropped.

After entries are sorted by date, `numdate` creates a unique index of each date in in the dataframe to make it easier to interface with intercative `dash.dcc` dash core components. This will be evident in the `get_slider_date` helper function.


## App Composition
The `dash.html_components` allow for generation of HTML with Python. This allows for easy integration with `dcc.Graph` objects and other interface options.

`select-dose` (`dcc.Dropdown`) filters the map display (not the text) by type of dose, acting as an input to the callback. This includes the aggregate values created in preprocessing the dataframe. It filters by the colomn selected in this dataframe.

`select-absolute-relative` (`dcc.Radioitems`) displays the information as either absoute numbers (directly from the Vaccine data df) or as relative percentages (Vaccine data divided by its county's estimated total population). This switch reflects both the text-based tabular stats and the choropleth map's representation of the data. It uses the `get_county_stats` function to compute its input (it's fed date-filtered data).

`select-date` (`dcc.Slider`) also affects both the map and the text-based stats. It does this by using the `filter_by_date` function. Since it's values can only be numeric, the dates are each assigned a unique numer that is used as an index. The `min` and `max` are set to the minimum and maximum of this index, which accesses the dates in the `VACCINATION_DATE` column of the Vaccine dataframe.

## Callback
`display_choropleth` takes the values from the dcc components (`select_date`, `select_dose`, and `select-absolute-relative`). When their values are changed, the fucntion updates the choropleth map based on the data they filter from the vaccine dataframe. `maryland-counties` is directly ingested into the Plotly figure (`fig`) and paired with the data using the `featureidkey="properties.name"` argument. The `locations="Counties"` argument allows the function to assign the data to each of the respective counties in the GeoJSON. For the style, a Mapbox account and a `mapbox_accesstoken` was needed to use the "dark" setting. For more information visit the Plotly documentation: https://dash.plotly.com

`display_stats` takes in two of the input proerties as the above funtion (`select_date` and `select-absolute-relative`). It also accept as input the `ClickData` generated when an object on the `choropleth_mapbox` is clicked. From this data, the name of the desired selected county can be accessed, allowing to lookup that county by name on the (date-filtered) dataframe using `filter_by_county`. When triggering the function, the boolean parameter `percent=False` allows users to use the state of `select-absolute-relative` to choose how the data should be represented in the stats. This is the same data being accessed when updating the mapbox figure. In a `dash_table` `DataTable`, cells are formatted based on their respective columns `format` parameter. This parameter accepts different `dash_table` objects from modules such as `dash_table.FormatTemplate` and `dash_table.Format` The helper function `format_table` allows the conditional formatting of absolute or relative data. It accepts a boolean argument that should indicate the format of the table column it is called upon, returning the respective `dash_table` object.

## Installation
To run this project locally, you will need to do a few things:

1. Make sure you are using Python 3.8
2. `git clone` the repo into the desired directory && cd into the repo
3. (Recommended) Set up and activate a [virtual environment](https://docs.python.org/3/library/venv.html)
4. Run `pip install --upgrade pip` and `pip install -r requirements.txt`
5. (Optional) Cusomize the theme, [sign up for a free mapbox account](https://www.mapbox.com)
  - If you would like to use the "dark" theme, or one of the other mapbox themes that require a free token
  - After you sign up for an account and copy your account token to your clipboard:
    - cd into the `app` directory
    - run `echo 'PASTE_YOUR_MAPBOX_KEY_HERE' > .mapbox_token` in the `app` directory
  - Otherwise, the theme will default to "carto-darkmatter". Visit the [plotly docs](https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth_mapbox.html) for more information.
6. Now you can run `python app.py` and use the localhost port given to preview the site!
7. If you have any feedback or run into issues, please feel free to contact me 🙂 📩  dennisgsmith12@gmail.com

## Credits
The GeoJSON mask of Maryland counties is provided courtesy of @frankrowe (https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson).

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).