import os
import io

from urllib.error import HTTPError
import pandas as pd
import boto3

AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")

DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"

# S3: Define location to write (and overwrite) vaccine data
s3 = boto3.resource('s3')

def main():
    get_vax_data(DATA_URL, s3)

def get_vax_data(url, s3_resource):
    """
    Attempt to get updated csv from URL
    Transform and clean the data before saving it to S3 if successful
    Upload df as csv to AWS S3
    """
    try:
        df = pd.read_csv(url)  # Pandas reads directly from URL input

    except HTTPError as e:
        # TODO Email Admin with error summary
        print(e)
        return

    else:
        # Clean and replace the file locally as backup
        # Drop daily columns
        df.drop(
            columns=["FirstDoseDaily", "SecondDoseDaily", "SingleDoseDaily"],
            inplace=True,
        )

        # Strip trailing whitespace from end of County names
        df["County"] = df["County"].str.rstrip()

        df = df[
            ~(df["VACCINATION_DATE"] <= "2020-12-01")
        ]  # Get rid of data before this date

        df.fillna(0, inplace=True)  # Fill missing entries with 0

        # Compute and store aggregates in df to save on load time
        # Get county total of at least 1 vaccination and full vaccinations
        df["At Least One Vaccine"] = (
            df["FirstDoseCumulative"] + df["SingleDoseCumulative"]
        )
        df["Fully Vaccinated"] = df["SecondDoseCumulative"] + df["SingleDoseCumulative"]

        df.rename(
            columns={
                "FirstDoseCumulative": "First Dose",
                "SecondDoseCumulative": "Second Dose",
                "SingleDoseCumulative": "Single Dose",
            },
            inplace=True,
        )

    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer)
    s3_resource.Object(AWS_S3_BUCKET, 'MD_Vax_Data.csv').put(Body=csv_buffer.getvalue())


if __name__ == "__main__":
    main()  # Run job on startup
