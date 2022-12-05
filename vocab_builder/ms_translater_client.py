import requests
import os
import re
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
        try:
            request = requests.get(url, params=params, headers=headers, timeout=5.0)
            response = request.json()
            return response['translation']
        except:
            return None

    def detect_language(self, text):
        path = '/detect?api-version=3.0'
        url = endpoint + path
        body = [{
            "text": "'" + text + "'"
        }]
        try:
            request = requests.post(url, headers=headers, json=body, timeout=5.0)
            response = request.json()
            # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
            return response
        except:
            return None
    
    def translate(self, from_lang, to_lang, text):
        path = '/translate?api-version=3.0'
        url = endpoint + path
        params = {
            "from": from_lang,
            "to": to_lang
        }
        body = [{
            "text": "'" + text + "'"
        }]
        try:
            request = requests.post(url, params=params, headers=headers, json=body, timeout=5.0)
            response = request.json()
            # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
            text = response[0]["translations"][0]["text"]
            return re.sub("^'", "", re.sub("'$", "", text))
        except:
            return None

"""
resp.text when not subscribed
{"message":"You are not subscribed to this API."}
{"message":"You are not subscribed to this API."}
"""
