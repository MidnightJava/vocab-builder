#!/bin/env python3

from flask import Flask, json
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
    return str(langs)
    
    
if __name__ == "__main__":
    start_server()