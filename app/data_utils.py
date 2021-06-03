import os
import io
from typing import Tuple
import json

import boto3
import boto3.session
import pandas as pd
from dash_table import FormatTemplate
from dash_table.Format import Format
import sqlalchemy
import numpy as np

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
ACCESS_ID = os.getenv("AWS_ACCESS_KEY_ID")
ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

DATABASE_URI = os.getenv("DATABASE_URI")


class LoadS3:
    def __init__(self, key: str):
        self.key = key
        session = boto3.session.Session(
            aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
        )
        self.s3_resource = session.resource("s3")
        self.obj = self.s3_resource.meta.client.get_object(
            Bucket=AWS_S3_BUCKET, Key=self.key
        )

    def read_s3_geojson(self):
        return json.load(io.BytesIO(self.obj["Body"].read()))

    def read_s3_df(self) -> pd.DataFrame:
        """Read data from S3 to Pandas DataFrame"""
        return pd.read_csv(io.BytesIO(self.obj["Body"].read()))

    def prep_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform Pandas DataFrame after csv read"""
        df.rename(
            columns={
                "vaccination_date": "date",
                "county": "County",
                "firstdosecumulative": "First Dose",
                "seconddosecumulative": "Second Dose",
                "singledosecumulative": "Single Dose",
                "fullvaccinatedcumulative": "Fully Vaccinated",
                "atleastonedosecumulative": "At Least One Vaccine",
                "firstdosedaily": "First Dose Daily",
                "seconddosedaily": "Second Dose Daily",
                "singledosedaily": "Single Dose Daily",
            },
            inplace=True,
        )

        # Convert to datetime
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

        # Sort by date ad create numeric representation for each unique date for numeric Slider input
        df.sort_values(by="date", inplace=True)
        return df

    def etl_pipeline(self) -> pd.DataFrame:
        df = self.read_s3_df()
        return self.prep_df(df)


class LoadDb:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(DATABASE_URI)

    def read_db_df(self) -> pd.DataFrame:
        """Read data from Postgres DB to Pandas DataFrame"""
        df = pd.read_sql_table("vaccines", self.engine)
        df.drop_duplicates(inplace=True)
        return df


class CallbackUtils:
    def __init__(self):
        census_s3 = LoadS3("Population_Estimates_by_County.csv")
        self.census_data = census_s3.read_s3_df()
        self.features = [
            "County",
            "First Dose",
            "Second Dose",
            "Single Dose",
            "At Least One Vaccine",
            "Fully Vaccinated",
        ]

    def get_numdate(self, df: pd.DataFrame) -> int:
        return [i for i in range(len(df["date"].unique()))]

    def get_slider_date(
        self, df: pd.DataFrame, selected_date_index: int
    ) -> np.datetime64:
        """Return timestamp based on numerical index provided by slider"""
        return df["date"].unique()[selected_date_index]

    def get_county_pop(self, county_name: str) -> int:
        """Match df.County on county name input str"""
        return int(
            self.census_data.loc[
                self.census_data["County"] == county_name, "Population"
            ].values
        )

    def filter_by_date(
        self, df: pd.DataFrame, slider_date: np.datetime64
    ) -> pd.DataFrame:
        """Filter the dataframe based on the date entered"""
        dff = df.copy(deep=True)
        return dff[dff["date"] == slider_date]

    def filter_by_county(self, df: pd.DataFrame, county_name: str) -> pd.DataFrame:
        """Use Pandas boolean indexing to return a county-filtered dataframe"""
        stats_df = df.loc[df["County"] == county_name, self.features]
        stats_df.fillna(0)
        stats_df.drop(columns="County", inplace=True)
        return stats_df

    def get_county_stats(
        self, dff: pd.DataFrame, percent: bool = False
    ) -> pd.DataFrame:
        """
        Create a DataFrame from the input with the following values:
        "First Dose", "Second Dose", & "Single Dose"
        Normalize data values if param percent == True
        """
        # Get rid of index
        dff.reset_index(drop=True, inplace=True)

        if percent == True:
            # Copy estimated pop by county
            county_pops = self.census_data.copy(deep=True)

            # Filter for selected location
            merged_df = pd.merge(county_pops, dff, how="left", on="County")

            # Create list of columns to calculate percentage on
            county_stats_features = [col for col in self.features if col != "County"]

            # Get percent of total population vaccinated for numeric columns
            merged_df[county_stats_features] = merged_df[county_stats_features].div(
                merged_df.Population, axis=0
            )

            # Return the percent of the population vaccinated for
            return merged_df

        # Otherwise, just use absolute numbers
        return dff

    def get_state_stats(self, dff, percent=False) -> Tuple[np.int64, np.int64]:
        """Compute date-filtered dataframe totals"""
        # dataframe filterd to single day
        dff.copy()  # Shallow copy

        atleast1_sum_state = dff["First Dose"].sum() + dff["Single Dose"].sum()
        fully_sum_state = dff["Second Dose"].sum() + dff["Single Dose"].sum()

        if percent == True:
            state_pop = self.get_county_pop("State")
            atleast1_sum_state /= state_pop
            fully_sum_state /= state_pop

        return atleast1_sum_state, fully_sum_state

    def format_table(self, percent: bool = False):
        """Return dash_table formatting string based on boolean arg"""
        if not percent:
            return Format().group(True)
        else:
            return FormatTemplate.percentage(2)
