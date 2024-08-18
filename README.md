# vocab-builder (work in progress)

This is the back-end component (implemented in python) of the Vocabulary Builder app. The front-end component is https://github.com/MidnightJava/vocab-builder-ui. Eventually the front-end and back-end will be combined into a single AppImage installable product using Tauri (https://tauri.app/)

The purpose of the app is to support the learning of a new language by providing an adaptive vocabulary test capability. The app does not teach you a  new language. Rather it works in concert with a language-learning app, such as DuoLingo or Babble. It can support any language, even one you just make up, and it can work with words and/or phrases. Thus you can use it to memorize answers to questions in a specific domain.

The user loads the vocabulary information into the app by either importing a csv file, entering words/phrases on a command line, or adding words/phrases to a table in the User Interface (UI). The user can specify the translation (or answer) for each entry, or the app can lookup translations online via the Microsoft Azure-hosted language translation API. The user must supply an API key for the online lookup to work. The Azure service is free with a usage limit of 500,000 characters per month.

## To install the back-end python application (Linux):

1. Create a python virtual environment
```
sudo yum install python3-virtualenv | sudo apt-get install python3-virtualenv
cd <project location>
virtualenv venv -p python3
```

2. Activate the virtual environment
```
. ./venv/bin/activate
```

3. Install dependencies:
```
pip install -r requirements.txt
```
4. Obtain an API key from MS Azure and specify it in the file ~/.env (create this file if it doesn't exist) as follows:
```export API_KEY="<YOUR_API_KEY>"```

5. Create a free subscription to the Microsoft Translation Service at https://learn.microsoft.com/en-us/rest/api/cognitiveservices/translator/translator. Create an API key and define it in your environment like this:
"API_KEY=<YOUUR API KEY>"  You can skip this if you want to provide word translations manually instead of relying on an external service. In that case, launch the program with the -nl option.

## To run the python command-line app:
```
vocab_builder/vocab_builder.py -h

usage: Vocab Builder [-av | -tv | -pwc | -pal | -iv IMPORT_VOCAB | -h] [-nl]
                     [-ntc] [-mc MIN_CORRECT] [-ma MIN_AGE] [-fl FROM_LANG]
                     [-tl TO_LANG] [-wo to-from | from-to]

A vocabulary practice tool for learning a foreign language

optional arguments:
  -av, --add-vocab      Prompt repeatedly for new vocabulary words to be
                        stored (default: False)
  -tv, --test-vocab     Present flashcard-style tests for stored vocabulary
                        words (default: False)
  -pwc, --pr-word-cnt   Print the number of stored words and exit (default:
                        False)
  -pal, --pr-avail-langs
                        Print the available languages and exit. Used only if
                        the --no-word-lookup option is not selected. (default:
                        False)
  -iv IMPORT_VOCAB, --import-vocab IMPORT_VOCAB
                        Path to csv file with vocabulary words to be imported
                        (default: None)
  -h, --help            Show this help message and exit

Add Vocabulary Options:
  -nl, --no-word-lookup
                        Manually specify the translation of words instead of
                        relying on the external translation service (default:
                        False)
  -ntc, --no-trans-check
                        When using the external translation service, accept
                        the translation without prompting for confirmation or
                        override (default: False)

Test Vocabulary Options:
  -mc MIN_CORRECT, --min-correct MIN_CORRECT
                        Prioritize testing of words that have not been
                        answered correctly this many times in a row (default:
                        5)
  -ma MIN_AGE, --min-age MIN_AGE
                        Prioritize testing of words that have not been tested
                        for at least this many days (default: 15)

Other Options:
  -fl FROM_LANG, --from-lang FROM_LANG
                        Name of the language you know. You must use one of the
                        ID codes displayed with the --pal option unless--no-
                        word-lookup option is selected (default: en)
  -tl TO_LANG, --to-lang TO_LANG
                        Name of the language you're learning. You must use one
                        of the ID codes displayed with the --pal option unless
                        --no-word-lookup option is selected (default: it)
  -wo to-from | from-to, --word-order to-from | from-to
                        Present words in the language you're learning
                        (to-from) or the language you already know (from-to). default:
                        to-from
  
  4. To run the server version of the app (to be used with the UI) instead of the command line client
  vocab_builder/server.py
```

Launch the https://github.com/MidnightJava/vocab-builder-ui web application (see the readme there), and it will connect to the server automatically. You can also test the REST API in the server by looking at server.py and using a web browser or a command-line tool like curl to form an appropriate HTTP request message, using either the GET or POST methods.

### To Build the Python App as a SIngle Executable
```
1. cd <project directory>

2. . venv/bin/activate

3. pip install pyinstaller

4. pyinstaller -F vocab_builder/server.py

5. find executable at dist/server
```

