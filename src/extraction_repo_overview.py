import requests
from dotenv import load_dotenv
import os

#PAT (Personal Access Token) validation
load_dotenv()
token = os.getenv("GITHUB_TOKEN")

if not token:
    raise ValueError("GITHUB_TOKEN not found in environmental variables")
else:
    print("GUTHUB_TOKEN is found!")

#Building an API request authentication
url = "https://api.github.com/repos/tensorflow/tensorflow"


headers = {'Authorization': f"bearer {token}", #Authorization head for PAT
           'Accept': 'application/json'} #Accept token for response specification

response = requests.get(url, headers = headers)

#Error handling
if response.status_code != 200:
    raise ValueError(f"Error: HTTP {response.status_code}, {response.text}")
else:
    print(f"Response is successful, HTTP {response.status_code}")
    data = response.json() #Parse JSON data

print(data)


