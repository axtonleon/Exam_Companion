import os
import json
import uuid
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

from models import *
from utils import (
    get_youtube_index, get_document_index, get_audio_index,
    fix_json_string, get_hash, TRANSCRIPT_DIR
)

load_dotenv()

app = FastAPI(
    title="Exam Companion API",
    description="A powerful API that helps students and educators process, analyze, and generate questions from various study materials.",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global cache: mapping session_id -> list of index objects
SESSION_INDEX_CACHE = {}

async def get_session_id(request: Request) -> str:
    """Get or create a unique session ID for the current user session."""
    if not request.cookies.get("session_id"):
        return str(uuid.uuid4())
    return request.cookies.get("session_id")

@app.get("/", response_class=HTMLResponse)
async def home():
    """Home route that explains the API."""
    return """
    <html>
      <head>
        <title>Multi-Content Query API</title>
      </head>
      <body>
        <h1>Multi-Content Query API</h1>
        <p>This API allows you to upload content (YouTube videos, documents, or audio files) and query them.</p>
        <ul>
          <li><b>/upload</b>: Upload a YouTube URL, document, or audio file. Uploaded content is associated with your session.</li>
          <li><b>/query</b>: Query all content uploaded in your session.</li>
        </ul>
        <p>For detailed API documentation and testing, visit the Swagger UI:</p>
        <a href="/docs" target="_blank">API Documentation</a>
      </body>
    </html>
    """

@app.post("/upload", response_model=UploadResponse)
async def upload(
    request: Request,
    response: Response,
    youtube_url: Optional[str]= File(None),
    file: Optional[UploadFile] = File(None)
):
    """Upload content (YouTube URL, document, or audio file)."""
    session_id = await get_session_id(request)
    response.set_cookie(key="session_id", value=session_id)
    
    if session_id not in SESSION_INDEX_CACHE:
        SESSION_INDEX_CACHE[session_id] = []

    if not youtube_url and not file:
        raise HTTPException(
            status_code=400,
            detail="No content provided. Please supply a youtube_url or upload a file."
        )

    try:
        if youtube_url:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(youtube_url)
            video_id = parse_qs(parsed_url.query).get('v', [''])[0]
            if not video_id:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid YouTube URL. Could not extract video ID."
                )

            index_obj = get_youtube_index(youtube_url)
            
            transcript_filename = f"{video_id}_youtube.txt"
            transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)
            
            if not os.path.exists(transcript_path):
                raise HTTPException(
                    status_code=500,
                    detail="Failed to save transcript during upload"
                )
                
            SESSION_INDEX_CACHE[session_id].append({"type": "youtube", "id": video_id, "index": index_obj["index"]})
            
            return UploadResponse(
                message="Content uploaded successfully.",
                content_type="youtube",
                content_id=video_id
            )

        if file:
            if file.filename == '':
                raise HTTPException(status_code=400, detail="No file selected")

            document_id = file.filename
            suffix = os.path.splitext(file.filename)[1].lower()

            if suffix in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"]:
                index_obj = get_document_index(document_id, file, file.filename)
                content_type = "document"
            elif suffix in [".mp3", ".wav", ".m4a", ".ogg"]:
                index_obj = get_audio_index(document_id, file, file.filename)
                content_type = "audio"
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            if index_obj is None:
                raise HTTPException(status_code=500, detail="Failed to index file.")

            SESSION_INDEX_CACHE[session_id].append(index_obj)
            return UploadResponse(
                message="Content uploaded successfully.",
                content_type=content_type,
                content_id=document_id
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query(
    request: Request,
    response: Response,
    query_request: QueryRequest
):
    """Query all content uploaded in the session."""
    session_id = await get_session_id(request)
    response.set_cookie(key="session_id", value=session_id)
    
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(status_code=404, detail="No content indexed in the session.")

    responses = []
    try:
        for content in SESSION_INDEX_CACHE[session_id]:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6)
            retriever = content["index"].as_retriever()
            qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
            result = qa_chain.invoke({"query": query_request.query})
            responses.append(f"[{content['type']}:{content['id']}] {result}")
        
        return QueryResponse(answer="\n".join(responses))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate/mcq", response_model=MCQResponse)
async def generate_mcq(request: Request, mcq_request: MCQRequest):
    """Generate multiple-choice questions from uploaded content."""
    session_id = await get_session_id(request)
    
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(
            status_code=404,
            detail="Please upload materials before generating MCQs."
        )

    selected_indexes = SESSION_INDEX_CACHE[session_id]
    combined_context = ""
    for idx in selected_indexes:
        retriever = idx['index'].as_retriever()
        retrieved_docs = retriever.get_relevant_documents("summarize")
        for doc in retrieved_docs:
            combined_context += doc.page_content + "\n"

    prompt = f"""
You are an AI assistant that generates multiple-choice questions from study material.
Based on the following content, generate {mcq_request.num_questions} multiple-choice questions.
Each question must have one correct answer and three plausible distractors.
The questions should be at a {mcq_request.difficulty} difficulty level.
Content:
{combined_context}
Respond in JSON format as a list of objects. Each object must contain the keys:
- "question": the text of the question,
- "options": an array of answer choices,
- "answer": the correct answer (which must be one of the options).

For example:
[
    {{
        "question": "What is the capital of France?",
        "options": ["Paris", "London", "Rome", "Berlin"],
        "answer": "Paris"
    }},
    {{
        "question": "Which planet is known as the Red Planet?",
        "options": ["Mars", "Venus", "Jupiter", "Saturn"],
        "answer": "Mars"
    }}
]
"""
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    response = llm.invoke(prompt)

    if hasattr(response, "content"):
        response = response.content.strip()
        fixed_string = fix_json_string(response)

    try:
        parsed_response = json.loads(fixed_string)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return MCQResponse(mcqs=parsed_response)

@app.post("/generate/flashcards", response_model=FlashcardResponse)
async def generate_flashcards(request: Request, flashcard_request: FlashcardRequest):
    """Generate flashcards from uploaded content."""
    session_id = await get_session_id(request)
    
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(
            status_code=404,
            detail="Please upload materials before generating flashcards."
        )

    # Aggregate content from all uploaded materials
    selected_indexes = SESSION_INDEX_CACHE[session_id]
    combined_context = ""
    for idx in selected_indexes:
        retriever = idx['index'].as_retriever()
        retrieved_docs = retriever.get_relevant_documents("summarize")
        for doc in retrieved_docs:
            combined_context += doc.page_content + "\n"

    # Construct the prompt for flashcard generation
    prompt = f"""
You are an AI assistant specialized in creating flashcards for learning.
Based on the following study material, generate {flashcard_request.num_flashcards} flashcards.
Each flashcard should consist of a 'question' that tests understanding of the material and an 'answer' providing a concise explanation.
Content:
{combined_context}
Respond in JSON format as a list of objects. Each object must contain the keys:
- "question": the flashcard question.
- "answer": the flashcard answer.

For example:
[
    {{
        "question": "What is photosynthesis?",
        "answer": "Photosynthesis is the process by which plants convert sunlight, water, and CO2 into energy."
    }},
    {{
        "question": "What is the capital of France?",
        "answer": "Paris is the capital of France."
    }}
]
"""

    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    response = llm.invoke(prompt)

    # If the response is an AIMessage, extract its content and fix formatting if necessary.
    if hasattr(response, "content"):
        response = response.content.strip()
        fixed_string = fix_json_string(response)
    else:
        fixed_string = response

    try:
        parsed_response = json.loads(fixed_string)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return FlashcardResponse(flashcards=parsed_response)

@app.get("/materials", response_model=MaterialsResponse)
async def get_materials(request: Request, response: Response):
    """
    Retrieve a list of all study materials uploaded in the current session.
    """
    session_id = await get_session_id(request)
    response.set_cookie(key="session_id", value=session_id)
    
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(status_code=404, detail='No content indexed in your session.')

    materials = [
        {"id": content["id"], "type": content["type"]}
        for content in SESSION_INDEX_CACHE[session_id]
    ]
    return MaterialsResponse(materials=materials)

@app.get("/transcript/{content_type}/{content_id}", response_model=TranscriptResponse)
async def get_transcript(
    request: Request,
    content_type: str,
    content_id: str
):
    """Retrieve the transcript for a YouTube video or audio file using its ID."""
    try:
        if content_type not in ["youtube", "audio"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid content type. Must be 'youtube' or 'audio'"
            )

        if content_type == "youtube":
            transcript_filename = f"{content_id}_youtube.txt"
        else:  # audio
            transcript_filename = f"{get_hash(content_id)}_audio.txt"

        transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)
      
        if not os.path.exists(transcript_path):
            raise HTTPException(
                status_code=404, 
                detail=f'Transcript file not found for {content_type} ID: {content_id}'
            )

        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_content = f.read()

        return TranscriptResponse(
            transcript=transcript_content,
            content_type=content_type,
            content_id=content_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f'Failed to retrieve transcript: {str(e)}'
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
