#!/bin/env python3

# TODO
# Add button to save default langs
# Filter meta entry from vocab list
from flask import Flask, json, jsonify, request, after_this_request
from vocab_builder import VocabBuilder

api = Flask(__name__)

def start_server():
    api.run(port=5000)
    
app = None

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
    return err.msg, err.code

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
        app = VocabBuilder(no_trans_check = False,
                no_word_lookup = False,
                min_correct = 5,
                min_age = 15,
                word_order= "from-to",
                from_lang = lang1,
                to_lang = lang2,
                cli_launch = False)
    except Exception as exc:
        raise BadRequestException(exc.args[0])
    
    return jsonify({"Result": "Initialized"})

def parse_request_params(request, *params):
    for param in params:
        if param not in request.args:
            raise BadRequestException(msg = f"Missing {param} parameter")
    
    return [request.args[param] for param in params]
    
@api.route('/languages/get', methods=['GET'])
def get_languages():
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
    
    if app is None:
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
    
    if app is None:
        raise NotInitializedException
    default_langs = app.get_default_langs()
    return jsonify(default_langs), 200

@api.route('/vocab/translate', methods=['GET'])
def translate():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if app is None:
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
    
    if app is None:
        raise NotInitializedException
    
    app.select_words()
    return jsonify({"Result": "Success"}), 200

@api.route('/vocab/next_word', methods=['GET'])
def next_word():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if app is None:
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
    
    
    if app is None:
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
    
    
    if app is None:
        raise NotInitializedException
    
    # word_entry = json.loads(json_str)
    app.merge_vocab([(word_entry['from'], word_entry['to'])], force=True)
    
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
    
    
    if app is None:
        raise NotInitializedException
    
    app.mark_correct(entry['text'])
    print(f"{entry['text']} is correct")
    return jsonify({}),200
    #TODO remove word from selection in app.mark_correct (and no longer in app.run_test_vocab) But look
    #at word-order when removing, to know which language the removed word is given in
    
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
    
    
    if app is None:
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
    
    
    if app is None:
        raise NotInitializedException
    
    app.word_order = word_order['value']
    app.select_words()
    
    return jsonify({}),200
    
    
if __name__ == "__main__":
    start_server()