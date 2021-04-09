from pathlib import Path
import sys

# Add module to python PATH for Docker container (unable to do relative imports in container)
pulldata_path = Path(__file__).parent / "pulldata"
sys.path.append(pulldata_path.resolve())

import pulldata  # Local import
import schedule
import time

BACKEND_DIR = Path(__file__).parent  # Directory of current file
# Navigate to folder that stores vaccine data
LOCAL_FILE_PATH = BACKEND_DIR / "scheduled_data" / "MD_Vax_Data.csv"
# Get updated COVID-19 data from https://data.imap.maryland.gov/
DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"


def get_data():
    pulldata.get_vax_data(DATA_URL, LOCAL_FILE_PATH)


if __name__ == "__main__":
    schedule.every().day.at("10:00").do(get_data)
    
    while True:
        n = schedule.idle_seconds()
        time.sleep(n - 1) # sleep until next job
        schedule.run_pending()