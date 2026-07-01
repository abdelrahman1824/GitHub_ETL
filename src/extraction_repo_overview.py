import requests
from dotenv import load_dotenv
import os
import json
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import logging
from datetime import datetime

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
    except requests.exception.Timeout:
        raise RuntimeError("GitHub API request timeout")
    
    if response.status_code != 200:
        raise ValueError(f"Error: HTTP {response.status_code}, {response.text}")

    print(f"Response is successful, HTTP {response.status_code}")
    data = response.json() #Parse JSON data

    return data
    

# ---------- Creating JSON file to save data ---------- #

def save_to_json_file(data):
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S") #Timestamp variable for our file name
    file_name = fr"tensorflow_tensorflow_{time_stamp}.json"
    file_path = fr"data\raw\{file_name}"

    try:
        os.makedirs(os.path.dirname(file_path), exist_ok = True)

        with open(file_path, 'w', encoding = "utf-8") as f:
            json.dump(data, f, indent = 4, ensure_ascii = False)
        
        print(f"Data saved to {file_name} succesfully!")
    
    except (TypeError, ValueError) as e:
        print(f"Failed to serialize data, details: {e}")
    
    except OSError as e:
        print(f"Failed to find Directory/File, details: {e}")
    
    return file_path
    

# ---------- Uploading data to S3 Bucket ---------- #

def upload_file_to_s3(file_name, Bucket, object_name = None):
    s3_client = boto3.client('s3')

    # If the object name is not determined then replace it with the file name
    if object_name == None:
        object_name = os.path.basename(file_name)

    # Upload file like object to S3
    try:
        s3_client.upload_file(file_name, Bucket, object_name)

    except FileNotFoundError as e:
        print(fr"File was not found in the directory, details: {e}")

    except NoCredentialsError as e:
        print(fr"AWS credentials wasn't found, details: {e}")

    except ClientError as e:
        print(fr"Client connection error, details: {e}")

# ---------- Main Extraction Script ---------- #
def main():
    #Load API Token for GitHub
    token = load_github_token()

    #Configure API Headers
    headers = build_api_headers(token)

    #Request the API URL data
    data = fetch_tensorflow_repo(headers)
    
    #Creat a file for saving data
    file = save_to_json_file(data)

    #Upload the file like Object to S3 Bucket
    Bucket = "my_bucket"
    upload_file_to_s3(file, Bucket)



if __name__ == "__main__":
    main()

