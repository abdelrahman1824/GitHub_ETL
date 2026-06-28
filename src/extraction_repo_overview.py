import requests
from dotenv import load_dotenv
import os
import json
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
    

# ---------- Creating a JSON file to save data ---------- #

def save_to_json_file(data):
    time_stamp = datetime.now().strftime("%Y%m%d_%H%M%S") #Timestamp variable for our file name

    file_name = f"tensorflow_tensorflow_{time_stamp}.json"
    full_file_path = fr"data\raw\{file_name}"

    try:
        os.makedirs(os.path.dirname(full_file_path), exist_ok = True)

        with open(full_file_path, 'w', encoding = 'utf-8') as f:
            json.dump(data, f, indent = 4, ensure_ascii = False)

        print(f"Data saved to {full_file_path} at {time_stamp} sucessfully!")

    except(TypeError, ValueError) as e:
        print(f"Failed to serialize data, Details: {e}")
    
    except OSError as e:
        print(f"File error, Details: {e}")


# ---------- Main Extraction Script ---------- #

token = load_github_token()
headers = build_api_headers(token)
data = fetch_tensorflow_repo(headers)
save_to_json_file(data)