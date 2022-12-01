# import requests

# API_KEY = "6d61800c92mshbc418b3cb563f33p13d57cjsnab299adbc702"
# url = "https://microsoft-translator-text.p.rapidapi.com/languages"
# querystring = {'api-version':'3.0'}
# headers = {
#     'X-RapidAPI-Key': API_KEY,
#     'X-RapidAPI-Host': 'microsoft-translator-text.p.rapidapi.com',
#     'accept': 'application/json',
#     'accept-encoding': 'gzip, deflate, br',
#     'usequerystring': 'true'
# }
# resp = requests.request('GET', url, params=querystring, headers=headers)
# print(resp.encoding)
# d = resp.content.decode('utf-8')
# print(d)
# print(resp.text)


import http.client
import json

conn = http.client.HTTPSConnection("microsoft-translator-text.p.rapidapi.com")

headers = {
    'X-RapidAPI-Key': "6d61800c92mshbc418b3cb563f33p13d57cjsnab299adbc702",
    'X-RapidAPI-Host': "microsoft-translator-text.p.rapidapi.com",
    }

conn.request("GET", "/languages?api-version=3.0", headers=headers)

res = conn.getresponse()
data = json.loads(res.read().decode('utf-8'))

print(data['translation'])