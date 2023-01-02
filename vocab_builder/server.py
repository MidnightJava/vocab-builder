#!/bin/env python3

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
        lang1, lang2 = parse_request_params(request)
    except BadRequestException as exc:
        raise exc
    
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

def parse_request_params(req):
    if not "from_lang" in request.args:
        raise BadRequestException(msg = "Missing from_lang parameter")
    elif not "to_lang" in request.args:
        raise BadRequestException(msg = "Missing to_lang parameter")
    
    return request.args["from_lang"], request.args["to_lang"]
    
@api.route('/languages', methods=['GET'])
def get_languages():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if app is None:
        raise NotInitializedException
    else:
        langs = app.get_avail_langs()
        return jsonify(langs)
    
@api.route('/vocab', methods=['GET'])
def get_vocab():
    global app
    
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    
    if app is None:
        raise NotInitializedException
    vocab = app.get_vocab()
    return jsonify(vocab)
    
    
if __name__ == "__main__":
    start_server()