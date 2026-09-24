import base64
import json
import os
import pathlib
import re
from google import genai
from google.genai import types
from mistralai.client import Mistral
from dotenv import load_dotenv
from supabase import create_client, Client
import time

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
MISTRAL_KEY = os.getenv("MISTRAL_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")

client = genai.Client(api_key=GEMINI_KEY)

def connect_to_supabase():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user: dict = supabase.auth.sign_in_with_password({
        'email': USERNAME,
        'password': PASSWORD,
    })
    print("Connected to Supabase:", supabase)
    return supabase

def process_all_pdfs_in_folders():
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
                        chat_response = client.models.generate_content(
                            model="gemini-3.1-flash-lite",
                            contents=[
                                    types.Part.from_bytes(
                                        data=pathlib.Path(filepath).read_bytes(),
                                        mime_type="application/pdf"
                                    ),
                                    prompt
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
                        create_index(input_tokens, output_tokens, path)
                    else:
                        print(f"\033[91mThe file md/{e.name}.md does not exist, skipping index creation.\033[0m")
            
            else:
                print(f"\033[93mThe file md/{e.name}.md already exists, skipping the folder.\033[0m")
            
def create_index(input_tokens, output_tokens, path):
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
    chat_response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=[
            prompt,
            notes_content
        ]
    )
    index_output = chat_response.choices[0].message.content
    
    print(f"\033[92mIndex created for {path}:\033[0m\n{index_output}")
    print(f"\033[93mTokens used for {path}:\033[0m {chat_response.usage.total_tokens}")

    with open(path, "r+", encoding="utf-8") as f:
        content = f.read()
        f.seek(0, 0)
        f.write(f"# Index\n{index_output}\n\n{content}")

    json_index_all_the_md_files(path)
    total_input_tokens = input_tokens + chat_response.usage.prompt_tokens
    total_output_tokens = output_tokens + chat_response.usage.completion_tokens
    input_tokens_cost = total_input_tokens * 0.00000044
    output_tokens_cost = total_output_tokens * 0.0000013
    total_cost = input_tokens_cost + output_tokens_cost
    print(f"\033[93mTotal cost to build {path}:\033[0m ${total_cost:.6f}")

    with open("cost.txt", "a+", encoding="utf-8") as file:
        file.write(f"Total cost to build {path}: ${total_cost:.6f}\n")

# Here you will use GEMINI if the key is available, if not use MISTRAL
def speak_with_model_about_notes(question):
    prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen, you're need see what is the file that contains the notes about the topic 
            of the question, after that you will answer questions about the notes you have taken, and you will return the answer in a most complete way possible, with all the details,
            so your colleagues can benefit from your answer, that answer should be based only on the notes you have taken, and not on your own knowledge.
                You only use the file is attached to the question, and you will answer the question based on the notes in that file, and you will not use any other knowledge you have, 
            only the notes in the file.
            '''
    topic_doc = "document_index.json"
   # folder = "md"
    path = pathlib.Path(topic_doc)

    if not os.path.exists(path):
        print(f"\033[91mThe file {topic_doc} does not exist, skipping.\033[0m")
        return
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        returned_files = []
        see_file_to_read = '''You will receive a JSON, and that json is like a easier way for you to find the files with the content of the question, 
        you can use how many file you need to answer the question, you only return the files that you will use, 
        and you will not return any other file, and you will return the files in a JSON format, like this:
        {
            "files_used": [
                "file1.md",
                "file2.md"
            ]
        }'''
        while True:
            try:
                files_to_read = client.models.generate_content(
                    model="gemini-3.1-flash-lite",
                    contents=[
                         see_file_to_read,
                            json.dumps(data),
                            question
                    ]
                )

                selection_text = (files_to_read.text).strip()
                if not selection_text:
                    raise ValueError("Model returned empty content (check API key / model name).")
                break
            except Exception as e:
                print(f"\033[91mError: {e}. Retrying...\033[0m")
                time.sleep(1)
                continue

        def extract_json_object(text):
            # Prefer a ```json ... ``` fenced block anywhere in the text
            fence_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
            if fence_match:
                return fence_match.group(1)
            fence_match = re.search(r"```\s*(\{.*?\})\s*```", text, re.DOTALL)
            if fence_match:
                return fence_match.group(1)
            # Fall back to the first { ... last } in the text
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return text[start:end + 1]
            return text

        json_candidate = extract_json_object(selection_text)
        try:
            returned_files = json.loads(json_candidate).get("files_used", [])
        except json.JSONDecodeError:
            returned_files = []

        if not returned_files:
            print(f"\033[91mI only speak about the contents I know.\033[0m")
            exit(1)
        else:
            while True:
                try:
                    response = client.models.generate_content(
                        model="gemini-3.1-flash-lite",
                        contents=[
                            prompt,
                            json.dumps(returned_files),
                            question
                        ]
                    )
                    break
                except Exception as e:
                    print(f"\033[91mError: {e}. Retrying...\033[0m")
                    time.sleep(1)
                    continue
    
    print(f"\033[92mAnswer to the question:\033[0m\n{response.text}")           

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

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=[
                types.Part.from_bytes(
                    data=pathlib.Path(file_path).read_bytes(),
                    mime_type="application/md"
                    ),
                prompt
            ]
        )

        print(f"\033[92mNotes for {filepath.name}:\033[0m")
        output_text = response.text.strip()
        print(f"\033[93mTokens used for {filepath.name}:\033[0m {response.usage_metadata.total_token_count}")

        total_input_tokens += response.usage_metadata.prompt_token_count
        total_output_tokens += response.usage_metadata.completion_token_count

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

def json_index_all_the_md_files(file_path):
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
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=[
            types.Part.from_bytes(
                data=pathlib.Path(file_path).read_bytes(),
                mime_type="application/md"
            ),
            prompt
        ]
    )

    index_path = pathlib.Path("document_index.json")
    try:
        existing_index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.stat().st_size else []
    except (json.JSONDecodeError, FileNotFoundError):
        existing_index = []

    response_text = response.text.strip()
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

    print(f"\033[92mJSON index created for {file_path}:\033[0m\n{response.text}")
'''
def see():
    #Write all the folders and PDFs inside the "information\\CSO" folder, at any depth
    for root, dirs, files in os.walk("information\\CSO"):
        for d in dirs:
            print(f"Folder: {d}")
        for f in files:
            if f.endswith(".pdf"):
                print(f"PDF: {f}")
'''
def main():
    while True:
        question = input("Ask a question about the notes: ")
        speak_with_model_about_notes(question)

if __name__=="__main__":
    main()