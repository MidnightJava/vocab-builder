import requests
import os
import re
import sys
import json
import uuid

from translator_client import TranslatorClient

endpoint = "https://api.cognitive.microsofttranslator.com"
location = "eastus"
params = {
    'api-version': '3.0'
}

class MSTranslatorClient(TranslatorClient):
  
  def __init__(self, api_key):
    self.api_key = api_key
  
  def headers(self):
    return  {
      'Ocp-Apim-Subscription-Key': self.api_key,
      'Ocp-Apim-Subscription-Region': location,
      'Content-type': 'application/json',
      'X-ClientTraceId': str(uuid.uuid4())
    }

  def get_languages(self):
      path = '/languages'
      url = endpoint + path
      try:
          request = requests.get(url, params=params, headers=self.headers(), timeout=5.0)
          response = request.json()
          return response['translation']
      except:
          return None

  def get_api_key(self):
    return self.api_key
  
  def set_api_key(self, api_key):
    self.api_key = api_key
    resp = self.detect_language('test')
    if isinstance(resp, list) and len(resp) and resp[0]['isTranslationSupported'] == True:
      self.save_api_key(api_key)
      return api_key
    return None
  
  def save_api_key(self, api_key):
    with open('./.env', 'w') as f:
      f.write(f"export API_KEY={api_key}")
      
  def detect_language(self, text):
      path = '/detect?api-version=3.0'
      url = endpoint + path
      body = [{
          "text": "'" + text + "'"
      }]
      try:
          request = requests.post(url, headers=self.headers(), json=body, timeout=5.0)
          response = request.json()
          # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
          return response
      except Exception as e:
          print(e)
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
          request = requests.post(url, params=params, headers=self.headers(), json=body, timeout=5.0)
          response = request.json()
          # print(json.dumps(response, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
          text = response[0]["translations"][0]["text"]
          return re.sub("^'", "", re.sub("'$", "", text))
      except Exception as e:
          print(repr(e))
          return None
"""
resp.text when not subscribed
{"message":"You are not subscribed to this API."}
"""
