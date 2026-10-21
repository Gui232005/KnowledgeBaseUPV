"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-10 - [Guilherme Silva]: Improve CLI interface
- 2026-10-15 - [Guilherme Silva]: Improve the architecture of the project, creating a base class for the providers and making the code more modular and maintainable.
- 2026-10-15 - [AlexPT2k22]: Turned the loose string after the log into a comment so the imports stay at the top of the module (ruff E402).
- 2026-10-16 - [Guilherme Silva]: Fix provider and add the option Conversation Review to the CLI interface.
- 2026-10-20 - [Guilherme Silva]: Added the ability to select a conversation file to review.
- 2026-10-21 - [Guilherme Silva]: Add conversation restoration, active-chat continuation, conversation review selection, and a New Chat menu option.
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
            files_array = []
            dir_list = os.listdir("conversations")
            files = len(dir_list)
            if files > 1:
                for file in dir_list:
                    files_array.append(file)
                    print(f"\033[92m{file}\033[0m")
                input_file = input("\033[92mEnter the number of the conversation file you want to review: \033[0m")                
                conversation = files_array[int(input_file) - 1]
                path = os.path.join("conversations", conversation)

                conversation_file = files_array[int(input_file) - 1]
                with open("memory.txt", "w", encoding="utf-8") as f:
                    f.write(f"{conversation_file}")

                with open(path, "r", encoding="utf-8") as f:
                    conversation = json.load(f)
            elif files == 1:
                conversation = dir_list[0]
                path = os.path.join("conversations", conversation)
                with open(path, "r", encoding="utf-8") as f:
                    conversation = json.load(f)

                conversation_file = dir_list[0]
                with open("memory.txt", "w", encoding="utf-8") as f:
                    f.write(f"{conversation_file}")
            else:
                print("\033[91mNo conversation files found. Please create a conversation first.\033[0m")
                conversation = None
                return
            print(f"\033[92mConversation file {path} loaded successfully.\033[0m")
            time.sleep(3)
            break
        elif see.lower() == "n":
            conversation = None
            break
        else:
            print("\033[91mInvalid choice. Please try again.\033[0m")
            return conversation
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
                if os.path.exists("memory.txt") and conversation is None:
                    conversation = continue_conversation()
                question = input("\033[92mEnter your question about the notes: \033[0m")
                provider.speak_with_model(question, "text", conversation)
                
            elif choice == "2":
                # Here you will use the speech text recognition<
                r = sr.Recognizer()
                r.pause_threshold = 1
                r.dynamic_energy_threshold = True
                if os.path.exists("memory.txt") and conversation is None:
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
                if os.path.exists("memory.txt") and conversation is None:
                    conversation = continue_conversation()
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "summary", conversation)

            elif choice == "4":
                os.system('cls')
                if os.path.exists("memory.txt") and conversation is None:
                    conversation = continue_conversation()
                question = input("Enter your theme to create a quiz about: ")
                provider.speak_with_model(question, "quizz", conversation)

            elif choice == "5":
                os.system('cls')
                if os.path.exists("memory.txt") and conversation is None:
                    conversation = continue_conversation()
                question = input("Enter your question about the notes: ")
                provider.speak_with_model(question, "flashcards", conversation)

            elif choice == "6":
                os.system('cls')
                if os.path.exists("memory.txt") and conversation is None:
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