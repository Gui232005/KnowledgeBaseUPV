# KnowledgeBaseUPV
This project is my idea to improve the way the student use AI to prepare to their exams, with LLMs we can access, like ChatGPT, Claude, Gemini, ... , we need to spend time attaching all the PDFs, this action can take you a lot of time, and it's not enough to attach all the PDFs, because we can reach several PDFs.

## Pre-Requirements
**Python:** 3.11.9(*recommended*)
**Requirements.txt**: Look at it

## Architecture
```mermaid
flowchart LR
    A[Web<br/><small>file: web.py</small>] <--> B[IA<br/><small>Gemma 3 1B 
    fiel: model.py</small>]
    B <--> C[RAG<br/><small>Can save you a lot of 
    tokens</small>]
```
## Step-by-Step
**Step 1:** *source .venv/bin/activate* at your root directory
