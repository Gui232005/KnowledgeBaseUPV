"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-10 - [Guilherme Silva]: Improve CLI interface
- 2026-10-15 - [Guilherme Silva]: Improve the architecture of the project, creating a base class for the providers and making the code more modular and maintainable.
- 2026-10-15 - [AlexPT2k22]: Turned the loose string after the log into a comment so the imports stay at the top of the module (ruff E402).
"""

# Impedir que quem nao respeite as regras faça commits and pushs

from providers.mistral import Mistral
import speech_recognition as sr
import os
import time

OPTIONS = {
    "1": ("Speak with text"),
    "2": ("Speak with voice"),
    "3": ("Summary"),
    "4": ("Quiz"),
    "5": ("Flashcards"),
    "6": ("Video"),
    "0": ("Exit")
}

def main():
    provider = Mistral(os.getenv("PROVIDER_KEY")) 
    
    while True:
            # Menu to choose output type
            print("\n\033[94mPlease choose an option:\033[0m")
            for key, (description) in OPTIONS.items():
                print(f"{key}. {description}")
            choice = input("\033[92mEnter your choice: \033[0m")
            if choice not in OPTIONS:
                print("\033[91mInvalid choice. Please try again.\033[0m")
                continue

            if choice == "1":
                os.system('cls')
                question = input("\033[92mEnter your question about the notes: \033[0m")
                provider.speak_with_model(question, "text")
                
            elif choice == "2":
                # Here you will use the speech text recognition
                r = sr.Recognizer()
                r.pause_threshold = 1
                r.dynamic_energy_threshold = True
                while True:
                    try:
                        with sr.Microphone() as source:
                            print("Fale agora...")
                            r.adjust_for_ambient_noise(source, duration=1)
                            audio = r.listen(source, timeout=None, phrase_time_limit=None)
    
                        texto = r.recognize_google(audio, language="pt-PT")
                        print(f"Foi dito: {texto}")
                        question = texto
                        provider.speak_with_model(question, "audio")
    
                        if texto.lower() in ["exit", "stop"]:
                            os.system('cls')
                            exit(0)
                    except sr.UnknownValueError:
                        print("I don't understand. Say again.")
                    except sr.WaitTimeoutError:
                        print("Waiting for you to speak...")
                    except sr.RequestError as e:
                        print(f"Error: {e}")
            
            elif choice == "3":
                os.system('cls')
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "summary")

            elif choice == "4":
                os.system('cls')
                question = input("Enter your theme to create a quiz about: ")
                provider.speak_with_model(question, "quizz")

            elif choice == "5":
                os.system('cls')
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "flashcards")

            elif choice == "6":
                os.system('cls')
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "video")

            elif choice == "0":
                print("\033[92mExiting the program. Goodbye!\033[0m")
                time.sleep(1.5)
                os.system('cls')
                break


if __name__ == "__main__":
    main()