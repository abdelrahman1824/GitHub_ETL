import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import boto3
import json

def download_raw_data(s3, bucket_name, s3_key):
    print(f"Downloading raw json snapshots")

    try:
        object_response = s3.get_object(Bucket = bucket_name,
                                            Key = s3_key,
                                            )

        json_data = json.loads(object_response["Body"].read().decode("utf-8"))
        print(f"Snapshot acquired, ready for transformation!")

        return json_data
        
    except Exception as e:
        print(f"Failed to download JSON Snapshot, details: {e}")

        return False

def process_data():

    try:
        #Connecting to AWS S3 client
        load_dotenv()

        access_id = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        region = os.getenv("REGION_NAME")
        bucket_name = os.getenv("BUCKET_NAME")

        try:
            s3 = boto3.client('s3',
                            aws_access_key_id = access_id,
                            aws_secret_access_key = secret_key,
                            region_name = region)

            list_buckets_response = s3.list_buckets()
            buckets = [bucket["Name"] for bucket in list_buckets_response.get("Buckets", [])]
            if bucket_name not in buckets:
                print(f"The bucket with the name {bucket_name} is not found!")
                return False
            
            objects_response = s3.list_objects_v2(Bucket = bucket_name,
                                         Prefix = "raw_data/")
            json_objects = [obj for obj in objects_response.get("Contents", []) if obj["Key"].lower().endswith(".json")]
            if not json_objects:
                print(f"No snapshots found in the bucket")
                return False

            latest_json_snapshot = max(json_objects,
                                       key = lambda object: object["LastModified"])
            s3_key = latest_json_snapshot["Key"]

        except Exception as e:
            print(f"Couldn't connect to AWS S3, details: {e}")
            return False

        #Download Snapshot from S3
        snapshot = download_raw_data(s3, bucket_name, s3_key)

        return snapshot
    
    except Exception as e:
        print(f"Couldn't process the data, details:{e}")
        return False

snapshot = process_data()
print(snapshot)