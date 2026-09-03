import base64
import os
import pathlib
from google import genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_KEY")

filepath = pathlib.Path('information\\1_ano\\1_semestre\\Algebra\\NotasALGA.pdf') # For one PDF file, you can change the path to the PDF you want to process, but I need to have a dynamic way to process all the PDFs in a folder, and create the corresponding markdown files.
client = genai.Client(api_key=GEMINI_KEY)

prompt = '''Beleive you are the best student ih the world, and you take very complete notes, with all the details, about everything you see at PDF you see, 
        so you will receive a PDF and you will take notes about it, and you will give me the notes in a very complete way, with all the details, 
        so your colleagues can benefit from your notes.'''

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=[
        {"type": "text", "text": prompt},
        {"type": "document", "data": base64.b64encode(filepath.read_bytes()).decode('utf-8'), "mime_type": "application/pdf"}
    ]
)

file = open("md/algebra.md", "w")
file.write(interaction.output_text)
file.close()
read = open("md/algebra.md", "r")
print(read.read())
read.close()

'''
THINGS TO DO:
1. Create a function to take all the PDFs by folder and create the corresponding markdown files.
2. Create a function to enable questions to the model about the notes, and make sure the model only answers based on the notes, and not on its own knowledge.
'''


# To see the token usage
print(f"Total tokens used: {interaction.usage.total_tokens}")