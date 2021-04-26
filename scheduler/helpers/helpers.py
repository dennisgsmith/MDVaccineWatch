import io
import requests
import datetime as dt
import pandas as pd
from urllib.error import HTTPError


# Clean up the data in pandas
def clean_df(df):
    """
    clean pandas df and return transformed dataframe
    ::df:: raw pandas dataframe before transform
    """
    # Clean and replace the file locally as backup
    try:
        # Drop daily columns
        df.drop(
            columns=["FirstDoseDaily", "SecondDoseDaily", "SingleDoseDaily"],
            inplace=True,
        )
    except:
        pass

    try:
        # Strip trailing whitespace from end of County names
        df["County"] = df["County"].str.rstrip()

        df.fillna(0, inplace=True)  # Fill missing entries with 0

        # Compute and store aggregates in df to save on load time
        # Get county total of at least 1 vaccination and full vaccinations
        df["AtLeastOneVaccine"] = df["FirstDoseCumulative"] + df["SingleDoseCumulative"]
        df["FullyVaccinated"] = df["SecondDoseCumulative"] + df["SingleDoseCumulative"]
        pass
    except:
        print("ERROR helpers.clean_csv: Could not clean file")
        return

    try:
        # all cols to lowercase for postgres to play nicely
        df.columns = [x.lower() for x in df.columns]
        return df
    except:
        print("Counld not convert columns to lowercase")
        return


def update_db(db_engine):
    """
    Update postgres db for archival purposes
    Clean data before uploading
    ::db_engine:: sqlalchemy database connection
    """
    # Use datetime to get epoch of each days date for query
    # Data for the previous day is updlaoded daily
    yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%d/%m/%Y")

    # Insert date range into query string
    query = (
        "https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/"
        "MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose/FeatureServer/0/query?"
        f"where=VACCINATION_DATE%20%3E%3D%20TIMESTAMP%20%27{yesterday}%27%20"
        f"AND%20VACCINATION_DATE%20%3C%3D%20TIMESTAMP%20%27{yesterday}%27"
        "&outFields=VACCINATION_DATE,County,SecondDoseCumulative,SingleDoseCumulative,"
        "FirstDoseCumulative&outSR=4326&f=json"
    )

    # Query the arcGIS database for data after update
    with requests.get(query) as response:
        updated_data = response.json()["features"]

    records = (row["attributes"] for row in updated_data)

    df = pd.DataFrame.from_records(records)

    if df.empty:
        print("No new data from source!")
        print("DATABASE IS UP TO DATE")
        return False

    # Transform queried data to fit within postgres database
    df = clean_df(df)
    df["vaccination_date"] = pd.to_datetime(df["vaccination_date"], unit="ms")
    df["vaccination_date"] = df["vaccination_date"].dt.tz_localize(None)

    # Append data to postgres database
    df.to_sql("vaccines", db_engine, if_exists="append")
    print(df)
    print("SUCCESSFULLY UPDATED DATABASE")
    return True


def update_s3(url, s3_resource, bucket_name):
    """
    Upload Pandas df as csv to AWS S3
    ::url:: CSV to retrieve data
    ::s3_resource:: AWS s3 bucket connection
    ::bucket_name:: name of AWS_S3 bucket
    """
    try:
        df = pd.read_csv(url)  # Pandas reads directly from URL input

    except HTTPError as e:
        # TODO Email Admin with error summary
        print(e)
        return False

    else:
        df = clean_df(df)

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    s3_resource.Object(bucket_name, 'MD_Vax_Data.csv').put(Body=csv_buffer.getvalue())

    return True
