#!/bin/env python3

import flask
from flask import Flask, json, jsonify, request, after_this_request, abort
from vocab_builder import VocabBuilder

api = Flask(__name__)

def start_server():
    api.run(port=5000)
    
app = None

class NotInitializedException(Exception):
    def __init__(self):
        self.code = 400
        self.msg = "Not Initialized"

@api.errorhandler(NotInitializedException)
def error_handler(err):
    print(err.msg)
    return err.msg, err.code

@api.route('/init', methods=['GET'])
def init():
    global app
    [l1, l2] = [request.args["from_lang"], request.args["to_lang"]]
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    if app:
         return "Already Initialized"
    else:
        app = VocabBuilder(no_trans_check = False,
                no_word_lookup = False,
                min_correct = 5,
                min_age = 15,
                word_order= "from-to",
                from_lang = l1,
                to_lang = l2,
                cli_launch = False)
        return "Initialized"

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
    [l1, l2] = [request.args["from_lang"], request.args["to_lang"]]
    vocab = app.get_vocab(l1, l2)
    return jsonify(vocab)
    
    
if __name__ == "__main__":
    start_server()