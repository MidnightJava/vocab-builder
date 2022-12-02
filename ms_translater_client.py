import requests
import os
import json

from translator_client import TranslatorClient
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

class MSTranslatorClient(TranslatorClient):

    def get_languages(self):
        resp = requests.get(url, params=querystring, headers=headers)
        langs = json.loads(resp.text)["translation"]
        return langs

"""
resp.text when not subscribed
{"message":"You are not subscribed to this API."}
{"message":"You are not subscribed to this API."}
"""
