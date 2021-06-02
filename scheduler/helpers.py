import io
import datetime as dt
from typing import Union

import sqlalchemy
import requests
import pandas as pd
from urllib.error import HTTPError


class WriteData:
    def __init__(
        self,
        s3_resource=None,  # boto3 type hinting not actively maintained
        db_conn: Union[sqlalchemy.engine.base.Engine, None] = None,
    ):
        self.s3_resource = s3_resource
        self.db_conn = db_conn

    # Clean up the data in pandas
    def clean_df(self, df: pd.DataFrame) -> Union[pd.DataFrame, None]:
        """clean pandas df and return transformed dataframe"""
        # Clean and replace the file locally as backup
        try:
            # Strip trailing whitespace from end of County names
            df["County"] = df["County"].str.rstrip().replace("", "Unknown")

            df.fillna(0, inplace=True)  # Fill missing entries with 0

        except:
            raise Exception("ERROR helpers.clean_csv: Could not clean file")

        try:
            # all cols to lowercase for postgres to play nicely
            df.columns = [x.lower() for x in df.columns]
            return df
        except:
            print("Could not convert columns to lowercase")
            return

    def upload_df_to_s3_as_csv(
        self, df: pd.DataFrame, bucket_name: str, file_name_no_extension: str
    ) -> bool:
        """Upload a datafrom to a a given S3 bucket after creating resource in class"""
        try:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer)
            self.s3_resource.Object(bucket_name, file_name_no_extension).put(
                Body=csv_buffer.getvalue()
            )
            return True

        except:
            print(
                "ERROR: Could not upload raw to S3.",
                "Did you create an S3 resource when instantiating the class?"
            )
            return False

    def update_s3_df(
        self, url: str, bucket_name: str, s3_file_name_no_extension: str
    ) -> bool:
        """Upload Pandas df as csv to AWS S3"""
        if not self.s3_resource:
            print("Must define s3_resource on class instantiation")
            return False
        try:
            df = pd.read_csv(url)  # Pandas reads directly from URL input
            # Upload raw data into data lake for archiving
            self.upload_df_to_s3_as_csv(
                df, bucket_name, f"{s3_file_name_no_extension}_raw.csv"
            )

        except HTTPError as e:
            # TODO Email Admin with error summary
            print(e)
            return False

        else:
            df = self.clean_df(df)
            # Upload clean data for use in web app
            self.upload_df_to_s3_as_csv(
                df, bucket_name, f"{s3_file_name_no_extension}_clean.csv"
            )

        return True

    def update_postgres_db(self, from_csv: bool = False) -> bool:
        """
        Update postgres db for archival purposes
        Clean data before uploading
        """
        if not self.db_conn:
            print("Must define db_conn on class instantiation")
            return False
        # Use datetime to get epoch of each days date for query
        # Data for the previous day is updlaoded daily
        yesterday = (dt.date.today() - dt.timedelta(days=1)).strftime("%d/%m/%Y")
        today = dt.date.today().strftime("%d/%m/%Y")

        # Insert date range into query string
        query = (
            "https://services.arcgis.com/njFNhDsUCentVYJW/arcgis/rest/services/"
            "MD_COVID19_TotalVaccinationsCountyFirstandSecondSingleDose/FeatureServer/0/query?"
            f"where=VACCINATION_DATE%20%3E%3D%20TIMESTAMP%20%27{yesterday}%27%20"
            f"AND%20VACCINATION_DATE%20%3C%3D%20TIMESTAMP%20%27{today}%27"
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
        df = self.clean_df(df)
        df["vaccination_date"] = pd.to_datetime(df["vaccination_date"], unit="ms")
        df["vaccination_date"] = df["vaccination_date"].dt.tz_localize(None)

        if from_csv:
            # First write to db
            df.to_sql("vaccines", self.db_conn)

        else:
            # Append data to postgres database
            df.to_sql("vaccines", self.db_conn, if_exists="append")

        print(df)
        print("SUCCESSFULLY UPDATED DATABASE")
        return True
