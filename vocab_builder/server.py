#!/bin/env python3

import flask
from flask import Flask, json, jsonify, make_response, after_this_request
from vocab_builder import VocabBuilder

api = Flask(__name__)

def start_server():
    api.run()


app = VocabBuilder(no_trans_check = False,
            no_word_lookup = False,
            min_correct = 5,
            min_age = 15,
            word_order= "from-to",
            from_lang = "en",
            to_lang = "it",
            cli_launch = False)

@api.route('/languages', methods=['GET'])
def get_languages():
    langs = app.get_avail_langs()
    # print(json.dumps(langs))
    # resp = flask.Response(jsonify(langs))
    # resp.headers['Access-Control-Allow-Origin'] = '*'
    # return resp
    @after_this_request
    def add_header(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp
    return jsonify(langs)
    
    
if __name__ == "__main__":
    start_server()