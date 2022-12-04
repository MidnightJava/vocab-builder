import requests
import os
import sys
import json
import uuid

from translator_client import TranslatorClient

API_KEY = os.getenv("API_KEY", None)
if API_KEY is None:
    print("You must specify an API key in the file .env")
    sys.exit(0)
endpoint = "https://api.cognitive.microsofttranslator.com"
location = "eastus"
params = {
    'api-version': '3.0'
}
headers = {
    'Ocp-Apim-Subscription-Key': API_KEY,
    'Ocp-Apim-Subscription-Region': location,
    'Content-type': 'application/json',
    'X-ClientTraceId': str(uuid.uuid4())
}

class MSTranslatorClient(TranslatorClient):

    def get_languages(self):
        path = '/languages'
        url = endpoint + path
        request = requests.get(url, params=params, headers=headers)
        response = request.json()
        return response['translation']

    def detect_language(self, text):
        path = '/detect?api-version=3.0'
        url = endpoint + path
        body = [{
            "text": "'" + text + "'"
        }]
        request = requests.post(url, headers=headers, json=body)
        response = request.json()
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        return response
    
    def translate(self, text):
        path = '/translate?api-version=3.0'
        url = endpoint + path
        params = {
            "from": "it",
            "to": "en"
        }
        body = [{
            "text": "'" + text + "'"
        }]
        request = requests.post(url, params=params, headers=headers, json=body)
        response = request.json()
        print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
        return response

"""
resp.text when not subscribed
{"message":"You are not subscribed to this API."}
{"message":"You are not subscribed to this API."}
"""
