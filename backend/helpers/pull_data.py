from urllib.error import HTTPError
from pathlib import Path
import pandas as pd

BACKEND_DIR = Path(__file__).resolve().parents[1]  # Go two directories up from file location
LOCAL_FILE_PATH = BACKEND_DIR / "files" / "scheduled" / "MD_Vax_Data.csv"  # Navigate to folder that stores vaccine data


# Get updated COVID-19 data from https://data.imap.maryland.gov/
DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"


def main():
    get_vax_data(DATA_URL, LOCAL_FILE_PATH)


def get_vax_data(url, local_file_path):
    """
    Attempt to get updated csv from URL, default to most recent local copy if request fails
    Return the csv as a pandas dataframe
    """
    try:
        df = pd.read_csv(
            url
        )  # Pandas reads directly from URL input
        print("SUCCESS: DATA URL Working")

    except HTTPError:
        print("ERROR: There was a problem accessing the maryland.gov data.")
        print("Reading from backup...")
        df = pd.read_csv(
            local_file_path
        )  # Read csv from local backup
        print("SUCCESS: Read local copy from backup")

    else:
        # Clean and replace the file locally as backup
        # Drop daily columns
        df.drop(columns=["FirstDoseDaily", "SecondDoseDaily", "SingleDoseDaily"], inplace=True)

        # Strip trailing whitespace from end of County names
        df["County"] = df["County"].str.rstrip()

        df = df[~(df["VACCINATION_DATE"] <= "2020-12-01")]  # Get rid of data before this date

        df.fillna(0, inplace=True)  # Fill missing entries with 0

        # Compute and store aggregates in df to save on load time
        # Get county total of at least 1 vaccination and full vaccinations
        df["At Least One Vaccine"] = df["FirstDoseCumulative"] + df["SingleDoseCumulative"]
        df["Fully Vaccinated"] = df["SecondDoseCumulative"] + df["SingleDoseCumulative"]

        df.rename(
            columns={
                "FirstDoseCumulative": "First Dose",
                "SecondDoseCumulative": "Second Dose",
                "SingleDoseCumulative": "Single Dose",
            },
            inplace=True
        )

        df.to_csv(
            local_file_path,
            index=False,
        )
        print("SUCCESS: Updated local backup (overwrite)")
    
    return df


if __name__ == "__main__":
    main()