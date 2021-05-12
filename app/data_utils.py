
import os
import io
from pathlib import Path
from typing import Tuple

import boto3
import pandas as pd
from dash_table import FormatTemplate
from dash_table.Format import Format
import sqlalchemy
import numpy as np


FILES_DIR = Path(__file__).parent / "files"
POP_EST_PATH = FILES_DIR / "Population_Estimates_by_County.csv"

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")

DATABASE_URI = os.getenv("DATABASE_URI")


class LoadS3:
    def __init__(self):
        self.s3_resource = boto3.resource(
            "s3", aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
        )
        self.vax_data_obj = self.s3_resource.meta.client.get_object(
            Bucket=AWS_S3_BUCKET, Key="MD_Vax_Data.csv"
        )


    def read_s3_df(self) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(self.vax_data_obj["Body"].read()))
    

class LoadDb:
    def __init__(self):
        self.engine = sqlalchemy.create_engine(DATABASE_URI)


    def read_db_df(self) -> pd.DataFrame:
        df = pd.read_sql_table("vaccines", self.engine)
        df.drop_duplicates(inplace=True)
        return df


class CallbackUtils:
    def __init__(self):
        self.census_data = pd.read_csv(POP_EST_PATH.resolve(), dtype={"Population": int})
        self.features = [
            "County",
            "First Dose",
            "Second Dose",
            "Single Dose",
            "At Least One Vaccine",
            "Fully Vaccinated",
        ]


    def get_slider_date(self, df: pd.DataFrame, selected_date_index: int) -> np.datetime64:
        """Return timestamp based on numerical index provided by slider"""
        return df["date"].unique()[selected_date_index]


    def filter_by_date(self, df: pd.DataFrame, slider_date: np.datetime64) -> pd.DataFrame:
        """
        Filter the dataframe based on the date entered
        Return filtered dataframe
        """
        dff = df.copy(deep=True)
        return dff[dff["date"] == slider_date]


    def filter_by_county(self, df: pd.DataFrame, county_name: str) -> pd.DataFrame:
        """Use Pandas boolean indexing to return a county-filtered dataframe"""
        stats_df = df.loc[df["County"] == county_name, self.features]
        stats_df.fillna(0)
        stats_df.drop(columns="County", inplace=True)
        return stats_df


    def get_county_stats(self, dff: pd.DataFrame, percent: bool = False) -> pd.DataFrame:
        """
        Input date filtered dataframe, percent Bool (optional)
        Return a DataFrame with 3 cols:
        "First Dose", "Second Dose", & "Single Dose"
        Values (percent=False(default)):absolute people vacciated in county_name OR
        Values (percent=True): relative people vaccinated in county_name
        """
        # Get rid of index
        dff.reset_index(drop=True, inplace=True)

        if percent == True:
            # Copy estimated pop by county
            county_pops = self.census_data.copy(deep=True)

            # Filter for selected location
            merged_df = pd.merge(county_pops, dff, how="left", on="County")

            # Create list of columns to calculate percentage on
            county_stats_col_list = [col for col in self.col_list if col != "County"]

            # Get percent of total population vaccinated for numeric columns
            merged_df[county_stats_col_list] = merged_df[county_stats_col_list].div(
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

        atleast1_sum_state = dff["First Dose"].sum()
        fully_sum_state = dff["Second Dose"].sum() + dff["Single Dose"].sum()

        if percent == True:
            state_pop = self.census_data["Population"].sum()
            atleast1_sum_state /= state_pop
            fully_sum_state /= state_pop

        return atleast1_sum_state, fully_sum_state


    def format_table(self, percent: bool = False):
        """Return dash_table formatting string based on boolean arg"""
        if not percent:
            return Format().group(True)
        else:
            return FormatTemplate.percentage(2)

    
    def get_county_pop(self, county_name: str):
        return int(
            self.census_data.loc[
                self.census_data["County"] == county_name, "Population"
            ].values
        )

