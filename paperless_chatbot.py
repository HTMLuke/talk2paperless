from fastapi import FastAPI
from pydantic import BaseModel
import requests
import spacy
import dateparser
import uvicorn
import logging
import os
from dotenv import load_dotenv


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger("paperless_chatbot")
load_dotenv(".env")


# Load NLP model
nlp = spacy.load("de_core_news_sm")


# Paperless-ngx Config
BASE_URL = os.environ.get("BASE_URL")
UI_BASE_URL = os.environ.get("UI_BASE_URL")
API_KEY = os.environ.get("API_KEY")

app = FastAPI(title="Paperless Chatbot API")


class QueryRequest(BaseModel):
    text: str


def parse_query(text: str):
    """Extracts document type, tags, contributors, and date from text"""
    doc = nlp(text)
    result = {
        "document_type": None,
        "tags": [],
        "contributors": [],
        "start_date": None,
        "end_date": None
    }

    # Recognize document type
    for token in doc:
        if token.lemma_.lower() in ["rechnung", "vertrag", "bericht"]:
            result["document_type"] = token.lemma_.lower()

    # Recognize contributors
    for ent in doc.ents:
        if ent.label_ == "ORG":
            result["contributors"].append(ent.text)

    # Recognize date
    date = dateparser.parse(text)
    if date:
        result["start_date"] = date.date().isoformat()
        result["end_date"] = date.date().isoformat()

    # Recognize tags: only nouns not document type or contributor
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            if token.lemma_.lower() not in ["rechnung", "vertrag", "bericht"] \
               and token.text not in result["contributors"] \
               and not dateparser.parse(token.text):
                result["tags"].append(token.lemma_)

    return result


def fetch_all_documents(query: dict):
    """Fetches all documents from Paperless (with pagination)"""
    documents = []
    url = f"{BASE_URL}/documents/"
    headers = {"Authorization": f"Token {API_KEY}"}

    params = {}
    if query.get("document_type"):
        params["document_type__name__icontains"] = query["document_type"]
    if query.get("tags"):
        params["tags__name__icontains"] = ",".join(query["tags"])
    if query.get("contributors"):
        params["correspondent__name__icontains"] = ",".join(query["contributors"])
    if query.get("start_date"):
        params["created__date__gte"] = query["start_date"]
    if query.get("end_date"):
        params["created__date__lte"] = query["end_date"]

    page = 1
    while True:
        params["page"] = page
        logger.info(f"API request: URL={url} PARAMS={params}")
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Error during API request: {e}")
            return {"error": str(e)}

        try:
            data = response.json()
        except ValueError:
            logger.error(f"Invalid JSON response: {response.text}")
            return {"error": "Response is not valid JSON"}

        results = data.get("results", [])
        if not results:
            break
        documents.extend(results)
        if not data.get("next"):
            break
        page += 1

    return documents


def format_user_message(documents):
    """Creates a user-friendly message with links to documents"""
    if not documents:
        return "No documents found."

    lines = []
    for doc in documents:
        title = doc.get("title", "Untitled document")
        link = f"{UI_BASE_URL}/{doc.get('id')}/"
        lines.append(f"[{title}]({link})")

    message = f"{len(lines)} document(s) found:\n" + "\n".join(lines)
    return message


@app.post("/query")
def handle_query(request: QueryRequest):
    parsed = parse_query(request.text)
    documents = fetch_all_documents(parsed)
    if isinstance(documents, dict) and "error" in documents:
        return {"message": f"Error fetching documents: {documents['error']}"}

    user_message = format_user_message(documents)
    return {"message": user_message}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7000)
