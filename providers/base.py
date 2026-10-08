'''
Base class for all AI providers.
'''
from dotenv import load_dotenv
from .mistral import speak_with_model_about_notes

load_dotenv()

class ModelProvider:
    def __init__(self, model_name: str, model_key: str):
        self.model_name = model_name
        self.model_key = model_key

    def print_info(self):
        print(f"Model Name: {self.model_name}, Model Key: {self.model_key}")

    def get_model_name(self):
        return self.model_name

    def speak_with_model(self, question:str, output_type:str):
        if self.model_name == "Mistral":
            speak_with_model_about_notes(question, output_type, self.model_key)