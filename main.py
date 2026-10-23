"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-10 - [Guilherme Silva]: Improve CLI interface
- 2026-10-15 - [Guilherme Silva]: Improve the architecture of the project, creating a base class for the providers and making the code more modular and maintainable.
- 2026-10-15 - [AlexPT2k22]: Turned the loose string after the log into a comment so the imports stay at the top of the module (ruff E402).
- 2026-10-16 - [Guilherme Silva]: Fix provider and add the option Conversation Review to the CLI interface.
- 2026-10-20 - [Guilherme Silva]: Added the ability to select a conversation file to review.
- 2026-10-21 - [Guilherme Silva]: Add conversation restoration, active-chat continuation, conversation review selection, and a New Chat menu option.
- 2026-10-23 - [Guilherme Silva]: Complete the file change log header.
"""

# Impedir que quem nao respeite as regras faça commits and pushs

import json

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
    "7": ("Conversation Review"),
    "8": ("New Chat"),
    "0": ("Exit")
}

def load_conversation():
    while True:
        see = input("\033[92mDo you want to restore a previous conversation? (y/n): \033[0m")
        if see.lower() == "y":
            if not os.path.isdir("conversations"):
                print("\033[91mNo conversation files found. Please create a conversation first.\033[0m")
                return None

            files_array = sorted(
                file
                for file in os.listdir("conversations")
                if file.lower().endswith(".json")
                and os.path.isfile(os.path.join("conversations", file))
            )
            if not files_array:
                print("\033[91mNo conversation files found. Please create a conversation first.\033[0m")
                return None

            if len(files_array) == 1:
                conversation_file = files_array[0]
            else:
                for index, file in enumerate(files_array, start=1):
                    print(f"\033[92m{index}. {file}\033[0m")
                input_file = input("\033[92mEnter the number of the conversation file to restore: \033[0m")
                try:
                    file_index = int(input_file) - 1
                    conversation_file = files_array[file_index]
                except (ValueError, IndexError):
                    print("\033[91mInvalid conversation number. Please try again.\033[0m")
                    continue

            path = os.path.join("conversations", conversation_file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    conversation = json.load(f)
            except (OSError, json.JSONDecodeError) as error:
                print(f"\033[91mCould not load {conversation_file}: {error}\033[0m")
                return None

            with open("memory.txt", "w", encoding="utf-8") as f:
                f.write(conversation_file)

            print(f"\033[92mConversation file {path} loaded successfully.\033[0m")
            time.sleep(3)
            break
        elif see.lower() == "n":
            conversation = None
            if os.path.exists("memory.txt"):
                os.remove("memory.txt")
            break
        else:
            print("\033[91mInvalid choice. Please try again.\033[0m")
            continue
    os.system('cls')
    return conversation

def continue_conversation():
    with open("memory.txt", "r", encoding="utf-8") as f:
        conversation = f.read().strip()
        if conversation:
            return conversation

def main():
    provider = Mistral(os.getenv("PROVIDER_KEY"))

    conversation = load_conversation()

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
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                question = input("\033[92mEnter your question about the notes: \033[0m")
                provider.speak_with_model(question, "text", conversation)
                
            elif choice == "2":
                # Here you will use the speech text recognition<
                r = sr.Recognizer()
                r.pause_threshold = 1
                r.dynamic_energy_threshold = True
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                while True:
                    try:
                        with sr.Microphone() as source:
                            print("Fale agora...")
                            r.adjust_for_ambient_noise(source, duration=1)
                            audio = r.listen(source, timeout=None, phrase_time_limit=None)
    
                        texto = r.recognize_google(audio, language="pt-PT")
                        print(f"Foi dito: {texto}")
                        question = texto
                        provider.speak_with_model(question, "audio", conversation)
    
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
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "summary", conversation)

            elif choice == "4":
                os.system('cls')
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                question = input("Enter your theme to create a quiz about: ")
                provider.speak_with_model(question, "quizz", conversation)

            elif choice == "5":
                os.system('cls')
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "flashcards", conversation)

            elif choice == "6":
                os.system('cls')
                if conversation is None and os.path.exists("memory.txt"):
                    conversation = continue_conversation()
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "video", conversation)

            elif choice == "7":
                os.system('cls')
                if conversation is None:
                    dir_list = os.listdir("conversations")
                    for file in dir_list:
                        if os.path.exists(os.path.join("conversations", file)):
                            provider.conversation_review(file)
                else:
                    provider.conversation_review(conversation)
            elif choice == "8":
                os.system('cls')
                conversation = None
                if os.path.exists("memory.txt"):
                    os.remove("memory.txt")
                
            elif choice == "0":
                print("\033[92mExiting the program. Goodbye!\033[0m")
                #delete the conversation.json file
                if os.path.exists("conversation.json"):
                    os.remove("conversation.json")
                time.sleep(1.5)
                os.system('cls')
                if os.path.exists("memory.txt"):
                    os.remove("memory.txt")
                else:
                    pass
                break


if __name__ == "__main__":
    main()