import base64
import os
import pathlib
from mistralai.client import Mistral
from dotenv import load_dotenv

load_dotenv()

MISTRAL_KEY = os.getenv("MISTRAL_KEY")

client = Mistral(api_key=MISTRAL_KEY)

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
                        chat_response = client.chat.complete(
                            model="mistral-large-2512",
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
                        print(output_text)
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

                # After a folder read all the PDFs and created the notes, I will create an index of the notes, with the title "Index".
                create_index(input_tokens, output_tokens) 
            
            else:
                print(f"\033[93mThe file md/{e.name}.md already exists, skipping the folder.\033[0m")
            
def create_index(input_tokens, output_tokens):
    # Here I will print all the folders inside the "information" folder, and then I will print all the PDFs inside each folder.
    folder = "md"
    path = pathlib.Path(folder)
    index_output = "" 
    prompt = '''You are a very good student, and you have taken very complete notes about the PDFs you have seen, 
            and now you will create an index of all the notes you have taken, and you will return the index in a very complete way, with all the details, 
            so your colleagues can benefit from your index, that index should have the every single topic that file contains and the respective pages. 
                Your return should be only the index nothing else, and you should not answer any questions, only create the index.
                '''
    ## This cycle will append the index in the top of the file, with the title "Index" and the page of each topic
    for e in os.scandir(path):
        print(f"File: {e.name}")
        if e.is_file() and e.name.endswith(".md"):
                print(f"\033[91mLet's process the PDF:\033[0m {e.name}")
                filepath = pathlib.Path(e.path)
                chat_response = client.chat.complete(
                    model="mistral-large-2512",
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
                print(f"\033[92mIndex for {e.name}:\033[0m")
                index_output = chat_response.choices[0].message.content
                print(index_output)
                print(f"\033[93mTokens used for {e.name}:\033[0m {chat_response.usage.total_tokens}")

                # Here I will append the index to the top of the file, with the title "Index" and the page of each topic
                with open(f"md/{e.name}", "r+", encoding="utf-8") as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(f"# Index\n{index_output}\n\n{content}")
                    f.close()
    # Here I will calculate the total cost of the tokens used to build the notes and the index, and print it in a file called "cost.txt"
    total_input_tokens = input_tokens + chat_response.usage.prompt_tokens
    total_output_tokens = output_tokens + chat_response.usage.completion_tokens
    input_tokens_cost = total_input_tokens * 0.00000044
    output_tokens_cost = total_output_tokens * 00.0000013
    total_cost = input_tokens_cost + output_tokens_cost
    print(f"\033[93mTotal cost to build {e.name}:\033[0m ${total_cost:.6f}")

    # Here I will append the total cost to a file called "cost.txt"
    file = open("cost.txt", "a+", encoding="utf-8")
    file.write(f"Total cost to build {e.name}: €{total_cost:.6f}\n")
    file.close()

def main():
    process_all_pdfs_in_folders()

if __name__=="__main__":
    main()

'''
THINGS TO DO:
1. Create a function to enable questions to the model about the notes, and make sure the model only answers based on the notes, and not on its own knowledge.
'''