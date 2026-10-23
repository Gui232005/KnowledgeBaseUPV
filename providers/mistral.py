"""
Log:
- YYYY-MM-DD - [NAME]: Describe the improvement made in this file.
- 2026-10-12 - [Guilherme Silva]: Added the ability to create videos and to play them.
- 2026-10-15 - [Guilherme Silva]: Improve the architecture of the project, creating a base class for the providers and making the code more modular and maintainable (NOT FINISHED).
- 2026-10-16 - [Guilherme Silva]: Start the ability to store the conversation in a JSON file, and to review the conversation.
- 2026-10-20 - [Guilherme Silva]: Added the conversation_review
- 2026-10-21 - [Guilherme Silva]: Load conversation files before review and reuse their JSON content when continuing a conversation.
- 2026-10-23 - [Guilherme Silva]: Complete the file change log header.
"""

import base64
import json
import os
import pathlib
import re
from cloup import file_path
from mistralai.client import Mistral as MistralClient
from dotenv import load_dotenv
import time
from gtts import gTTS #This is for text to speech
from playsound3 import playsound #This is for playing audio
import speech_recognition as sr #This is for speech to text
from providers.base import ModelProvider

load_dotenv()

class Mistral(ModelProvider):
    def __init__(self, api_key: str):
        super().__init__("Mistral", api_key)
        self.client = MistralClient(api_key=api_key)

    def conversation_review(self, conversation):
        print("\033[92mReviewing the conversation...\033[0m")
        if isinstance(conversation, (str, os.PathLike)):
            conversation_path = pathlib.Path(conversation)
            if not conversation_path.exists():
                conversation_path = pathlib.Path("conversations") / conversation_path
            with conversation_path.open("r", encoding="utf-8") as file:
                conversation = json.load(file)

        prompt = '''You're going to receive a JSON file with a conversation history stored there and you will review the conversation and give me a summary of that, with the 
            most important points, advices and conclusions about the whole conversation.
            The JSON content is included in the next message; review its content, not a filename.'''
        answer = self.model_output(
            prompt,
            json.dumps(conversation, ensure_ascii=False, indent=2),
            "Please review the conversation and give me a summary of that conversation.",
        )
        time.sleep(1)  # Adding a small delay to ensure the output is printed after the prompt
        os.system('cls')
        print(f"\033[92mConversation Review:\033[0m \n{answer}")

    def speak_with_model(self, question: str, output_type: str, conversation: list):
        return self.speak_with_model_about_notes(
            question,
            output_type,
            conversation,
        )

    def process_all_pdfs_in_folders(self):
        input_tokens = 0
        output_tokens = 0
        # Here I will print all the folders inside the "information" folder, and then I will print all the PDFs inside each folder.
        folder = "information"
        path = pathlib.Path(folder)
        prompt = '''Beleive you are the best student ih the world, and you take very complete notes, with all the details, about everything you see at PDF you see, 
            so you will receive a PDF and you will take notes about it, and you will give me the notes in a very complete way, with all the details, 
            so your colleagues can benefit from your notes. Your return should be only notes nothing else, and you should not answer any questions, only take notes.
                On your outputs you shouldn't have things like:
                "**Fim das Notas**
                **Elaborado por:** [Seu Nome] – O Melhor Aluno do Mundo 🌍📚
                **Data:** [Data de Hoje]
                ---
                **Nota**: Estas notas foram elaboradas com **detalhe máximo** para garantir que todos os colegas possam compreender os conceitos de IoT, desde os fundamentos até aplicações avançadas. Se tiverem dúvidas, não hesitem em perguntar! 😊"
            '''
        for e in os.scandir(path):
            if e.is_dir():
                print(f"Folder: {e.name}")
                file_path = pathlib.Path(f"md/{e.name}.md")
                if not file_path.exists():
                    for f in os.scandir(e.path):
                        if f.is_file() and f.name.endswith(".pdf"):
                            print(f"\033[91mLet's process the PDF:\033[0m {f.name}")
                            filepath = pathlib.Path(f.path)
                            chat_response = self.client.chat.complete(
                                model="mistral-large-latest",
                                messages=[
                                    {
                                        "role": "user",
                                        "content": [
                                            {"type": "text", "text": prompt},
                                            {
                                                "type": "document_url",
                                                "document_url": f"data:application/pdf;base64,{base64.b64encode(filepath.read_bytes()).decode('utf-8')}"
                                            }
                                        ]
                                    }
                                ]
                            )
                            print(f"\033[92mNotes for {f.name}:\033[0m")
                            output_text = chat_response.choices[0].message.content
                            print(f"\033[93mTokens used for {f.name}:\033[0m {chat_response.usage.total_tokens}")

                            input_tokens += chat_response.usage.prompt_tokens
                            output_tokens += chat_response.usage.completion_tokens

                            # See if the file was already created, if not create it, if yes, append the new notes to the file.
                            if not os.path.exists(f"md/{e.name}.md"):
                                with open(f"md/{e.name}.md", "w", encoding="utf-8") as f:
                                    f.write(f"\n{output_text}")
                                    f.close()
                                with open(f"md/{e.name}.md", "r", encoding="utf-8") as f:
                                    print(f.read())
                                    f.close()
                            else:
                                with open(f"md/{e.name}.md", "a", encoding="utf-8") as f:
                                    f.write(f"\n{output_text}")
                                    f.close()
                                with open(f"md/{e.name}.md", "r", encoding="utf-8") as f:
                                    print(f.read())
                                    f.close()
                    print(f"\033[92mFinished processing all PDFs in folder {e.name}.\033[0m")
                    if not os.path.exists(f"md/{e.name}.md"):
                        print(f"\033[91mNo notes were created for folder {e.name}, skipping index creation.\033[0m")
                    else:
                        path = pathlib.Path(f"md/{e.name}.md")
                        if path.exists():   
                            self.create_index(input_tokens, output_tokens, path)
                        else:
                            print(f"\033[91mThe file md/{e.name}.md does not exist, skipping index creation.\033[0m")

                else:
                    print(f"\033[93mThe file md/{e.name}.md already exists, skipping the folder.\033[0m")

    def create_index(self, input_tokens, output_tokens, path):
        prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen,
                and now you will create an index of all the notes you have taken, and you will return the index in a very complete way, with all the details,
                so your colleagues can benefit from your index, that index should have every single topic the notes contain, and the corresponding page numbers.
                    Your return should be only the index nothing else, and you should not answer any questions, only create the index.
                    At the end of your index you shoul have somthing like:

                    ### **Fim do Índice para este Arquivo**

                    This end should be the last line of your index, and you should not have any other text after this line, because this line is very important for 
                    the software to know that the index is finished, and that it should not read any other text after this line.

                    Here is something that you shouldn't do in your outputs:
                    # Index
                    - Here is the complete and detailed index of all the notes taken from the PDFs, organized by topic:
                    '''

        if not os.path.exists(path):
            print(f"\033[91mThe file {path} does not exist, skipping index creation.\033[0m")
            return

        print(f"\033[92mThe file {path} exists, let's create the index.\033[0m")

        # Read the notes we already have in the file
        with open(path, "r", encoding="utf-8") as f:
            notes_content = f.read()

        print(f"\033[91mLet's build the index for:\033[0m {path}")
        mistral_response = self.client.chat.complete(model="mistral-large-latest", messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": notes_content}
            ]
        }])

        #index_output = chat_response.choices[0].message.content
        index_output = mistral_response.choices[0].message.content
        print(f"\033[92mIndex created for {path}:\033[0m\n{index_output}")
        print(f"\033[93mTokens used for {path}:\033[0m {mistral_response.usage.total_tokens}")

        with open(path, "r+", encoding="utf-8") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(f"# Index\n{index_output}\n\n{content}")

        self.json_index_all_the_md_files(path)
        total_input_tokens = input_tokens + mistral_response.usage.prompt_tokens
        total_output_tokens = output_tokens + mistral_response.usage.completion_tokens
        input_tokens_cost = total_input_tokens * 0.00000044
        output_tokens_cost = total_output_tokens * 0.0000013
        total_cost = input_tokens_cost + output_tokens_cost
        print(f"\033[93mTotal cost to build {path}:\033[0m ${total_cost:.6f}")

        with open("cost.txt", "a+", encoding="utf-8") as file:
            file.write(f"Total cost to build {path}: ${total_cost:.6f}\n")

    def json_index_all_the_md_files(self, file_path):
        subject_name = pathlib.Path(file_path).stem
        prompt = f"""You will receive a md file, and you will create a JSON index of all the notes in that file, and you will return the JSON index in a very complete way,
                    with all the details, so your colleagues can benefit from your index.
                    The file field must be exactly "{subject_name}". Do not include the .md extension.
                    This is your template for the JSON index you will create:
                    [
                        {{
                            "file": "{subject_name}",
                            "summary": "Short description of the main content covered in this file",
                            "topics": [
                            "Main topic",
                            "Secondary topic",
                            "Specific concept"
                            ],
                            "keywords": [ # List of relevant keywords or phrases that can help in searching for this file
                            "keyword1",
                            "keyword2",
                            "keyword3",
                            "abbreviation"
                            ]
                        }}
                    ]
                """
        mistral_response = self.client.chat.complete(model="mistral-large-latest", messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "text", "text": json.dumps(pathlib.Path(file_path).read_text(encoding="utf-8"))},
                {"type": "text", "text": prompt}
            ]
        }])
        
        index_path = pathlib.Path("document_index.json")
        try:
            existing_index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.stat().st_size else []
        except (json.JSONDecodeError, FileNotFoundError):
            existing_index = []
        
        response_text = mistral_response.choices[0].message.content.strip()
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[1].rsplit("\n", 1)[0]
        
        new_index = json.loads(response_text)
        if isinstance(new_index, dict):
            new_index = [new_index]
        if not isinstance(new_index, list):
            raise ValueError("The model response must be a JSON object or array.")
        if not isinstance(existing_index, list):
            raise ValueError("document_index.json must contain a JSON array.")
        
        with index_path.open("w", encoding="utf-8") as f:
            json.dump(existing_index + new_index, f, ensure_ascii=False, indent=2)
        
        print(f"\033[92mJSON index created for {file_path}:\033[0m\n{new_index}")

    def model_output(self, prompt, returned_files, question, conversation = None):
        mistral_response = self.client.chat.complete(model="mistral-large-latest", messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Instructions:\n{prompt}"},
                    {"type": "text", "text": f"Available document index:\n{returned_files}"},
                    {"type": "text", "text": f"Current user request:\n{question}"},
                    {
                        "type": "text",
                        "text": (
                            "Previous conversation JSON:\n"
                            f"{json.dumps(conversation, ensure_ascii=False)}"
                        ),
                    },
                ]
            }
        ])
        return mistral_response.choices[0].message.content

    # Here you will use your MISTRAL KEY to make questions to the model about your knowledge
    def speak_with_model_about_notes(self, question, option, conversation):
        topic_doc = "document_index.json"
        path = pathlib.Path(topic_doc)

        if isinstance(conversation, (str, os.PathLike)):
            conversation_path = pathlib.Path(conversation)
            if not conversation_path.exists():
                conversation_path = pathlib.Path("conversations") / conversation_path
            with conversation_path.open("r", encoding="utf-8") as file:
                conversation = json.load(file)

        if not os.path.exists(path):
            print(f"\033[91mThe file {topic_doc} does not exist, skipping.\033[0m")
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            returned_files = []
            if conversation is None:
                see_file_to_read = '''You will receive a JSON, and that json is like a easier way for you to find the files with the content of the question, 
                you can use how many file you need to answer the question, you only return the files that you will use, 
                and you will not return any other file. The values in the "file" fields are the only valid file names.
                Return those exact values, without adding ".md" or changing their spelling, in this JSON format:
                {
                    "files_used": [
                        "AC",
                        "AI_1"
                    ]
                }'''
            else:
                see_file_to_read = '''You will receive a JSON, and that json is like a easier way for you to find the files with the content of the question, 
                you can use how many file you need to answer the question, and you will use the information from previous conversations to see if the answer was already given, you only return the files that you will use, 
                and you will not return any other file. The values in the "file" fields are the only valid file names.
                Return those exact values, without adding ".md" or changing their spelling, in this JSON format:
                {
                    "files_used": [
                        "AC",
                        "AI_1"
                    ]
                }
                If the request uses vague wording such as "these topics", infer the topics from the previous conversation and select the matching files from the index.
                If the previous conversation does not identify a topic, return an empty "files_used" array.'''

            # Here you will use the model to find the files to answer the question, and you will return the files in a JSON format
            while True:
                try:
                    selection_text = self.model_output(
                        see_file_to_read,
                        json.dumps(data),
                        question,
                        conversation
                    ).strip()
                    if not selection_text:
                        raise ValueError("Model returned empty content (check API key / model name).")
                    break
                except Exception as e:
                    print(f"\033[91mError: {e}. Retrying...\033[0m")
                    time.sleep(1)
                    continue

            json_candidate = ModelProvider.extract_json_object(selection_text)
            try:
                returned_files = json.loads(json_candidate).get("files_used", [])
            except json.JSONDecodeError:
                returned_files = []

            if not returned_files:
                print(f"\033[91mI only speak about the contents I know.\033[0m")
                exit(1)
            else:
                if conversation is None:
                    title_prompt= """ Generate a short title for this conversation.
                        Rules:
                        - Return only the title.
                        - Do not provide multiple suggestions.
                        - Do not include numbering, quotation marks, Markdown, explanations, or emojis.
                        - Use between 3 and 8 words.
                        - Use only letters, numbers, spaces, and hyphens.
                        - Do not include line breaks.
                        - The title must be suitable for use as a Windows or any other operating system filename.
                        - Do not include a file extension such as .json. """ 
                    title = self.model_output(title_prompt, json.dumps(returned_files), question, conversation)
                    title = title + ".json"
                else:
                    title = self.load_title()
                while True:
                    try: 
                        if option == "audio":
                            prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen, you're need see what is the file that contains the notes about the topic 
                                of the question, after that you will answer questions about the notes you have taken, and you will return the answer in a most complete way possible, with all the details,
                                so your colleagues can benefit from your answer, that answer should be based only on the notes you have taken, and not on your own knowledge.
                                You only use the file is attached to the question, and you will answer the question based on the notes in that file, and you will not use any other knowledge you have, 
                                only the notes in the file and if applicable, the information from previous conversations.
                            '''
                            mistral_response = self.model_output(prompt, json.dumps(returned_files), question, conversation)
                            self.create_conversation({"question": question, "answer": mistral_response}, title = title)
                            print(f"\033[92mAnswer:\033[0m {mistral_response}")

                            try:
                                # Here you will use the gTTS library to convert the text to speech, and then you will play the audio using the playsound library
                                parsed_response = re.sub(r"[*#_`~]", "", mistral_response).strip()
                                myobj = gTTS(text=parsed_response, lang="pt-PT", slow=False)
                                myobj.save("text_to_speech.mp3")
                                playsound("text_to_speech.mp3")
                                os.remove("text_to_speech.mp3")
                            except Exception as e:
                                print(f"\033[91mError in text-to-speech or audio playback: {e}\033[0m")
                                exit(1)
                            if question.lower() in ["exit", "stop"]:
                                os.system('cls')
                                break

                        elif option == "text":
                            prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen, you're need see what is the file that contains the notes about the topic 
                                of the question, after that you will answer questions about the notes you have taken, and you will return the answer in a most complete way possible, with all the details,
                                so your colleagues can benefit from your answer, that answer should be based only on the notes you have taken, and not on your own knowledge.
                                You only use the file is attached to the question, and you will answer the question based on the notes in that file, and you will not use any other knowledge you have, 
                                only the notes in the file and the information from previous conversations if applicable.
                            '''
                            answer = self.model_output(prompt, json.dumps(returned_files), question, conversation)
                            self.create_conversation(conversation_data={"question": question, "answer": json.dumps(answer)}, title = title)
                            os.system('cls')
                            print(f"\033[92mAnswer:\033[0m {answer}")
                            input("\033[93mPress Enter to continue...\033[0m")
                            os.system('cls')
                            break

                        elif option == "summary":
                            prompt = f'''You are a very good person to do summaries, and you will receive a text, and you will need to create a very good summary of that text, 
                                with the most important points of the text, and you will return the summary based on the text and the information from previous conversations if applicable.'''
                            answer = self.model_output(prompt, json.dumps(returned_files), question, conversation)
                            self.create_conversation(conversation_data={"question": question, "answer": answer}, title = title)
                            os.system('cls')
                            print(f"Summary: {answer}")
                            input("\033[93mPress Enter to continue...\033[0m")
                            break

                        elif option == "quizz":
                            grade = 0
                            prompt = f'''You are a very good person to create quizzes, and you will receive a request, and you will need to create a very good quiz of that request,
                                with the most important points of the content, but never reveal the correct option, I want into a format JSON, like this:
                                [
                                    {{
                                        "question": "Question 1",
                                        "options": [
                                            "Option A",
                                            "Option B",
                                            "Option C",
                                            "Option D"
                                        ]
                                    }},
                                    {{
                                        "question": "Question 2",
                                        "options": [
                                            "Option A",
                                            "Option B",
                                            "Option C",
                                            "Option D"
                                        ]
                                    }}
                                ] I only want the JSON, nothing else, and you will not answer any questions, only create the quiz.
                                    NOTE: Use the information from previous conversations if applicable that will improve your quality
                                '''
                            response = ModelProvider.extract_json_object(self.model_output(prompt, json.dumps(returned_files), question, conversation))
                            answer = "[" + response + "]"                 
                            self.create_conversation(conversation_data={"question": question, "answer": response}, title = title)                            
                            os.system('cls')
                            try:
                                json_quiz = json.loads(answer)
                                if isinstance(json_quiz, list):
                                    for i, q in enumerate(json_quiz):
                                        print(f"\033[92mQuestion {i + 1}:\033[0m {q.get('question')}")
                                        for j, opt in enumerate(q.get('options', [])):
                                            print(f"  Option {chr(65 + j)}: {opt}") # 65 is the ASCII code for 'A'
                                        while True:
                                            my_answer = input("\033[92mEnter your answer (A, B, C, D): \033[0m").strip().upper()
                                            if my_answer in ['A', 'B', 'C', 'D']:
                                                break
                                            print("\033[91mInvalid option. Please enter A, B, C, or D.\033[0m")
                                        print(f"\033[92mEvaluating your answer...\033[0m")
                                        prompt_check = '''You will need to evaluate the answer of the user, and you will need to tell if the answer is correct or not,
                                        and you will need to give a very complete explanation of the answer. Your is YES or NO, if the answer is NO give me the letter
                                        of the correct option, follow this template:
                                            "correct": "YES" or "NO",
                                            "correct_option": "A" or "B" or "C" or "D".
                                        No explanations, no other text, only the JSON, nothing else, and you will not answer any questions, only evaluate the answer of the user.'''
                                        correction = self.model_output(
                                            prompt_check,
                                            json.dumps(returned_files),
                                            f"Question: {q.get('question')}, Options: {q.get('options')}, User's answer: {my_answer}",
                                        )
                                        correction_data = ModelProvider.extract_json_object(correction)
                                        correction_json = json.loads(correction_data)
                                        if "YES" in correction:
                                            print(f"\033[92mCorrect! Your answer is right.\033[0m")
                                            grade += 1
                                            input("\033[92mPress Enter to continue to the next question...\033[0m")
                                            os.system('cls')
                                        else:
                                            print(f"\033[91mIncorrect. The correct answer is: {correction_json.get('correct_option')}\033[0m")
                                            input("\033[91mPress Enter to continue to the next question...\033[0m")
                                            os.system('cls')
                                final_grade = (grade / len(json_quiz)) * 100 if json_quiz else 0
                                print(f"\033[92mYour final grade is: {final_grade:.2f}%\033[0m")
                            except json.JSONDecodeError:
                                print(f"\033[91mError: The model did not return a valid JSON for the quiz.\033[0m")
                                print(f"\033[91mModel output:\033[0m {answer}")
                            except Exception as e:
                                print(f"\033[91mUnexpected error: {e}\033[0m")
                            input("\033[92mPress Enter to continue...\033[0m")
                            break

                        elif option == "flashcards":
                            prompt = f'''You are a very good person to create flashcards, and you will receive a request, and you will need to create a very good flashcards of that request,
                                with the most important points of the content, and you will return the flashcards in a JSON format, like this:
                                [
                                    {{
                                        "question": "Question 1",
                                        "answer": "Answer 1"
                                    }},
                                    {{
                                        "question": "Question 2",
                                        "answer": "Answer 2"
                                    }}
                                ] I only want the JSON, nothing else, and you will not answer any questions, only create the flashcards. And 10 flashcards is the maximum you can create, if the content is too big, 
                                you will create only 10 flashcards, and you will not create more than 10 flashcards.
                                NOTE: Use the information from previous conversations if applicable that will improve your quality
                                '''
                            response = ModelProvider.extract_json_object(self.model_output(prompt, json.dumps(returned_files), question, conversation))
                            self.create_conversation(conversation_data={"question": question, "answer": response}, title = title)
                            answer = "[" + response + "]"
                            os.system('cls')
                            try:
                                json_flashcards = json.loads(answer)
                                if isinstance(json_flashcards, list):
                                    for i, card in enumerate(json_flashcards):
                                        print(f"\033[92mFlashcard {i + 1}:\033[0m\n")
                                        print(f"Question: {card.get('question')}")
                                        input("\033[93mPress Enter to see the answer...\033[0m")
                                        print(f"Answer: {card.get('answer')}\n")
                                        input("\033[93mPress Enter to continue to the next flashcard...\033[0m")
                                        os.system('cls')
                                else:
                                    print(f"\033[91mError: The model did not return a valid JSON for the flashcards.\033[0m")
                            except json.JSONDecodeError:
                                print(f"\033[91mError: The model did not return a valid JSON for the flashcards.\033[0m")
                                print(f"\033[91mModel output:\033[0m {answer}")
                            except Exception as e:
                                print(f"\033[91mUnexpected error: {e}\033[0m")
                            input("\033[92mPress Enter to continue...\033[0m")
                            break
                        
                        elif option == "video":
                            prompt = """
                                Write a complete, runnable Python script using the Manim Community library
                                (16:9 widescreen layout).

                                Crucial requirements:
                                - Respond ONLY with raw Python code (no explanations and no Markdown fences).
                                - Match the language of the prompt for on-screen text.
                                - Create a fluid educational video, not a sequence of static slides.
                                - Use a clear visual rhythm: animate the introduction, reveal content progressively,
                                and use smooth transitions between ideas. Prefer FadeIn, FadeOut, Transform,
                                ReplacementTransform, FadeTransform, Create, Uncreate, AnimationGroup, or
                                LaggedStart with run_time and smooth_rate_func where appropriate.
                                - Avoid abrupt scene changes. Before replacing a section, animate it out or
                                transform it into the next section. Keep related objects on screen when they
                                provide context.
                                - Use short pauses after important concepts and vary animation timing naturally.
                                Use run_time values generally between 0.4 and 1.5 seconds, unless a longer
                                explanation genuinely needs more time.
                                - Use ONLY Text(...) for typography and labels. NEVER use Tex(...),
                                MathTex(...), or BulletedList(...), because LaTeX is not installed.
                                - Use only standard colors (WHITE, BLACK, BLUE, RED, GREEN, YELLOW, ORANGE,
                                PURPLE, GRAY) or hex strings such as '#2A9D8F'.
                                - When using Code(...), pass ONLY code_string='...' and language='python'.
                                Do not pass style, code_style, font, or font_name arguments.
                                - Write(...) only accepts one vectorized mobject. Use Write(text), Write(line),
                                or another individual VMobject. NEVER call Write(...) with Group(...),
                                VGroup(...), a Python list, or a container of mobjects. To write several
                                mobjects, use LaggedStart(*[Write(item) for item in items]).
                                - Use Group(...) only when a group itself is the target of an operation that
                                supports groups, such as FadeOut(group). Do not reuse that group with Write.
                                - Do not use VGroup(*self.mobjects) for cleanup; use Group(*self.mobjects).
                                - Design every scene for the actual Manim frame. Keep all content
                                inside a safe area with one unit of margin on every side; do not
                                place content at the extreme left or right edges.
                                - Never put a long sentence on one line. Split long text into multiple
                                lines with '\\n', use short bullet points, and use font_size between
                                24 and 40 for body text. A list must fit vertically as well as
                                horizontally; show fewer items per scene when necessary.
                                - Make the layout responsive to the rendered frame rather than assuming
                                fixed pixel positions. Use config.frame_width and config.frame_height,
                                frame_center, relative coordinates, and arrange/next_to methods.
                                Prefer arranging text with VGroup(...).arrange(DOWN, buff=...) and then
                                call group.scale_to_fit_width(config.frame_width - 1) and
                                group.scale_to_fit_height(config.frame_height - 1) when needed.
                                - Keep all important content inside a responsive safe area of
                                config.frame_width - 2 and config.frame_height - 2. Recalculate group
                                sizes after adding content, and use scale_to_fit_width or
                                scale_to_fit_height instead of hard-coded scaling when possible.
                                - Use a consistent 16:9 composition that remains readable when the video
                                player is resized or viewed on a smaller screen. Do not rely on tiny text,
                                edge-aligned objects, or fixed coordinates tied to one screen size.
                                - Use one coherent color palette and recurring visual elements so transitions
                                feel connected. Include a brief animated title and a closing summary when
                                appropriate, but do not add filler content.

                                NOTE: If applicable to the question use previous conversations to improve the quality of the video, if applicable to the case
                            """
                            answer = self.model_output(prompt, json.dumps(returned_files), question, conversation)
                            self.create_conversation(
                                conversation_data={
                                    "question": question,
                                    "answer": "A video was created successfully.",
                                },
                                title=title,
                            )
                            ModelProvider.run_video(answer, quality="m", preview=True)
                            input("\033[92mPress Enter to continue...\033[0m")
                            break

                    except Exception as e:
                        print(f"\033[91mError: {e}. Retrying...\033[0m")
                        time.sleep(1)
                        continue

        def ingest_specific_pdf_to_md(mdFile, pdf, mainFolder):
            prompt = '''Beleive you are the best student ih the world, and you take very complete notes, with all the details, about everything you see at PDF you see, 
                    so you will receive a PDF and you will take notes about it, and you will give me the notes in a very complete way, with all the details, 
                    so your colleagues can benefit from your notes. Your return should be only notes nothing else, and you should not answer any questions, only take notes.
                        On your outputs you shouldn't have things like:
                        "**Fim das Notas**
                        **Elaborado por:** [Seu Nome] – O Melhor Aluno do Mundo 🌍📚
                        **Data:** [Data de Hoje]
                        ---
                        **Nota**: Estas notas foram elaboradas com **detalhe máximo** para garantir que todos os colegas possam compreender os conceitos de IoT, desde os fundamentos até aplicações avançadas. Se tiverem dúvidas, não hesitem em perguntar! 😊"
                    '''

            folder_path = pathlib.Path(mainFolder)
            if not os.path.exists(folder_path):
                print(f"\033[91mThe folder {mainFolder} does not exist, skipping.\033[0m")
                return

            target_name = pathlib.Path(pdf).name

            file_path = pathlib.Path(f"md/{mdFile}.md") if not mdFile.endswith(".md") else pathlib.Path(f"md/{mdFile}")

            total_input_tokens = 0
            total_output_tokens = 0
            found = False

            pdf_files = sorted(
                (e for e in os.scandir(folder_path) if e.is_file() and e.name.endswith(".pdf")),
                key=lambda e: e.name
            )

            for f in pdf_files:
                if not found:
                    if f.name == target_name:
                        found = True
                    else:
                        print(f"\033[90mSkipping {f.name}, still looking for {target_name}.\033[0m")
                        continue

                filepath = pathlib.Path(f.path)
                print(f"\033[91mLet's process the PDF:\033[0m {filepath.name}")

                mistral_response = self.model_output(prompt, json.dumps([filepath.name]), f'''Please take notes about the PDF {filepath.name} and return them 
                                                     in a very complete way, with all the details.''')

                print(f"\033[92mNotes for {filepath.name}:\033[0m")
                output_text = mistral_response

                if not os.path.exists(file_path):
                    with open(file_path, "w", encoding="utf-8") as f2:
                        f2.write(f"\n{output_text}")
                else:
                    with open(file_path, "a", encoding="utf-8") as f2:
                        f2.write(f"\n{output_text}")

                with open(file_path, "r", encoding="utf-8") as f2:
                    print(f2.read())

                print(f"\033[92mFinished processing {filepath.name} into {file_path}.\033[0m")

            if not found:
                print(f"\033[91mCould not find {target_name} inside {mainFolder}.\033[0m")

            return total_input_tokens, total_output_tokens