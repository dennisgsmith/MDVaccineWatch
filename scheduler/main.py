import os
import time
from sqlalchemy import create_engine
import boto3
from helpers import helpers

DATABASE_URI = os.getenv("DATABASE_URI")
engine = create_engine(DATABASE_URI)

DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"
ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
s3_resource = boto3.resource(
    "s3", aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
)


def main():
    try:
        helpers.update_s3(DATA_URL, s3_resource, AWS_S3_BUCKET)
    except:
        print("S3 UPDATE FAILED")
    try:
        helpers.update_db(engine)
    except:
        print("DATABASE UPDATE FAILED")


if __name__ == "__main__":
    main()  # Run only once

    while True:
        time.sleep(1)  # Sleep until process-scheduler kills task
