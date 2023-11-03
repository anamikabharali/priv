import uvicorn
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, status
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


from datetime import datetime, timedelta
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext

SECRET_KEY = "787ba61010a4ed2ddd9f2108fbce1d41c54b3156821621c9310fda37d1c8bb43"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 300


fake_users_db = {
    "anamika": {
        "username": "anamika",
        "hashed_password": "$2b$12$tIuUebxpoLqU03leSs9TSu9Y4qsnMc5TSAa26hR3wQffgEFN5X4Jm",
        "disabled": False,
    },
    "shruti": {
        "username": "shruti",
        "hashed_password": "$2b$12$dxDgdB3dLY0C9kSq6rwLdeNhv//QThEGt/xf/jOx3fsS6RxM.XS6G",
        "disabled": False,
    },
    "saniya": {
        "username": "saniya",
        "hashed_password": "$2b$12$2Kbc9YFtLzoi4N2pMiELHOY59KBzVGwro0sNeaMwKx5gRRQYOkFXK",
        "disabled": False,
    }
}

def get_password_hash(password):
    return pwd_context.hash(password)


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#usernames = ['anamika','shruti','saniya']
#hashed_password = ['$2b$12$tIuUebxpoLqU03leSs9TSu9Y4qsnMc5TSAa26hR3wQffgEFN5X4Jm','$2b$12$dxDgdB3dLY0C9kSq6rwLdeNhv//QThEGt/xf/jOx3fsS6RxM.XS6G','$2b$12$2Kbc9YFtLzoi4N2pMiELHOY59KBzVGwro0sNeaMwKx5gRRQYOkFXK']


app = FastAPI()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]


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
