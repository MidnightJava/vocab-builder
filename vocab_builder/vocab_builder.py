#!/bin/env python3

from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=f"{os.environ['HOME']}{os.path.sep}/.env")

import json
from os.path import exists, sep
import sys
import readchar
import csv
from collections import defaultdict
from datetime import date
from random import randint
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ms_translater_client import MSTranslatorClient

DATA_DIR = "data"

class VocabBuilder():

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
        self.vocab_filename = f"{DATA_DIR}{sep}{self.to_lang}_{self.from_lang}_vocab"
        self.client = MSTranslatorClient()
        if not self.no_word_lookup: 
            langs = self.client.get_languages()
            self.langs = langs if langs else {}
            self.check_langs()
        else:
            self.langs = {}
            self.to_langname = self.to_lang
            self.from_langname = self.from_lang
            
        self.initialize_vocab()
        
        if self.cli_launch:
            if self.pr_avail_langs:
                print("Available languages for translation")
                print("Code\tName")
                # print(json.dumps(self.langs, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
                for lang in self.get_avail_langs():
                    print(lang)
                
            elif self.pr_word_cnt:
                vocab = self.get_vocab()
                print(f"{len(vocab)} {self.to_langname} TO {self.from_langname} words saved")
            elif self.import_vocab:
                self.import_vocab_file(self.import_vocab)
                self.export_vocab()
            elif self.add_vocab:
                self.run_add_vocab(self.no_trans_check)
                self.export_vocab()
            elif self.test_vocab:
                self.run_test_vocab()
            
    def get_avail_langs(self):
        return self.client.get_languages()
    
    def run_test_vocab(self):        
        done = False
        lang1 = {"id": self.from_lang, "name": self.from_langname}
        lang2 = {"id": self.to_lang, "name": self.to_langname}
        if self.word_order == "from-to":
            [lang1, lang2] = [lang2, lang1]
        self.selected_words = self.select_words()
        while not done:
            word = self.next_word()
            if word is None:
                print("No more words to review for this round")
                done = True
                continue
            ans = input(f"\n{lang2['name']} word: {word}\n\nPress Enter to see translation, any other key plus Enter to quit")
            if len(ans):
                done = True
                break
            trans = self.get_saved_translation(word)
            print(f"\n{lang1['name']} Translation: {trans}\n")
            print("Press Enter if you knew the translation, any other key if you did not ")
            c = readchar.readkey()
            if c == '\n':
                self.mark_correct(word if self.word_order == 'to-from' else trans)
                try:
                    self.selected_words.remove(word)
                except:
                    pass
    
    def import_vocab_file(self, filename):
        #Assumes the first column is the TO language and the second column is the FROM language
        with open(filename, mode='r') as file:
            csvFile = csv.reader(file)
            missed_translation = False
            untranslated_words = set()
            translated_words = []
            print(f"{len(file.readlines())} words to import")
            file.seek(0)
            for row in csvFile:
                if len(row) == 1: row.append("")
                if row[0] and not row[1]:
                    if not self.no_word_lookup:
                        row[1] = self.client.translate(self.to_lang, self.from_lang, row[0])
                    if row[1] == row[0]:
                        missed_translation = True
                        untranslated_words.add(row[0])
                    else:
                        translated_words.append((row[0], row[1]))
                elif row[1] and not row[0]:
                    if not self.no_word_lookup:
                        row[0] = self.client.translate(self.from_lang, self.to_lang, row[1])
                    if row[0] == row[1]:
                        missed_translation = True
                        untranslated_words.add(row[1])
                    else:
                        translated_words.append((row[0], row[1]))
                else:
                    translated_words.append((row[0], row[1]))
                    if len(row) > 2:
                        for i in range(2, len(row)):
                            translated_words.append((row[0], row[i]))
            if missed_translation:
                print("The following words were not imported because a translation could not be determined and was not explicitly provided. " +
                      "This error will also occur if the translation is identical to the original word.")
                for w in untranslated_words: print(w)
            
            vocab = self.get_vocab()
            duplicate_words = set()
            duplicate_translation = False
            for w1, w2 in translated_words:
                [w1, w2] = [w1.strip(), w2.strip()]
                if not w1 in vocab:
                    vocab[w1] = {
                        "translations": [w2],
                        "lastCorrect": "",
                        "count": 0
                    }
                else:
                    val = vocab[w1]
                    if w2 in val["translations"]:
                        duplicate_translation = True
                        duplicate_words.add(w2)
                    else:
                        val["translations"].append(w2)
            if duplicate_translation:
                print("The following words were not imported because a translation entry already exists")
                for w in duplicate_words: print(w)
            self.set_vocab(vocab)
            print(f"{len(translated_words) - len(duplicate_words)} words imnported")
                
                
    
    def select_words(self):
        def select(entry):
            k,v = entry
            if k == 'meta':
                return False
            if v["count"] <= self.min_correct:
                return True
            if not len(v["min_age"]):
                return True
            last_correct = date.fromisoformat(v['lastCorrect'])
            delta_days = (date.today() - last_correct).days
            return delta_days >= int(self.min_age)
        
        vocab = dict(filter(select, self.get_vocab().items()))
        if self.word_order == "from-to":
                vals = list(map( lambda v: v['translations'], filter(lambda k: k != "meta", vocab.values())))
                #Now flatten it
                return [item for sublist in vals for item in sublist]
        else:
            return list(filter(lambda k: k != "meta", vocab.keys()))
    
    def next_word(self):
        if not len(self.selected_words):
            return None
        idx = randint(0, len(self.selected_words) - 1)
        return self.selected_words[idx]
    
    def mark_correct(self, word):
        vocab = self.get_vocab()
        entry = vocab[word]
        entry['count']+= 1
        entry['lastCorrect'] = date.today().isoformat()
        self.set_vocab(vocab)
          
    def run_add_vocab(self, no_trans_check):
        done = False
        new_words = []
        lang1 = {"id": self.to_lang, "name": self.to_langname}
        lang2 = {"id": self.from_lang, "name": self.from_langname}
        if self.word_order == "from-to":
            [lang1, lang2] = [lang2, lang1]
        while not done:
            w_1 = input(f"{lang1['name']} word (Enter to quit): ").lower()
            if not len(w_1):
                done = True
            else:
                if len(self.langs) == 0:
                    w_2 = input(f"{lang2['name']} word: ").lower()
                    if self.word_order == "from-to":
                         new_words.append((w_1, w_2))
                    else:
                        new_words.append((w_2, w_1))
                else:
                    w_2 = self.client.translate(lang1["id"], lang2["id"], w_1).lower()
                    if w_2 and w_2 != w_1:
                        if not no_trans_check:
                            ans = input(f"translation: {w_2}   Enter to accept, or type a custom translation: ")
                            if len(ans): w_2 = ans
                        else:
                            print(f"translation: {w_2}")
                        if self.word_order == "from-to":
                             new_words.append((w_1, w_2))
                        else:     
                            new_words.append((w_2, w_1))
                    else:
                        ans = input("No translation found. Enter to skip, or type a custom translation: ")
                        if len(ans): new_words.append((ans, w_1))
        self.merge_vocab(new_words)
        
    def get_vocab(self, l1=None, l2=None):
        if l1 == None or l2 == None:
            vocab_file = self.vocab_filename
        else:
            vocab_file = f"{DATA_DIR}{sep}{l2}_{l1}_vocab"
        if exists(vocab_file):
            with open(vocab_file, 'r') as f:
                contents = f.read()
                return  json.loads(contents)
        else:
            return {}
        
    def get_saved_translation(self, word):
        vocab = self.get_vocab()
        if self.word_order == "to-from":
            return ",".join(vocab[word]["translations"])
        else:
            trans = ""
            for k, v in vocab.items():
                if k == "meta": continue
                for w in v["translations"]:
                    if w == word:
                        trans = k
                        break
            return trans 
        
    def set_vocab(self, vocab):
        with open(self.vocab_filename, 'w') as f:
            f.write(json.dumps(vocab))
            
    def merge_vocab(self, new_words):
        vocab = self.get_vocab()
        for w_from, w_to in new_words:
            if not w_to in vocab:
                vocab[w_to] = {"translations": [w_from], "lastCorrect": "", "count": 0}
            else:
                trans = vocab[w_to]["translations"]
                if not w_from in trans:
                    trans.append(w_from)
        self.set_vocab(vocab)
    
    def initialize_vocab(self):
        if not exists(self.vocab_filename):
            with open(self.vocab_filename, 'a') as f:
                f.write(json.dumps({"meta": {
                    "val_lang": f"{self.from_lang}",
                    "val_langname": f"{self.from_langname}",
                    "key_lang": f"{self.to_lang}",
                    "key_langname": f"{self.to_langname}"
                }}))
                
    def export_vocab(self):
        vocab = self.get_vocab()
        with open(f"{DATA_DIR}{sep}{self.to_lang}_{self.from_lang}_exported_words", "w") as file:
            csvwriter = csv.writer(file,  quoting=csv.QUOTE_NONE)
            for k,v in vocab.items():
                if k == "meta": continue
                row = [k]
                for w in v["translations"]:
                    row.append(w)
                csvwriter.writerow(row)
                
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
    mode_group.add_argument("-tv", "--test-vocab", action="store_true",
                         help="Present flashcard-style tests for stored vocabulary words")
    mode_group.add_argument("-pwc", "--pr-word-cnt", action="store_true",
                         help="Print the number of stored words and exit")
    mode_group.add_argument("-pal", "--pr-avail-langs", action="store_true",
                         help="Print the available languages and exit.  Used only if the --no-word-lookup option is not selected.")
    mode_group.add_argument("-iv", "--import-vocab", type=str,
                         help="Path to csv file with vocabulary words to be imported")
    mode_group.add_argument("-h", "--help", action="help",
                         help="Show this help message and exit")
    
    addGroup = parser.add_argument_group(title = "Add Vocabulary Options")
    addGroup.add_argument("-nl", "--no-word-lookup", action="store_true",
                         help="Manually specify the translation of words instead of relying on the external translation service")
    addGroup.add_argument("-ntc", "--no-trans-check", action="store_true",
                         help="When using the external translation service, accept the translation without prompting for confirmation or override")
    
    testGroup = parser.add_argument_group(title = "Test Vocabulary Options")
    testGroup.add_argument("-mc", "--min-correct", type=int, default=5,
                         help="Prioritize testing of words that have not been answered correctly this many times in a row")
    testGroup.add_argument("-ma", "--min-age", type=int, default=15,
                         help="Prioritize testing of words that have not been tested for at least this many days")
    
    
    othGroup = parser.add_argument_group(title = "Other Options")
    othGroup.add_argument("-fl", "--from-lang", default="en",
                         help="Name of the language you know. You must use one of the ID codes displayed with the --pal option unless--no-word-lookup option is selected")
    othGroup.add_argument("-tl", "--to-lang", default="it",
                         help="Name of the language you're learning. You must use one of the ID codes displayed with the --pal option unless--no-word-lookup option is selected")
    othGroup.add_argument("-wo", "--word-order", default="to-from", metavar="to-from | from-to",
                         help="Present words in the language you're learning (default) or the language you already know")
    
    args = parser.parse_args()
    VocabBuilder(add_vocab = args.add_vocab,
                 no_trans_check = args.no_trans_check,
                 test_vocab = args.test_vocab,
                 import_vocab = args.import_vocab,
                 no_word_lookup = args.no_word_lookup,
                 min_correct = args.min_correct,
                 min_age = args.min_age,
                 word_order=args.word_order,
                 pr_word_cnt = args.pr_word_cnt,
                 pr_avail_langs = args.pr_avail_langs,
                 from_lang = args.from_lang,
                 to_lang = args.to_lang,
                 cli_launch = True)
    
