Thorughout the COVID-19 pandemic, data has played a integral role in keeping people informed. There is an immense amount of open data that's free to use out there relating to the pandemic, making it a relevant subject for a data-driven web app.

In this article, I go over my process of creating a dashboard application from scratch using Dash and Docker, from the simplest to most challenging aspects of the project.

If you would like to make a similar project of your own, feel free to fork the repository and follow along. Installation instructions are at the bottom of the README :)

# Background & Overview

I got the idea for this project while following along with a [Real Python tutorial on Dash](https://realpython.com/python-dash/). After completing the tutorial and reading thorugh some of Dash and Plotly's documentation, I wanted to simply try mapping a vaccine data from a CSV file (maryland.gov) to county positions on a map. I chose my home state of maryland becuase it is:

- Relevent
- The data is easily accessable
- The size of the data is relatively small

After reading through some of the [Plotly|Dash documentation](https://dash.plotly.com), I structured the html with the Dash API and mapped my data to each county location using GEOJSON data. Then, I created the interfacing tools used to manipulate and filter the data using callback functions.

At this point, I was just reading the data from a static CSV file. The ultimate goal would be to scedule updating the data as a job. I did this by creating a seperate Python script that retrieves the data via "GET" request with Pandas and transforms it, before storing it as a local CSV file to be loaded into the Dash application frontend. The local CSV ensures that the web app will still work if there is an issue retrieving the data from the url.

*Ideally, I would establish a connection to the database that hosts the information and send SQL queries to regularly update it, but that service (ArcGIS) is proprietary, so I an limited to downloading the entire CSV.*

Once I created a seperate script for the job, I found a sceduler to automate the job for me. I picked the Python module [scedule](https://schedule.readthedocs.io/en/stable/) by Dan Bader to run the update data job because it's very simple to use and does't require any external dependencies. There are microservices that could do this, but I wanted to stay PaaS-agnostic at his point because I was still considering the pros and cons of each.

Once the sceduler was working, it was time to containerize everything with Docker. Following the rule of "containers should do one thing", I created two pyhton:3.8 containers:

1. The Dash app itself (app)
2. The data ingestion job (scheduler)

I configured the containers each with their own seperate Dockerfiles and requirements.txt files. The data from the scheduler container is persisted in a volume that it shares over a network connection with the app container. Docker Compose orchestrates the execution of the Dockerfiles, managing the creation of the containers and making sure that the images are built in the necessary order.

Okay, so things are looking good development-wise. I'm thinking about deploying my application to share it with the world. I had been considering Heroku due to it's cost (*free*), but I soon realized that it wouldn't be the best fit for this project because:

**In Heroku, filesystems are *ephemeral***
  - Meaning that mounting volumes would not be possible, or at least not with this file system structure.

**There is no native support for docker-compose.yml**
  - Translating my docker-compose.yml to a heroku.yml didn't sound like the most productive way to spend my time.


# /backend

## pulldata.py
Retrieve data on a dily schedule and feed it into a volume shared with the app container

### Load Data
`pandas` loads, queries, cleans and transforms vaccine data from maryland.gov. The vaccine data (`MD_Vax_Data.csv`) queries direcly from `pd.read_csv(url)`.

### Clean Data
All of the unneeded "Daily" columns are dropped to improve performace of aggragate functions.

Some entries in the vaccine data were blank, indicating there were no vaccines in the given county on that day. Each blank entry was replaced with a 0.

Some etries occasionally have erronius dates entered that are later corrected. To minimize plotting error, any entries with dates before December 1, 2020 are dropped.

### Create local backup
If the request is successful, the file is saved locally in the data folder (and overwrites older version if one exists). If an `HTTPError` is raised, a dataframe will be created from the local csv.

### Automated job execution
`schedule` is being used to automate the jobs. I's a very straightforward and easy to use module because of it's readbility. Learn more about it [here](https://schedule.readthedocs.io/en/stable/).

# /app

## /files
`maryland-counties.geojson` allows the `plotly.express.choropleth_mapbox` to create a mask layer that is superimposed on the map. This creates interactive elements for each county.

`Population_Estimates_by_County.csv` is locally stored in the data folder for calcuating relative percentages dynamically.

### /scheduled_data
This directory recieves a the daily updated data from a shared Docker volume.

## app.py
### numdate
After entries are sorted by date, `numdate` creates a unique index of each date in in the dataframe to make it easier to interface with intercative `dash.dcc` dash core components. This will be evident in the `get_slider_date` helper function.

### Dash Core Components
The `dash.html_components` allow for generation of HTML with Python. This allows for easy integration with `dcc.Graph` objects and other interface options.

`select-dose` (`dcc.Dropdown`) filters the map display (not the text) by type of dose, acting as an input to the callback. This includes the aggregate values created in preprocessing the dataframe. It filters by the colomn selected in this dataframe.

`select-absolute-relative` (`dcc.Radioitems`) displays the information as either absoute numbers (directly from the Vaccine data df) or as relative percentages (Vaccine data divided by its county's estimated total population). This switch reflects both the text-based tabular stats and the choropleth map's representation of the data. It uses the `get_county_stats` function to compute its input (date-filtered data).

`select-date` (`dcc.Slider`) also affects both the map and the text-based stats. It does this by using the `filter_by_date` function. Since it's values can only be numeric, the dates are each assigned a unique numer that is used as an index. The `min` and `max` are set to the minimum and maximum of this index, which accesses the dates in the `VACCINATION_DATE` column of the Vaccine dataframe.

### Callback

`display_choropleth` takes the values from the dcc components (`selected-date-index`, `selected-dose`, and `select-absolute-relative`). When their values are changed, the fucntion updates the choropleth map based on the data they filter from the vaccine dataframe.

`maryland-counties` is directly ingested into the Plotly figure (`fig`) and paired with the data using the `featureidkey="properties.name"` argument. The `locations="Counties"` argument allows the function to assign the data to each of the respective counties in the GeoJSON.

For the style, a Mapbox account and a `mapbox_accesstoken` was needed to use the "dark" setting. For more information visit the Plotly documentation: https://dash.plotly.com


`display_stats` takes in two of the input proerties as the above funtion (`select_date` and `select-absolute-relative`). It also accept as input the `ClickData` generated when an object on the `choropleth_mapbox` is clicked.

From this data, the name of the desired selected county can be accessed, allowing to lookup that county by name on the (date-filtered) dataframe using `filter_by_county`. When triggering the function, the boolean parameter `percent=False` allows users to use the state of `select-absolute-relative` to choose how the data should be represented in the stats. This is the same data being accessed when updating the mapbox figure.

In a `dash_table` `DataTable`, cells are formatted based on their respective columns `format` parameter. This parameter accepts different `dash_table` objects from modules such as `dash_table.FormatTemplate` and `dash_table.Format` The helper function `format_table` allows the conditional formatting of absolute or relative data. It accepts a boolean argument that should indicate the format of the table column it is called upon, returning the respective `dash_table` object.

## Installation
### Running the project with Docker

Check out the [docker docs](https://docs.docker.com/get-started/) if you wnat to learn more about Docker.

1. Make sure you have Docker and Docker Compose installed
2. `git clone` the repo into the desired directory && cd into the repo
3. (Optional) Cusomize the theme, [sign up for a free mapbox account](https://www.mapbox.com)
  - If you would like to use the "dark" theme, or one of the other mapbox themes that require a free token
  - After you sign up for an account and copy your account token to your clipboard:
    - Make sure you're in the project's root directory
    - Run `echo 'PASTE_YOUR_MAPBOX_KEY_HERE' > app/.mapbox_token`
  - Otherwise, the theme will default to "carto-darkmatter". Visit the [plotly docs](https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth_mapbox.html) for more information.
4. Run `docker-compose build`
5. Run `docker-compose up` (add the `-d` flag to run in detached mode)
6. Open the host port in your browser (default http://0.0.0.0:5000/) and preview the site!
7. If you have any feedback or run into issues, please feel free to contact me 🙂 📩  dennisgsmith12@gmail.com

## Credits
The GeoJSON mask of Maryland counties is provided courtesy of @frankrowe (https://github.com/frankrowe/maryland-geojson/blob/master/maryland-counties.geojson).

Vaccination data is provided by Maryland State Gov. (https://data.imap.maryland.gov/)

Total population by county is provided by the U.S. Census Beurau (https://www.census.gov/).