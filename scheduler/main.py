import os
import time
from sqlalchemy import create_engine
import boto3
from helpers.helpers import WriteData

DATABASE_URI = os.getenv("DATABASE_URI")
DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"
ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")


def main():
    try:
        engine = create_engine(DATABASE_URI)
    except:
        print("FAILED TO CONNECT TO DB")
    try:
        s3_resource = boto3.resource(
            "s3", aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
        )
    except:
        print("FAILED TO CONNECT TO S3")
    else:
        wd = WriteData(s3_resource=s3_resource, db_conn=engine)
    try:
        wd.update_s3(DATA_URL, AWS_S3_BUCKET)
        print("SUCCESS: S3 UPDATED")
    except:
        print("S3 WRITE FAILED")
    try:
        wd.update_postgres_db()
        print("SUCCESS: DB UPDATED")
    except:
        print("DATABASE APPEND FAILED")


if __name__ == "__main__":
    main()  # Run only once

    while True:
        time.sleep(1)  # Sleep until process-scheduler kills task
