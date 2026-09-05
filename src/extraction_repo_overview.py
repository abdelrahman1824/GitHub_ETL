import requests
from dotenv import load_dotenv
import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from datetime import datetime
import tempfile

# ---------- Configuration ---------- #

def load_github_token (): #PAT (Personal Access Token) validation Function
    load_dotenv()

    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise ValueError("GITHUB_TOKEN not found in environmental variables")
    else:
        print("GITHUB_TOKEN is found!")
    return token


# ---------- Request Setup ---------- #

def build_api_headers(token): #Building an API request authentication Function

    return {'Authorization': f"Bearer {token}", #Authorization head for PAT
           'Accept': 'application/json'} #Accept token for response specification
    

# ---------- Data Extraction ---------- #

def fetch_tensorflow_repo(headers):
    url = "https://api.github.com/repos/tensorflow/tensorflow"
    connect_timeout = 3
    read_timeout = 7

    #Error handling
    try:
        response = requests.get(url, headers = headers, timeout = (connect_timeout, read_timeout))
        time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    except requests.exception.Timeout:
        raise RuntimeError("GitHub API request timeout")
    
    if response.status_code != 200:
        raise ValueError(f"Error: HTTP {response.status_code}, {response.text}")

    print(f"Response is successful, HTTP {response.status_code}")
    data = response.json() #Parse JSON data

    return data, time_stamp
    

# ---------- Creating JSON file to save data ---------- #

def upload_json_file_to_s3(data, time_stamp):
    print("Uploading extraction snapshot to S3...")
    file_name = fr"tensorflow_tensorflow_{time_stamp}.json"
    
    load_dotenv()

    key_id = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket = os.getenv("BUCKET_NAME")
    region = os.getenv("REGION")

    print(f"AWS_ACCESS_KEY_ID = {key_id}")

    print(f"AWS_SECRET_ACCESS_KEY = {'FOUND' if secret_key else None}")

    print(f"BUCKET_NAME = {bucket}")

    print(f"REGION = {region}")

    print("Connecting to AWS S3...")
    try:
        s3 = boto3.client('s3',
                          aws_access_key_id = key_id,
                          aws_secret_access_key = secret_key,
                          region_name = region)
        
        s3_key = f"raw_data/{file_name}"

        s3.put_object(Bucket = bucket, Key = s3_key,
                      Body = json.dumps(data, indent = 4, ensure_ascii=False),
                      ContentType = "application/json")

        print(f"Snapshot uploaded succesfuly at" 
              f"{datetime.now().strftime("%Y%m%d_%H%M%S")}")

        return True

    except Exception as e:
        print(f"Failed to upload extraction snapshot, details: {e}")

        return False


# ---------- Verify that data is uploaded ---------- #

def verify_upload():
    print("\nVerifying data is uploaded...")

    load_dotenv()
    key_id = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket = os.getenv("BUCKET_NAME")
    region = os.getenv("REGION")
    
    print("Connecting to AWS S3...")
    try:
        s3 = boto3.client('s3',
                            aws_access_key_id = key_id,
                            aws_secret_access_key = secret_key,
                            region_name = region)

        bucket_content = s3.list_objects_v2(Bucket = bucket, Prefix = "raw_data")
        snapshots_uploaded = len(bucket_content["Contents"])

        print(f"Snapshot is captured and uploaded Successfuly")
        print(f"Snapshots Uploaded: {snapshots_uploaded}")

        return True

    except Exception as e:
        print(f"Error while verifying uploaded snapshots, details: {e}")

        return False


# ---------- Main Extraction Script ---------- #
def main():
    #Load API Token for GitHub
    token = load_github_token()

    #Configure API Headers
    headers = build_api_headers(token)

    #Request the API URL data
    data, time_stamp = fetch_tensorflow_repo(headers)
    
    #Upload JSON snapshot in S3
    success = upload_json_file_to_s3(data, time_stamp)

    return success

if __name__ == "__main__":
    success = main()

    if success:
        verify_upload()

