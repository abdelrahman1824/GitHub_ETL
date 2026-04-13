import requests
from dotenv import load_dotenv
import os
import json

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

token = load_github_token()
headers = build_api_headers(token)
data = fetch_tensorflow_repo(headers)
print(data)