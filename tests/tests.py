import pandas as pd
from pathlib import Path
import os
from dotenv import load_dotenv
import boto3
import json
import psycopg

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


def create_postgres_connection():
    load_dotenv()

    #Load PostgreSQL .env variables
    username = os.getenv("POSTGRES_USERNAME")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTRGES_PORT")

    #Establish PostreSQL Connection
    postgres_credentials = {
        "POSTGRES_USERNAME": username,
        "POSTGRES_PASSWORD": password,
        "POSTGRES_DB": database,
        "POSTGRES_HOST": host,
        "POSTGRES_PORT": port
    }

    missing_values = [name for name, value in postgres_credentials.items()
                      if not value]

    if missing_values:
        raise ValueError("Missing PostgreSQL Credentials"
                         + ",  ".join(missing_values))

    postgres_connection = psycopg.connect(
        host = host,
        port = port,
        dbname = database,
        user = username,
        password = password
    )

    return postgres_connection


def load_snapshot(processed_data):
    insert_repository = """ 
    INSERT INTO analytics.repositories
    (
    github_repo_id,
    repo_name,
    owner_id,
    created_at
    )
    VALUES
    (
    %(repo_id)s,
    %(name)s,
    %(owner_id)s,
    %(created_at)s
    )
    ON CONFLICT (github_repo_id, repo_name)
    DO NOTHING
    RETURN repo_id
    """

    insert_snapshot = """
    INSERT INTO analytics.repository_snapshots
    (
    repository_name,
    repository_id,
    owner_id,
    stargazers_count,
    forks_count,
    open_issues,
    subscribers_count,
    created_at,
    pushed_at,
    updated_at,
    extracted_at,
    s3_object
    )
    VALUES
    (
    %(name)s,
    %(repo_id)s,
    %(owner_id)s,
    %(stargazers_count)s,
    %(forks_count)s,
    %(open_issues)s,
    %(subscribers_count)s,
    %(created_at)s,
    %(pushed_at)s,
    %(updated_at)s,
    %(extracted_at)s,
    %(s3_key)s
    )
    RETURNING snapshot_id
    """

    try:
        postgres_connection = create_postgres_connection()

        with postgres_connection as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    insert_repository,
                    processed_data
                )
                repo_id = cursor.fetchone()[1]

                cursor.execute(
                    insert_snapshot,
                    processed_data
                )
                snapshot_id = cursor.fetchone()[0]

                print(f"Data inserted as a new row, with snapshot_id {snapshot_id}")
        return True

    except Exception as e:
        print(f"Couldn't load data to the database, details: {e}")
        
        return False

if __name__ == "__main__":
