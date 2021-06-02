import os
import boto3
from helpers import WriteData
from dotenv import load_dotenv

load_dotenv()

DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"
ACCESS_ID = os.getenv("ACCESS_ID")
ACCESS_KEY = os.getenv("ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")


def main():
    try:
        s3_resource = boto3.resource(
            "s3", aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
        )
    except:
        print("FAILED TO CONNECT TO S3")
    else:
        wd = WriteData(s3_resource=s3_resource)
    try:
        wd.update_s3(DATA_URL, AWS_S3_BUCKET)
        print("SUCCESS: S3 UPDATED")
    except:
        print("S3 WRITE FAILED")


if __name__ == "__main__":
    main()
