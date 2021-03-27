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

`display_stats` takes in two of the input proerties as the above funtion (`select_date` and `select-absolute-relative`). It also accept as input the `ClickData` generated when an object on the `choropleth_mapbox` is clicked. From this data, the name of the desired selected county can be accessed, allowing to lookup that county by name on the (date-filtered) dataframe using `filter_by_county`. When triggering the function, the boolean parameter `percent=False` allows users to use the state of `select-absolute-relative` to choose how the data should be represented in the stats. This is the same data being accessed when updating the mapbox figure. The helper function, `btn_state` allows the conditional formatting of absolute or relative data. If the button state passed in is "Realtive" the appropirate string-format symbol will be returned ("%") otherwise, the funtion will return string-formatting for absolute values.

## Credits
The GeoJSON mask of Maryland counties is provided courtesy of @frankrowe (https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson).

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).