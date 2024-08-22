#!/bin/env python3

from flask import Flask, json, jsonify, request, after_this_request
from vocab_builder import VocabBuilder
import os, signal
import sys
import logging
from threading import Timer
LOGGING_DIR = "/var/log/vocab-builder"
os.makedirs(LOGGING_DIR, exist_ok=True)
LOG_FILE_NAME = os.path.join(LOGGING_DIR, "vb.log")
DEFAULT_LISTEN_PORT = 5100

os.chdir("/")

port = os.environ.get("SERVER_PORT", DEFAULT_LISTEN_PORT)

logger = logging.getLogger(__name__)
FileOutputHandler = logging.FileHandler(os.path.join(LOGGING_DIR, LOG_FILE_NAME))

logger.addHandler(FileOutputHandler)
logger.setLevel(logging.INFO)
logger.info("Server logging initialized")

api = Flask(__name__)
app = VocabBuilder()

def shutdown_server():
    logging.info('Shutting down server...')
    os.kill(os.getpid(), signal.SIGINT)

def start_server():
    logging.info(f"Starting server on port {port}")
    try:
      api.run(host='0.0.0.0', port=int(port))
    except Exception as e:
      logging.error(e)

class NotInitializedException(Exception):
    def __init__(self):
        self.code = 400
        self.msg = "Not Initialized"
        
class BadRequestException(Exception):
    def __init__(self, msg):
        self.code = 400
        self.msg = msg

@api.errorhandler(NotInitializedException)
@api.errorhandler(BadRequestException)
def error_handler(err):
    print(err.msg)
    return jsonify({"Error": err.msg}), 200

@api.route('/init', methods=['GET'])
def init():
    global app
    try:
        lang1, lang2 = parse_request_params(request, 'from_lang', 'to_lang')
    except BadRequestException as exc:
        lang1, lang2 = "", ""
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    try:
        app.initialize(no_trans_check = False,
          no_word_lookup = False,
          min_correct = int(request.args['min_correct']) or 5,
          min_age = int(request.args['min_age']),
          part_of_speech = request.args['part_of_speech'],
          word_order= "from-to",
          from_lang = lang1,
          to_lang = lang2,
          cli_launch = False)
    except Exception as exc:
        logger.error(f"Init exception {exc}")
        raise BadRequestException(exc.args[0])
    
    return jsonify({"Result": "Initialized"})

@api.route('/kill', methods=['POST', 'OPTIONS', 'GET'])
def kill():
  
  if request.method == "OPTIONS" or request.method == 'GET':
    return "OK", 200
  
  logging.warning('Kill server request')
  shutdown_server()
  return jsonify({"status": "OK"}), 200


@api.route('/alive', methods=['GET'])
def is_alive():
  global app
    
  @after_this_request
  def add_header(resp):
      resp.headers["Access-Control-Allow-Origin"] = "*"
      resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
      return resp
  
  return jsonify({"status": "OK"}), 200

@api.route('/apilookup/set', methods=['POST', 'OPTIONS', 'GET'])
def set_api_lookup():
  global app
    
  @after_this_request
  def add_header(resp):
      resp.headers["Access-Control-Allow-Origin"] = "*"
      resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
      return resp
  
  if request.method == "OPTIONS" or request.method == 'GET':
      return "OK", 200

  try:
      body = request.get_json(force=True)
  except BadRequestException as exc:
      raise exc
  
  
  if not app.initialized:
      raise NotInitializedException
  
  res = app.set_api_lookup(body['api_lookup'])
  
  return jsonify({"result": res}), 200

def parse_request_params(request, *params):
    for param in params:
        if param not in request.args:
            raise BadRequestException(msg = f"Missing {param} parameter")
    
    return [request.args[param] for param in params]
  
@api.route('/api_key/set', methods=['POST', 'OPTIONS', 'GET'])
def set_api_key():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200

    try:
        body = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    res = app.set_api_key(body['api_key'])
    
    return jsonify({"result": res if res == body['api_key'] else None}), 200

@api.route('/api_key', methods=['GET'])
def api_key():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException
    
    res = app.get_api_key()
    return jsonify({"result": res}), 200
    
@api.route('/languages/get', methods=['GET'])
def get_languages():
    # logger.info("GET LANGUAGES")
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    langs = app.get_avail_langs()
    return jsonify(langs)
    
@api.route('/vocab/get_all', methods=['GET'])
def get_vocab():
    global app
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException
    vocab = app.get_vocab()
    return jsonify(vocab), 200

@api.route('/languages/get_defaults', methods=['GET'])
def get_default_langs():
    global app
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException
    default_langs = app.get_default_langs()
    return jsonify(default_langs), 200

@api.route('/partsofspeech/get', methods=['GET'])
def get_parts_of_speech():
    # logger.info(f"GET PARTS OF SPEECH ENDPOINT")
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    # logger.info(f"GET PARTS OF SPEECH GET PARTS")
    parts = app.get_parts_of_speech()
    # logger.info(f"GET PARTS OF SPEECH GOT PARTS")
    return jsonify(parts)

@api.route('/partsofspeech/set', methods=['POST', 'OPTIONS', 'GET'])
def set_parts_of_speech():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        jsonContent = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    res = app.set_parts_of_speech(jsonContent['partsOfSpeech'])
    if res:
      return jsonify({"Result": "OK"}),200
    else:
      return jsonify({"Result": "ERROR"}),200
        

@api.route('/vocab/translate', methods=['GET'])
def translate():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException
    
    try:
        word, from_lang, to_lang = parse_request_params(request, 'word', 'from_lang', 'to_lang')
    except BadRequestException as exc:
        raise exc
    
    res = app.translate(word, from_lang, to_lang)
    return jsonify({"result": res}), 200

@api.route('/vocab/select_words', methods=['GET'])
def select_words():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException
    
    count = app.select_words()
    print(f"{count} WORDS SELECTED")
    return jsonify({"Result": count}), 200

@api.route('/vocab/next_word', methods=['GET'])
def next_word():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if not app.initialized:
        raise NotInitializedException

    
    res = app.next_word()
    return jsonify(res), 200
    
@api.route('/vocab/delete_entry', methods=['POST', 'OPTIONS', 'GET'])
def delete_vocab_entry():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    global app
    try:
        entry = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    # word_entry = json.loads(json_str)
    print(entry)
    deleted = []
    try:
        if not isinstance(entry, list):
            entry = [entry]
        for item in entry:
            app.delete_entry(item['key'])
            deleted.append(item['key'])
    except Exception as e:
        return jsonify({"error": str(e)}),400
    return jsonify({"deleted": deleted}), 200

@api.route('/vocab/add_entry', methods=['POST', 'OPTIONS', 'GET'])
def add_vocab_entry():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        word_entry = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    # word_entry = json.loads(json_str)
    app.merge_vocab([(word_entry['from'], word_entry['to'], word_entry['part_of_speech'])], force=True)
    
    return jsonify({}),200
  
@api.route('/vocab/update_entry', methods=['POST', 'OPTIONS', 'GET'])
def update_vocab_entry():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        word_entry = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    # word_entry = json.loads(json_str)
    app.merge_vocab([(word_entry['from'], word_entry['to'], word_entry['part_of_speech'])], force=True, update=True)
    
    return jsonify({}),200


@api.route('/vocab/mark_correct', methods=['POST', 'OPTIONS', 'GET'])
def vocab_mark_correct():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        entry = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    app.mark_correct(entry['text'])
    print(f"{entry['text']} is correct")
    return jsonify({}),200
    #TODO remove word from selection in app.mark_correct (and no longer in app.run_test_vocab) But look
    #at word-order when removing, to know which language the removed word is given in. DONE??
    
@api.route('/languages/set_defaults', methods=['POST', 'OPTIONS', 'GET'])
def set_default_langs():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        default_langs = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    # word_entry = json.loads(json_str)
    app.set_default_langs(frm=default_langs["from"], to=default_langs["to"])
    
    return jsonify({}),200

@api.route('/vocab/set_word_order', methods=['POST', 'OPTIONS', 'GET'])
def set_word_order():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    try:
        word_order = request.get_json(force=True)
    except BadRequestException as exc:
        raise exc
    
    
    if not app.initialized:
        raise NotInitializedException
    
    app.word_order = word_order['value']
    app.select_words()
    
    return jsonify({}),200

@api.route('/vocab/import_csv', methods=['GET', 'OPTIONS', 'POST'])
def import_csv():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    if not app.initialized:
        raise NotInitializedException
    
    if request.method == 'POST':
        if 'file' not in request.files:
          print('Import CSV vocab: No file found in request')
        file = request.files['file']
        if file.filename == '':
            print('Import CSV vocab: No file name specified')
        if file:
            app.import_vocab_csv(file=file.read())
    return jsonify({"Result": "OK"}),200

@api.route('/vocab/export_csv', methods=['GET'])
def export_csv():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    global app
    if not app.initialized:
        raise NotInitializedException
    
    data = app.export_vocab_csv()
    return jsonify({"file": data}),200

@api.route('/vocab/import_json', methods=['GET', 'OPTIONS', 'POST'])
def import_json():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    
    if request.method == "OPTIONS" or request.method == 'GET':
        return "OK", 200
    
    global app
    if not app.initialized:
        raise NotInitializedException
    
    if request.method == 'POST':
        if 'file' not in request.files:
          print('Import JSON vocab: No file found in request')
        file = request.files['file']
        if file.filename == '':
            print('Import JSON vocabn: No file name specified')
        if file:
            app.import_vocab_json(file=file)
    return jsonify({"Result": "OK"}),200
    
@api.route('/vocab/export_json', methods=['GET'])
def export_json():
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    global app
    if not app.initialized:
        raise NotInitializedException
    
    data = app.export_vocab_json()
    return jsonify({"file": data}),200
    
if __name__ == "__main__":
    start_server()