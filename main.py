from providers.mistral import *
from providers.base import ModelProvider

# Create the same login, default class and I choose the provider to use
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

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
                ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "text")
                
            elif choice == "2":
                print("\033[93mThis isn't perfect yet, It still in development.\033[0m")
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
                        ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "audio")
    
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
                question = input("Enter your question about the notes: ")
                ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "summary")

            elif choice == "4":
                question = input("Enter your theme to create a quiz about: ")
                ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "quizz")

            elif choice == "5":
                question = input("Enter your question about the notes: ")
                ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "flashcards")

            elif choice == "6":
                question = input("Enter your question about the notes: ")
                ModelProvider("Mistral", os.getenv("PROVIDER_KEY")).speak_with_model(question, "video")

            elif choice == "0":
                print("\033[92mExiting the program. Goodbye!\033[0m")
                time.sleep(1.5)
                os.system('cls')
                break


if __name__ == "__main__":
    main()