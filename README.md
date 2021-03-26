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
The `dash.html_components` allow for generation of HTML with Python. This allows for easy integration with `dcc.Graph` objects and other interfacing options.


`dcc.RadioItems` filters the dataframe by type of dose, acting as an input to the callback. `dcc.Slider` plays a similar role but filters by date.


## Callback
The slider and radio buttons call `display_choropleth` when their values are changed, updating the map based on the data they filter from the dataframe. The funtion returns a container to display the current selected date and the `plotly.express` `choropleth_mapbox`.


## Credits
The `geojson` mask of Maryland counties is provided courtesy of @frankrowe (https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson).

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).