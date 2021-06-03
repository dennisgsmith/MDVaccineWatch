import os
import boto3
import boto3.session
from helpers import WriteData

DATA_URL = "https://opendata.arcgis.com/datasets/89c9c1236ca848188d93beb5928f4162_0.csv"
ACCESS_ID = os.getenv("AWS_ACCESS_KEY_ID")
ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
S3_FILE_NAME_NO_EXTENSION = os.getenv("S3_FILE_NAME_NO_EXTENSION")


def main():
    try:
        session = boto3.session.Session(
            aws_access_key_id=ACCESS_ID, aws_secret_access_key=ACCESS_KEY
        )
        s3_resource = session.resource("s3")
    except:
        print("FAILED TO CONNECT TO S3")
    else:
        wd = WriteData(s3_resource=s3_resource)
    try:
        wd.update_s3_df(
            DATA_URL, AWS_S3_BUCKET, s3_file_name_no_extension=S3_FILE_NAME_NO_EXTENSION
        )
        print("SUCCESS: S3 UPDATED")
    except:
        print("S3 WRITE FAILED")


if __name__ == "__main__":
    main()
