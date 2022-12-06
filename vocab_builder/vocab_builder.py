from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=f"{os.environ['HOME']}{os.path.sep}/.env")

import json
from os.path import exists, sep
import sys
import readchar
from collections import defaultdict
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ms_translater_client import MSTranslatorClient

DATA_DIR = "data"

class VocabBuilder():

    def __init__(self, **kwargs):
        self.from_lang = kwargs["from_lang"]
        self.to_lang = kwargs["to_lang"]
        self.vocab_filename = f"{DATA_DIR}{sep}{kwargs['to_lang']}_{kwargs['from_lang']}_vocab"
        self.initialize_vocab()
        self.client = MSTranslatorClient()
        if not kwargs.get("no_word_lookup"):
            langs = self.client.get_languages()
            self.langs = langs if langs else {}
            self.check_langs()
        else:
            self.langs = {}
            self.to_langname = self.to_lang
            self.from_langname = self.from_lang
        
        if kwargs.get("pr_avail_langs", None):
            print("Available languages for translation")
            print("Code\tName")
            # print(json.dumps(self.langs, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
            for k,v in self.langs.items():
                print(f"{k}\t{v['name']}")
        elif kwargs.get("pr_word_cnt", None):
            vocab = self.get_vocab()
            print(f"{len(vocab)} {self.to_lang} TO {self.from_lang} words saved")
        elif kwargs.get("add_vocab", None):
            self.run_add_vocab(kwargs['no_trans_check'])
        elif kwargs["test_vocab"]:
            done = False
            # self.selected_words = select_words()
            while not done:
                # word = self.next_word()
                word = 'word'
                ans = input(f"\nItalian word: {word} Press Enter to see translation, any other key plus Enter to quit")
                if len(ans):
                    done = True
                    break
                print("\nEnglish Translation: foo\n")
                print("Press Enter if you knew the translation, any other key if you did not ")
                c = readchar.readkey()
                if c == '\n':
                    print("Correct")
                else:
                    print("Missed it")
            
    def run_add_vocab(self, no_trans_check):
        done = False
        new_words = []
        while not done:
            w_to = input(f"{self.to_langname} word (Enter to quit): ").lower()
            if not len(w_to):
                done = True
            else:
                if len(self.langs) == 0:
                    w_from = input(f"{self.from_langname} word: ").lower()
                    new_words.append((w_from, w_to))
                else:
                    w_from = self.client.translate(self.to_lang, self.from_lang, w_to).lower()
                    if w_from and w_from != w_to:
                        if not no_trans_check:
                            ans = input(f"translation: {w_from}   Enter to accept, or type a custom translation: ")
                            if len(ans): w_from = ans
                        else:
                            print(f"translation: {w_from}")
                        new_words.append((w_from, w_to))
                    else:
                        ans = input("No translation found. Enter to skip, or type a custom translation: ")
                        if len(ans): new_words.append((ans, w_to))
        self.merge_vocab(new_words)
        
    def get_vocab(self):
        with open(self.vocab_filename, 'r') as f:
            contents = f.read()
            return  defaultdict(list, json.loads(contents))
        
    def set_vocab(self, vocab):
        with open(self.vocab_filename, 'w') as f:
            f.write(json.dumps(vocab))
            
    def merge_vocab(self, new_words):
        vocab = self.get_vocab()
        for w_from, w_to in new_words:
           vocab[w_to] = {"text": w_from, "lastCorrect": "", "count": 0}
        self.set_vocab(vocab)
    
    def initialize_vocab(self):
        if not exists(self.vocab_filename):
            with open(self.vocab_filename, 'a') as f:
                f.write(json.dumps({}))
                
    def check_langs(self):
        found_from = found_to = False
        for k,v in self.langs.items():
            if k == self.from_lang:
                found_from = True
                self.from_langname = v["name"]
            elif k == self.to_lang:
                found_to = True
                self.to_langname = v["name"]
            if found_from and found_to: break
        if not found_from or not found_to:
            missing = (self.from_lang if not found_from else "") + (f" {self.to_lang}" if not found_to else "")
            print(f"One or both anguages specified are not available: {missing}")
            sys.exit(0)

if __name__ == "__main__":
    parser = ArgumentParser(prog="Vocab Builder", add_help=False,
                            description="A vocabulary practice tool for learning a foreign language",
                            formatter_class=ArgumentDefaultsHelpFormatter)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-av", "--add-vocab", action="store_true",
                        help="Prompt repeatedly for new vocabulary words to be stored")
    mode_group.add_argument("-tv", "--test-vocab", action="store_false",
                         help="Present flashcard-style tests for stored vocabulary words")
    mode_group.add_argument("-pwc", "--pr-word-cnt", action="store_true",
                         help="Print the number of stored words and exit")
    mode_group.add_argument("-pal", "--pr-avail-langs", action="store_true",
                         help="Print the available languages and exit.  Used only if the --no-word-lookup option is not selected.")
    mode_group.add_argument("-h", "--help", action="help",
                         help="Show this help message and exit")
    
    addGroup = parser.add_argument_group(title = "Add Vocabulary Options")
    addGroup.add_argument("-nl", "--no-word-lookup", action="store_true",
                         help="Give the translation of words instead of relying on an external translation service")
    addGroup.add_argument("-ntc", "--no-trans-check", action="store_true",
                         help="When using the -nl option, accept the translation without prompting for confirmation or override")
    
    testGroup = parser.add_argument_group(title = "Test Vocabulary Options")
    testGroup.add_argument("-mc", "--min-correct", type=int, default=5,
                         help="Prioritize testing of words that have not been answered correctly this many times in a row")
    testGroup.add_argument("-ma", "--min-age", type=int, default=15,
                         help="Prioritize testing of words that have not been tested for at least this many days")
    testGroup.add_argument("-to", "--test-order", default="to-from", metavar="to-from | from-to",
                         help="Present words in the language you're learning (default) or the language you already know")
    
    othGroup = parser.add_argument_group(title = "Other Options")
    othGroup.add_argument("-fl", "--from-lang", default="en",
                         help="Name of the language you know. You must use one of the ID codes displayed with the --pal option unless--no-word-lookup option is selected")
    othGroup.add_argument("-tl", "--to-lang", default="it",
                         help="Name of the language you're learning. You must use one of the ID codes displayed with the --pal option unless--no-word-lookup option is selected")
    args = parser.parse_args()
    VocabBuilder(add_vocab = args.add_vocab,
                 no_trans_check = args.no_trans_check,
                 test_vocab = args.test_vocab,
                 no_word_lookup = args.no_word_lookup,
                 min_correct = args.min_correct,
                 min_age = args.min_age,
                 test_order=args.test_order,
                 pr_word_cnt = args.pr_word_cnt,
                 pr_avail_langs = args.pr_avail_langs,
                 from_lang = args.from_lang,
                 to_lang = args.to_lang)