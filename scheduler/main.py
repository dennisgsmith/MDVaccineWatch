import time
import os
import schedule
from sqlalchemy import create_engine
import boto3
from helpers import helpers

DATABASE_URI = os.getenv("DATABASE_URI")
engine = create_engine(DATABASE_URI)

DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"
AWS_S3_BUCKET = os.getenv('AWS_S3_BUCKET')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION')
s3_resource = boto3.resource('s3')


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
    schedule.every().day.at("12:00").do(main)
    while True:
        schedule.run_pending()
        time.sleep(1)
