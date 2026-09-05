import os
import requests

token = "REMOVED_TOKEN"
url = f"https://api.apify.com/v2/users/me?token={token}"
response = requests.get(url)
print(response.json())
