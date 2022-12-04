from dotenv import load_dotenv
load_dotenv()

import json
from os.path import exists, sep
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from ms_translater_client import MSTranslatorClient

DATA_DIR = "data"

class VocabBuilder():

    def __init__(self, **kwargs):
        self.vocab_filename = f"{DATA_DIR}{sep}{kwargs['from_lang']}_{kwargs['to_lang']}_vocab"
        self.initialize_vocab()
        self.client = MSTranslatorClient()
        self.langs = self.client.get_languages()
        
        if kwargs.get("pr_avail_langs", None):
            print("Available languages for translation")
            print("Code\tName")
            # print(json.dumps(self.langs, sort_keys=True, indent=4, ensure_ascii=False, separators=(',', ': ')))
            for k,v in self.langs.items():
                print(f"{k}\t{v['name']}")
        elif kwargs.get("pr_word_cnt", None):
            words = self.get_vocab()
            print(f"{len(words)} words saved")
        else:
            lang = self.client.detect_language("pomeriggio")
            print (lang)
        
            self.client.translate("pomeriggio")
    
    def get_vocab(self):
        with open(self.vocab_filename, 'r') as f:
            contents = f.read()
            return json.loads(contents)
    
    def initialize_vocab(self):
        
        if not exists(self.vocab_filename):
            with open(self.vocab_filename, 'a') as f:
                f.write(json.dumps({}))

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
    
    testGroup = parser.add_argument_group(title = "Test Vocabulary Options")
    testGroup.add_argument("-cct", "--correct-count-threshold", type=int, default=5, metavar="INTEGER",
                         help="Prioritize testing of words that have not been answered correctly this many times in a row")
    testGroup.add_argument("-at", "--age-threshold", type=int, default=15, metavar="INTEGER",
                         help="Prioritize testing of words that have not been tested for at least this many days")
    
    othGroup = parser.add_argument_group(title = "Other Options")
    othGroup.add_argument("-fl", "--from-lang", default="en", metavar="XY",
                         help="ID code for the language you know (use --pal to list them). Used only if the --no-word-lookup option is not selected")
    othGroup.add_argument("-tl", "--to-lang", default="es", metavar="XY",
                         help="ID code for the language you're learning (use --pal to list them). Used only if the --no-word-lookup option is not selected")
    args = parser.parse_args()
    VocabBuilder(add_vocab = args.add_vocab,
                 test_vocab = args.test_vocab,
                 no_word_lookup = args.no_word_lookup,
                 correct_count_threshold = args.correct_count_threshold,
                 age_threshold = args.age_threshold,
                 pr_word_cnt = args.pr_word_cnt,
                 pr_avail_langs = args.pr_avail_langs,
                 from_lang = args.from_lang,
                 to_lang = args.to_lang)