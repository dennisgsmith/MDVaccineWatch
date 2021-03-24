# MDVaccineWatch
Tracking Maryland COVID-19 vaccine data by county in real time with Plotly Dash.


### ETL
`pandas` queries, cleans and aggregates data from mulitple sources, thens loads them into dataframes. The vaccine data automatically updates when the program is run by passing the cav query direcly into `pd.read_csv(url)`.


`numdate` creates a unique index of each date in in the dataframe to make it easier to interface with intercative `dash.dcc` dash core components.


`total_pop_by_county` TODO


### App Composition
The `dash.html_components` allow for generation of HTML with Python. This allows for easy integration with `dcc.Graph` objects and other interfacing options.


`dcc.RadioItems` filters the dataframe by type of dose, acting as an input to the callback. `dcc.Slider` plays a similar role but filters by date.


### Callback
The slider and radio buttons call `display_choropleth` when their values are changed, updating the map based on the data they filter from the dataframe. The funtion returns a container to display the current selected date and the `plotly.express` `choropleth_mapbox`.


### Credits
The `geojson` mask of Maryland counties is provided courtesy of frankrowe.

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).