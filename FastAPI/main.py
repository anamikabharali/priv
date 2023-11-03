import uvicorn
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import requests
import wget
import re
import os
from io import BytesIO
from pypdf import PdfReader
import gunicorn
import httpx
import json
import openai

app = FastAPI()
with open('form_qa.json', 'r') as json_file:
    json_data = json.load(json_file)
# Set up OpenAI API Key
os.environ['OPENAI_API_KEY'] = "sk-r 7R8gBmZx4MvZKqVl2wET3BlbkFJu1cLyoePHirfzn98Hv7A"  #Passkey: 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
openai.api_key = os.getenv("OPENAI_API_KEY")
@app.post("/get_answer/")
def get_answer(context, user_question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Use the provided text to answer the user's question. If the answer cannot be found in the text, write 'I don't know the answer'"},
                {"role": "user", "content": f"\n\n{context}\n\nQuestion:\n{user_question}\n\nAnswer:\n"}
            ],
            temperature=0,
            max_tokens=257,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return str(e)

@app.get("/get_a/")
async def extract_text(user_url_input: str, user_question: str):
    if user_url_input in json_data:
        pdf_data = json_data[user_url_input]
        pyPDF_extraction = pdf_data['pyPDF_extraction']
        questions_and_answers = pdf_data['questions_and_answers']
    else:
        raise HTTPException(status_code=404, detail="PDF link not found in JSON data")
    
    # Get the answer using OpenAI
    answer = get_answer(pyPDF_extraction, user_question)
    return {
        "pyPDF_extraction": pyPDF_extraction,
        "answer": answer
        }
    
@app.get("/extract_text/")
async def extract_text(selected_tab: str, user_url_input: str, extraction_method: str):
    if selected_tab != "Try":
        raise HTTPException(status_code=400, detail="Invalid tab selected")
    try:
        if extraction_method == "PyPDF":
            # Match 'user_url_input' with 'pdf_link' to get 'pyPDF_extraction' and questions/answers
            response = requests.get(user_url_input)
            if response.status_code == 200:
                pdf_stream = BytesIO(response.content)
                pdf_file = PdfReader(pdf_stream)
                extracted_texts = []
                for page_num in range(len(pdf_file.pages)):
                    page = pdf_file.pages[page_num]
                    page_text = page.extract_text()
                    extracted_texts.append(page_text)
                    concatenated_string = "".join(extracted_texts)
            return {"texts": concatenated_string}
                
        elif extraction_method == "Nougat OCR":
            target_directory = "https://github.com/BigDataIA-Fall2023-Team5/fastApi/"
            wget.download(user_url_input, out=target_directory)
            match = re.search(r'/([^/]+)$', user_url_input)
            extracted_part = match.group(1)
            file_path = os.path.join(target_directory, extracted_part)
            url = "https://f3bb-35-196-208-33.ngrok-free.app/predict"
            payload = {}
            files = [('file', (extracted_part, open(file_path, 'rb'), 'application/pdf'))]
            headers = {}
            response = requests.request("POST", url, headers=headers, data=payload, files=files)
            if response.status_code == 200:
                extracted_text = response.text
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                return {"texts": extracted_text}
                
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to retrieve PDF from URL: {response.status_code}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail="Enter URL Above or check the error: " + str(e))

if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
