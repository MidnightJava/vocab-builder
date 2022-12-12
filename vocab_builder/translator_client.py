# Abstract class

class TranslatorClient():

    def get_languages(self):
        print("Unsupported operation: get_languages")
        return None

    def detect_language(self, text):
        print("Unsupported operation: detect_language")
        return None

    def translate(self, text):
        print("Unsupported operation: translate")
        return None
    
    def get_subscription_status(self):
        print("Unsupported funciton: get_subscription_status")
        return None