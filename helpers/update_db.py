import os
import requests
import datetime as dt
import pandas as pd
from sqlalchemy import create_engine
import helpers

DATABASE_URL = os.getenv('DATABASE_URL')

def main():
    engine = create_engine(DATABASE_URL)

    # Use datetime to get epoch of each days date for query
    # Data for the previous day is updlaoded daily
    today = dt.date.today().strftime('%d/%m/%Y')
    yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime('%d/%m/%Y')

    # Insert date range into query string
    query = (
        'https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/'
        'MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose/FeatureServer/0/query?'
        f'where=VACCINATION_DATE%20%3E%3D%20TIMESTAMP%20%27{yesterday}%27%20'
        f'AND%20VACCINATION_DATE%20%3C%3D%20TIMESTAMP%20%27{today}%27'
        '&outFields=VACCINATION_DATE,County,SecondDoseCumulative,SingleDoseCumulative,'
        'FirstDoseCumulative&outSR=4326&f=json'
    )

    # Query the arcGIS database for data after update
    with requests.get(query) as response:
        updated_data = response.json()['features']

    records = (row['attributes'] for row in updated_data)

    df = pd.DataFrame.from_records(records)

    # Transform queried data to fit within postgres database
    df = helpers.clean_df(df)
    df['vaccination_date'] = pd.to_datetime(df['vaccination_date'], unit='ms')
    df['vaccination_date'] = df['vaccination_date'].dt.tz_localize(None)

    # Append data to postgres database
    df.to_sql('vaccines', engine, if_exists='append')
    print(df)
    print('SUCCESSFULLY UPDATED POSTGRES DB')

if __name__ =="__main__":
    main()