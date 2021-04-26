import os
from sys import argv
from sqlalchemy import create_engine
import helpers
import pandas as pd

DATABASE_URL = os.getenv("DATABASE_URL")
# Create the database connection with SQL Alchemy for Pandas to read
engine = create_engine(DATABASE_URL)


def main():
    """
    Simple command line script to upload csv to postgres db
    Pass csv to be uploaded as command line argument
    """
    if len(argv) != 2:
        print(len(argv))
        print("USAGE: python csv_to_db.py path/to/file.csv")
        return 1  # TODO Error

    csv_file = argv[1]

    if csv_file[-4:] != ".csv":
        print("ERROR helpers.clean_csv: Input file suffix must be .csv")
        return  # TODO ERROR

    try:
        df = pd.read_csv(csv_file)
    except:
        print("ERROR helpers.clean_csv: Pandas unable to read .csv")
        return

    df = helpers.clean_df(df)  # returns Pandas df

    # datetime data cannot be localized, must be timezone unaware
    df["vaccination_date"] = pd.to_datetime(df["vaccination_date"])
    df["vaccination_date"] = df["vaccination_date"].dt.tz_localize(None)

    df.to_sql("vaccines", engine)


if __name__ == "__main__":
    main()
