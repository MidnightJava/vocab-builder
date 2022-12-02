from dotenv import load_dotenv

from ms_translater_client import MSTranslatorClient

class VocabBuilder():

    def __init__(self):
        self.client = MSTranslatorClient()
        langs = self.client.get_languages()
        print(langs)

if __name__ == "__main__":
    VocabBuilder()