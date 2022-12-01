import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["API_KEY"]
url = "https://microsoft-translator-text.p.rapidapi.com/languages"
querystring = {'api-version':'3.0'}
headers = {
    'X-RapidAPI-Key': API_KEY,
    'X-RapidAPI-Host': 'microsoft-translator-text.p.rapidapi.com',
    'accept-encoding': 'identity'
}
resp = requests.get(url, params=querystring, headers=headers)
langs = json.loads(resp.text)["translation"]
print(langs)


# import http.client
# import json

# conn = http.client.HTTPSConnection("microsoft-translator-text.p.rapidapi.com")

# headers = {
#     'X-RapidAPI-Key': API_KEY,
#     'X-RapidAPI-Host': "microsoft-translator-text.p.rapidapi.com",
#     }

# conn.request("GET", "/languages?api-version=3.0", headers=headers)

# res = conn.getresponse()
# data = json.loads(res.read().decode('utf-8'))

# print(data['translation'])

"""
resp.text when not subscribed
{"message":"You are not subscribed to this API."}
{"message":"You are not subscribed to this API."}
"""
