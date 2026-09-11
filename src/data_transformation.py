import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import boto3
import json
from datetime import datetime, timezone
from decorators import *

#---------- Download data from S3 ----------#
def download_raw_data(client, bucket_name, s3_key):
    print(f"Downloading raw json snapshots")

    try:
        object_response = client.get_object(Bucket = bucket_name,
                                            Key  = s3_key,
                                            )
        try:
            #Assign the timestamp of extraction
            raw_timestamp_parts = s3_key.rsplit("_", 2)
            raw_timestamp = f"{raw_timestamp_parts[1]}_{raw_timestamp_parts[2]}"
            timestamp = raw_timestamp.removesuffix('.json')

            #Convert into a datetime object
            extraction_time = datetime.strptime(timestamp,"%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
            
        except Exception as e:
            print(f"Couldn't convert extraction time into time object, details: {e}")
            return False

        json_data = json.loads(object_response["Body"].read().decode("utf-8"))
        print(f"Snapshot acquired, ready for transformation!")

        return json_data, extraction_time
        
    except Exception as e:
        print(f"Failed to download JSON Snapshot, details: {e}")

        return False

#---------- Filter Raw data to the wanted features ----------#
def filter_snapshot(snapshot, extraction_time,s3_key):
    print("\nFiltering JSON data...")

    created_at = datetime.strptime(snapshot.get("created_at"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    updated_at = datetime.strptime(snapshot.get("updated_at"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    pushed_at = datetime.strptime(snapshot.get("pushed_at"), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    
    data = {
        "repo_id":snapshot.get("id"),
        "name":snapshot.get("full_name"),
        "owner_id":snapshot.get("owner")["id"],
        "stargazers_count":snapshot.get("stargazers_count"),
        "forks_count":snapshot.get("forks_count"),
        "open_issues":snapshot.get("open_issues_count"),
        "subscribers_count":snapshot.get("subscribers_count"),
        "pushed_at":pushed_at,
        "created_at":created_at,
        "updated_at":updated_at,
        "extracted_at":extraction_time,
        "s3_key":s3_key 
    }
    print("Data filtered successfuly!")

    return data

#---------- Create the main processing function ----------#
@timer
def process_data():
    print("Data processing initialized...")
    #Connecxt to AWS S3 client
    load_dotenv()

    access_id = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = os.getenv("REGION_NAME")
    bucket_name = os.getenv("BUCKET_NAME")

    if not bucket_name:
        print(f"There is no bucket name loaded!")
        return False

    try:
        s3 = boto3.client('s3',
                          aws_access_key_id = access_id,
                          aws_secret_access_key = secret_key,
                          region_name = region)

        list_buckets_response = s3.list_buckets()
        buckets = [bucket["Name"] for bucket in list_buckets_response.get("Buckets", [])]
        if bucket_name not in buckets:
            print(f"The bucket with the name {bucket_name} is not found")
            return False

        objects_response = s3.list_objects_v2(Bucket = bucket_name,
                                              Prefix = "raw_data/")
        json_objects = [obj for obj in objects_response.get("Contents", [])]
        if not json_objects:
            print("No JSON Snapshots were found!")
            return False

        if len(json_objects) <= 1:
            s3_key = json_objects[0]["Key"]
        else:
            latest_snapshot = max(json_objects,
                         key = lambda obj: obj["LastModified"])
            s3_key = latest_snapshot["Key"]
            
    except Exception as e:
        print(f"Couldn't connect to AWS S3, details: {e}")

    try:
        #Download Snapshot from S3
        snapshot, extraction_time = download_raw_data(s3, bucket_name, s3_key)

        #Filter JSON Keys to the chosen keys
        filtered_data = filter_snapshot(snapshot, extraction_time, s3_key)
        print(f"Snapshot has been successfuly processed and ready for loading")

        return filtered_data

    except Exception as e:
        print(f"Snapshot can't be processed, details: {e}")