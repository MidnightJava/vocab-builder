#!/bin/env python3

from dotenv import load_dotenv
import os
from os import listdir
from os.path import isfile, exists, sep, join
import shutil
load_dotenv()

import json
import platform
from os import path
from pathlib import Path
import shutil
import sys, errno
# import readchar
import csv
from datetime import date
from random import randint
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ms_translater_client import MSTranslatorClient
from contextlib import suppress
import io
import logging
from logging.config import dictConfig

home_dir_var_name = "HOMEPATH" if platform.system() == "Windows" else "HOME"

VB_DIR = "vocab_builder"
LOGGING_DIR = os.environ.get("VB_LOGGING_DIR", None) or \
  os.path.join(os.getenv(home_dir_var_name), VB_DIR, "logs")

#In pyinstaller, exist_ok will be ignored
try:
  Path(LOGGING_DIR).mkdir(parents=True, exist_ok=True)
except OSError as exception:
  if exception.errno != errno.EEXIST:
      raise
LOG_FILE_NAME = os.path.join(LOGGING_DIR, "vb.log")

from log_config import config
dictConfig(config(LOG_FILE_NAME))

#Determine if we're running as a bundle created by PyInstaller
isBundled =  getattr( sys, 'frozen', False )
if isBundled:
  INITIAL_DATA_DIR =  path.abspath(path.join(sys._MEIPASS, 'initial-data'))
else:
    INITIAL_DATA_DIR =  path.abspath(path.join(path.dirname(__file__), '..', 'initial-data'))
DATA_DIR = os.environ.get("VB_DATA_DIR", None) or \
  os.path.join(os.getenv(home_dir_var_name), VB_DIR, "data")
PARTS_OF_SPEECH_FILE = "parts_of_speech.json"
API_KEY_FILE_NAME = "api_key"

class VocabBuilder():
  
    def __init__(self):
      self.initialized = False
      self.client = MSTranslatorClient(os.path.join(DATA_DIR, API_KEY_FILE_NAME))
      current_dir = os.getcwd()
      logging.info(f"CWD: {current_dir}")
      logging.info(f"Data Dir: {DATA_DIR}")
      logging.info(f"SERVER_PORT: {os.environ.get('SERVER_PORT', None)}")

    def initialize(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)
        try:
          if not self.data_files_exist():
            self.copy_initial_data()
        except Exception as exception:
          logging.error(f"Failed to cerate initial data files. {exception}")
        self.vocab_filename = f"{DATA_DIR}{sep}{self.to_lang}_{self.from_lang}_vocab"
        self.vocab_filename_json = f"{self.vocab_filename}.json"
        self.vocab_filename_csv = f"{self.vocab_filename}.csv"
        if not self.no_word_lookup: 
            langs = self.client.get_languages()
            self.langs = langs if langs else {}
            self.check_langs()
        else:
            self.langs = {}
            self.to_langname = self.to_lang
            self.from_langname = self.from_lang
            
        if self.lang_attrs_set(): self.initialize_vocab()
                
        if self.cli_launch:
          if self.pr_avail_langs:
              print("Available languages for translation")
              print("Code\t\tName")
              # print(json.dumps(self.langs, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
              for lang in self.get_avail_langs():
                  print(f"{lang}\t\t{self.available_langs[lang]['name']}")
              
          elif self.pr_word_cnt:
              vocab = self.get_vocab()
              print(f"{len(vocab)} {self.to_langname} TO {self.from_langname} words saved")
          elif self.import_vocab:
              self.import_vocab_csv(filename=self.import_vocab)
              self.save_vocab_csv()
          elif self.add_vocab:
              self.run_add_vocab(self.no_trans_check)
              self.save_vocab_csv()
          elif self.test_vocab:
              self.run_test_vocab()
        self.initialized = True
        
    def copy_initial_data(self):
      try:
        #In pyinstaller, exist_ok will be ignored
        os.makedirs(DATA_DIR, exist_ok=True)
      except OSError as exception:
        if exception.errno != errno.EEXIST:
            if exception.errno == errno.ENOTDIR:
                logging.error(f"Unable to create the data directory at {DATA_DIR} because a regular file exists there.")
            raise
      initial_files = [f for f in listdir(INITIAL_DATA_DIR) if isfile(join(INITIAL_DATA_DIR, f))]
      logging.info(f"Copy {len(initial_files)} files from {INITIAL_DATA_DIR} to {DATA_DIR}")
      for file in initial_files:
          if not exists(join(DATA_DIR, file)):
            logging.info(f"Copy {file}")
            shutil.copy(join(INITIAL_DATA_DIR, file), DATA_DIR)
          
    def data_files_exist(self):
      if isfile(DATA_DIR): raise Exception(f"Unable to create the data directory at {DATA_DIR} because a regular file exists there.")
      if not exists(INITIAL_DATA_DIR): return False
      found = True
      for file in listdir(INITIAL_DATA_DIR):
        if not exists(join(DATA_DIR, file)):
          found = False
          break
      return found
    
    def lang_attrs_set(self):
        res = (
          hasattr(self, 'from_lang') and self.from_lang and 
          hasattr(self, 'from_langname') and self.from_langname and
          hasattr(self, 'to_lang') and self.to_lang and
          hasattr(self, 'to_langname') and self.to_langname
        )
        return res

    def get_api_key(self):
      return os.environ.get("API_KEY", self.client.get_api_key())
    
    def set_api_key(self, api_key):
      # Don't save the key to a file if it exists in the environment
      return os.environ.get("API_KEY", self.client.set_api_key(api_key))
    
    def set_api_lookup(self, api_lookup):
        self.no_word_lookup = api_lookup == False
        return "OK"
        
    def get_avail_langs(self):
        if not getattr(self, "available_langs", None):
            self.available_langs = self.client.get_languages()
        return self.available_langs
    
    def translate(self, text, from_lang, to_lang):
        from_lang = self.to_id(from_lang)
        to_lang = self.to_id(to_lang)
        if to_lang:
            return self.client.translate(from_lang, to_lang, text)
        else:
            return text
    
    def to_id(self, lang):
        if lang in self.langs:
            return lang
        for k,v in self.langs.items():
            if lang == v['name'] or lang == v['nativeName']:
                return k
        logging.error(f"Invlaid language: {lang}")
        return None
    
    def kill_app(self):
        sys.exit(0)
    
    """
    CALLED FROM CLI CLIENT OR SERVER
    
    * Get additional vocab words from a csv file, append them to the existing in-memory vocabulary,
        and save the updated vocabulary as a CSV file
    * The input CSV content can be a csv file on the file system (CLI mode) or bytes provided in a
        function call (server mode, providing a file uploaded from the browser)
    """
    def import_vocab_csv(self, filename=None, file=None):
        """
        CSV File structure: Three or more columns
        COl 0: Word in "to" language (can be empty string, but only if Col 2 is not empty)
        Col 1: Part of speech (can be empty string)
        Col 2: Word in "from" language (can be empty string, but only id col 0 is not empty)
        Col 3...n: (optional) Addiitional words in "from" language, i.e. multiple translations of the "to" word
        
        """
        self.backup_vocab_file()
        if file:
            file = io.BytesIO(file)
            print(f"{len(file.readlines())} words to import")
            file.seek(0)
            csvFile = csv.reader(io.TextIOWrapper(file, encoding='utf-8'), quotechar='|',  quoting=csv.QUOTE_NONE)
        elif filename:
            try:
              file = open(filename, 'r')
              print(f"{len(file.readlines())} words to import")
              file.seek(0)
              csvFile = csv.reader(file, quotechar='|',  quoting=csv.QUOTE_NONE)
            except:
                print(f"Import failed. File {filename} does not exist.")
                return
        else:
            print("Import failed. No CSV file was specified.")
            return
        missed_translation = False
        untranslated_words = set()
        translated_words = []
        extra_translations = []
        for row in csvFile:
            if len(row) == 1: row.append("")
            if row[0] and not row[2]:
                if not self.no_word_lookup:
                    row[2] = self.client.translate(self.to_lang, self.from_lang, row[0])
                if row[2] == row[0]:
                    #TODO handle case where word is identical in both languages
                    missed_translation = True
                    untranslated_words.add(row[0])
                else:
                    translated_words.append((row[0], row[1], row[2]))
            elif row[2] and not row[0]:
                if not self.no_word_lookup:
                    row[0] = self.client.translate(self.from_lang, self.to_lang, row[2])
                if row[0] == row[2]:
                    #TODO handle case where word is identical in both languages
                    missed_translation = True
                    untranslated_words.add(row[2])
                else:
                    translated_words.append((row[0], row[1], row[2]))
            else:
                translated_words.append((row[0], row[1], row[2]))
                if len(row) > 3:
                    for i in range(3, len(row)):
                        extra_translations.append((row[0], row[i]))
        if missed_translation:
            print("The following words were not imported because a translation could not be determined and was not explicitly provided. " +
                  "This error will also occur if the translation is identical to the original word.")
            for w in untranslated_words: print(w)
        
        vocab = self.get_vocab()
        duplicate_words = set()
        duplicate_translation = False
        for w1, w2, w3 in translated_words:
            [w1, w2, w3] = [w1.strip(), w2.strip(),  w3.strip()]
            if not w1 in vocab:
                vocab[w1] = {
                    "translations": [w3],
                    "lastCorrect": "",
                    "count": 0,
                    "part": w2
                }
            else:
                val = vocab[w1]
                if w3 in val["translations"]:
                    duplicate_translation = True
                    duplicate_words.add(w3)
                else:
                    val["translations"].append(w3)
                    val["part"] = w2
        if extra_translations:
            for w1, w2 in extra_translations:
                [w1, w2] = [w1.strip(), w2.strip()]
                val = vocab[w1]
                if w2 not in val["translations"]:
                    val["translations"].append(w2)
        if duplicate_translation:
            print("The following words were not imported because a translation entry already exists")
            for w in duplicate_words: print(w)
        self.set_vocab(vocab)
        print(f"{len(translated_words) - len(duplicate_words)} words imnported")
        # Save a csv copy of the vocab json file
        self.save_vocab_csv()
        if file:
            file.close()

    # CALLED FROM SERVER
    # Save file uploaded from browser
    def import_vocab_json(self, file=None):
       if file:
         self.backup_vocab_file()
         file.save(f"{self.vocab_filename_json}")
       else:
           print("Import failed. No JSON file was specified.")
      
    # CALLED FROM SERVER
    # Download saved CSV vocab file to browser
    def export_vocab_csv(self):
        try:
          with open(f"{self.vocab_filename_csv}") as file:
              if file:
                return file.read()
        except:
          print(f"File {self.vocab_filename_csv} does not exist")
          return []
    
    # CALLED FROM SERVER
    # Download saved JSON vocab file to browser
    def export_vocab_json(self):
        try:
          with open(f"{self.vocab_filename_json}") as file:
              if file:
                return file.read()
        except:
          print(f"File {self.vocab_filename_json} does not exist")
          return []
    
  
    def select_words(self):
        def select(entry):
            retval = True
            k,v = entry
            if k == 'meta' or k.strip() == '':
                retval = False
            else:
              if v["count"] <= self.min_correct:
                  retval &= True
              if not len(v["lastCorrect"]):
                  retval &= True
              else:
                last_correct = date.fromisoformat(v['lastCorrect'])
                delta_days = (date.today() - last_correct).days
                retval &= (delta_days >= int(self.min_age))
              if self.part_of_speech != 'Any':
                try:
                  retval &= (v['part'] == self.part_of_speech)
                except:
                    print(str(v))
            return retval
        
        vocab = dict(filter(select, self.get_vocab().items()))
        if self.word_order == "from-to":
                vals = list(map( lambda item: item[1]['translations'], filter(lambda item: item[0] != "meta" and item[0].strip() != '', vocab.items())))
                #Now flatten it
                self.selected_words = [item for sublist in vals for item in sublist]
        else:
            self.selected_words = list(filter(lambda k: k != "meta" and k.strip() != '', vocab.keys()))
        self.selected_count = 0
        return len(self.selected_words)
    
    def next_word(self):
        if not len(self.selected_words):
            return None
        idx = randint(0, len(self.selected_words) - 1)
        self.selected_count+= 1
        return {"text": self.selected_words[idx], "count": self.selected_count, "size": len(self.selected_words)}
        #Word is removed from selected_words in run_test_vocab method, only if user knew the translation

    def get_vocab_entry(self, word):
      vocab = self.get_vocab()
      if self.word_order == 'from-to':
          return list(map(lambda w: w.strip(), word.split(',')))
      for entry in vocab.items():
        if entry[0] == "meta": continue
        for w in entry[1]["translations"]:
            if w == word:
                return entry[0]
      return None
    
    def get_word_in_other_lang(self, word):
        vocab = self.get_vocab()
        translations = []
        if self.word_order == 'to-from':
            for entry in vocab.items():
              if entry[0] == "meta": continue
              for w in entry[1]["translations"]:
                  if w == word:
                      translations.append(entry[0])
                      break
        else:
          entry = vocab.get(word, None)
          if entry: translations = entry['translations']
        return translations
            

    def mark_correct(self, word):
        vocab = self.get_vocab()
        keys = self.get_vocab_entry(word)
        if not isinstance(keys, list): keys = [keys]
        for key in keys:
          entry = vocab.get(key, None)
          if entry is not None:
            entry['count']+= 1
            entry['lastCorrect'] = date.today().isoformat()
            self.set_vocab(vocab)
            with suppress(ValueError):
              # The word to be removed will be given in the oposite language in which
              # the list of selected words is represented.
              words = word.split(',') if isinstance(word, str) else [word]
              word = words[0].strip() if len(words) else ''
              to_remove = self.get_word_in_other_lang(word)
              for word in to_remove:
                self.selected_words.remove(word)
    
    def get_parts_of_speech(self):
      logging.debug("Get parts of speech")
      file = os.path.join(DATA_DIR, PARTS_OF_SPEECH_FILE)
      try:
        with open(file, 'r') as f:
          parts = json.load(f)
          return parts
      except Exception as e:
            logging.error(f"Cannot get parts of speech. File {file} does not exist")
            return []
    
    def set_parts_of_speech(self, parts):
      try:
          s = json.dumps(parts)
      except:
          logging.error(f"Uable to parse parts of speech as json: {str(parts)}")
          return False
      file = os.path.join(DATA_DIR, PARTS_OF_SPEECH_FILE)
      with open(file, 'w+') as f:
          f.write(s)
      return True

    # Save a copy of the vocab json file
    def backup_vocab_file(self):
        shutil.copy2(self.vocab_filename_json, f"{self.vocab_filename_json}.bk")
    
    def delete_entry(self, key):
        vocab = self.get_vocab()
        if key in vocab:
            del vocab[key]
            self.set_vocab(vocab)
        
    def get_vocab(self, l1=None, l2=None):
        if l1 == None or l2 == None:
            vocab_file = self.vocab_filename_json
        else:
            vocab_file = f"{DATA_DIR}{sep}{l2}_{l1}_vocab.json"
        if exists(vocab_file):
            with open(vocab_file, 'r') as f:
                contents = f.read()
                try:
                    contents = json.loads(contents).items()
                    filtered = dict(filter(lambda el: el[0] != "meta", contents))
                except:
                    filtered = {}
                return filtered
        else:
            return {}
        
    def get_saved_translation(self, word):
        vocab = self.get_vocab()
        if self.word_order == "to-from":
            return ",".join(vocab[word]["translations"])
        else:
            trans = ""
            done = False
            for k, v in vocab.items():
                if done: break
                if k == "meta": continue
                for w in v["translations"]:
                    if w == word:
                        trans = k
                        done = True
                        break
            return trans 
    
    # Write vocab entries in memory to json file
    def set_vocab(self, vocab):
        with open(self.vocab_filename_json, 'w+') as f:
            f.write(json.dumps(vocab))
        self.backup_vocab_file()
            
    def merge_vocab(self, new_words, force=False, update=False):
        vocab = self.get_vocab()
        for w_from, w_to, part_of_speech in new_words:
            if isinstance(w_from, str):
                w_from_l = w_from.split(',')
            else:
                w_from_l = w_from
            if w_to in vocab:
                trans = vocab[w_to]["translations"]
                found = False
                for w in w_from_l:
                  if w.strip().lower() in map(lambda x: x.strip().lower(), trans):
                    found = True
                    break
                if not found:
                  trans.append(w_from)
                vocab[w_to]['part'] = part_of_speech
            else:
                if update:
                   vocab = dict(filter(lambda x: x[1]['translations'] != w_from_l, vocab.items()))
                vocab[w_to] = {"translations": w_from_l, "lastCorrect": "", "count": 0, "part": part_of_speech}
                
        self.set_vocab(vocab)
    
    def initialize_vocab(self):
        if not exists(self.vocab_filename_json):
            with open(self.vocab_filename_json, 'w') as f:
                f.write(json.dumps({"meta": {
                    "val_langid": f"{self.from_lang}",
                    "val_langname": f"{self.from_langname}",
                    "key_langid": f"{self.to_lang}",
                    "key_langname": f"{self.to_langname}"
                }}))
                
    def set_default_langs(self, frm, to):
         with open(f"{DATA_DIR}{sep}default_langs.json", 'w+') as f:
            f.write(json.dumps({"from": frm, "to": to}))
            
    def get_default_langs(self):
        try:
          with open(f"{DATA_DIR}{sep}default_langs.json", 'r') as f:
              default_langs = json.loads(f.read())
              return default_langs
        except:
            return {}

    # Save the in-memory vocab as a csv file            
    def save_vocab_csv(self):
        vocab = self.get_vocab()
        with open(f"{DATA_DIR}{sep}{self.to_lang}_{self.from_lang}_exported_words.csv", "w+") as file:
            csvwriter = csv.writer(file,  quotechar='|',  lineterminator='\n', quoting=csv.QUOTE_NONE)
            for k,v in vocab.items():
                if k == "meta": continue
                row = [k]
                row.append(v['part'])
                for w in v["translations"]:
                    row.append(w)
                try:
                    csvwriter.writerow(row)
                except:
                    print(f"Bad row: {row}")
                
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
            return f"The following language(s) were specified but are not available: {missing}"
        else:
            return None
        
    ######################
    # CLI-only functions #
    ######################
    def run_test_vocab(self):
        if not self.lang_attrs_set(): logging.info("Lang attrs not set")
        done = False
        lang1 = {"id": self.from_lang, "name": self.from_langname}
        lang2 = {"id": self.to_lang, "name": self.to_langname}
        if self.word_order == "from-to":
            [lang1, lang2] = [lang2, lang1]
        self.select_words()
        while not done:
            word = self.next_word()['text']
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
            # c = readchar.readkey()
            # if c == '\n':
            #     self.mark_correct(word if self.word_order == 'to-from' else trans)
    
    def run_add_vocab(self, no_trans_check):
        if not self.lang_attrs_set(): logging.info("Lang attrs not set")
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
                    # Manual translation
                    w_2 = input(f"{lang2['name']} word: ").lower()
                    if self.word_order == "from-to":
                         new_words.append((w_1, w_2))
                    else:
                        new_words.append((w_2, w_1))
                else:
                    # Translation service lookup
                    w_2 = self.client.translate(lang1["id"], lang2["id"], w_1)
                    if w_2:
                        w_2 = w_2.lower()
                    else:
                        print("The translation lookup failed. Check your Internet connection and your service subscription status. " +
                              "Use option --no-word-lookup (-nl) to skip the online lookup and specify translations manuially.")
                        sys.exit(0)
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
    app = VocabBuilder()
    app.initialize(add_vocab = args.add_vocab,
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
    
