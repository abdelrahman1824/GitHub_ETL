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

def get_stored_repos(cursor):
    select_repos = """ 
    SELECT github_repo_id, repo_name, owner_id
    FROM analytics.repositories;
    """
    cursor.execute(
        select_repos
    ) 

    stored_repos = {
        row[0]:
        {
            "repo_name": row[1],
            "owner_id": row[2]
        }
        for row in cursor.fetchall()
    }

    print(f"Stored repos: {stored_repos}")

    return stored_repos

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
    RETURNING repo_id;
    """

    try:
        postgres_connection = create_postgres_connection()

        with postgres_connection as connection:
            with connection.cursor() as cursor:

                #The repo details of the snapshot
                snapshot_repo = {
                    "snapshot_repo_id": processed_data.get("repo_id")
                }

                #The repo id for comparing stored repos
                snapshot_repo_id = snapshot_repo.get("snapshot_repo_id")
                print(snapshot_repo_id)

                stored_repos = get_stored_repos(cursor)
                
                if not stored_repos:
                    print("New repository!")
                    cursor.execute(
                            insert_repository,
                            processed_data
                        )
                    repo_id = cursor.fetchone()[0]
                
                else:
                    if snapshot_repo_id not in stored_repos:
                        print("New repository!")  
                        cursor.execute(
                                insert_repository,
                                processed_data
                            )
                        repo_id = cursor.fetchone()[0]

                    else:
                        get_stored_repo_id = """ 
                        SELECT repo_id 
                        FROM analytics.repositories
                        WHERE github_repo_id = %(snapshot_repo_id)s
                        """
                    
                        cursor.execute(
                            get_stored_repo_id,
                            snapshot_repo
                        )
                        repo_id = cursor.fetchone()[0]
                        print(repo_id)

                insert_snapshot = """
                INSERT INTO analytics.repository_snapshots
                (
                stargazers_count,
                forks_count,
                open_issues,
                subscribers_count,
                pushed_at,
                updated_at,
                extracted_at,
                s3_object,
                repo_id
                )
                VALUES
                (
                %(stargazers_count)s,
                %(forks_count)s,
                %(open_issues)s,
                %(subscribers_count)s,
                %(pushed_at)s,
                %(updated_at)s,
                %(extracted_at)s,
                %(s3_key)s,
                %(repo_id)s
                )
                RETURNING snapshot_id;
                """
                
                snapshot_parameters = processed_data.copy()
                snapshot_parameters["repo_id"] = repo_id

                cursor.execute(
                    insert_snapshot,
                    snapshot_parameters
                )
                snapshot_id = cursor.fetchone()[0]

                print(f"Data inserted as a new row, with snapshot_id {snapshot_id}")

        return True

    except Exception as e:
        print(f"Couldn't load data to the database, details: {e}")
        
        return False

if __name__ == "__main__":
    data = {
            "repo_id":55,
            "name": "scikit-learn",
            "owner_id":4356,
            "stargazers_count":56757,
            "forks_count":675785,
            "open_issues":56,
            "subscribers_count":6567,
            "pushed_at":'2015-11-07 03:19:20.000 +0200',
            "created_at":'2015-11-07 03:19:20.000 +0200',
            "updated_at":'2015-11-07 03:19:20.000 +0200',
            "extracted_at":'2015-11-07 03:19:20.000 +0200',
            "s3_key":"ghfgh" 
            }

    load_snapshot(data)