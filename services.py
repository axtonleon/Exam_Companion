import os
import json
from typing import List, Dict, Any
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from urllib.parse import urlparse, parse_qs

from utils import (
    get_youtube_index, get_document_index, get_audio_index,
    fix_json_string, get_hash, TRANSCRIPT_DIR
)
from schemas import (
    UploadResponse, QueryResponse, MCQResponse,
    FlashcardResponse, MaterialsResponse, TranscriptResponse
)

# Global cache: mapping session_id -> list of index objects
SESSION_INDEX_CACHE = {}

def process_youtube_upload(youtube_url: str, session_id: str) -> UploadResponse:
    """Process YouTube URL upload and return response."""
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
            
    SESSION_INDEX_CACHE[session_id].append({
        "type": "youtube",
        "id": video_id,
        "index": index_obj["index"]
    })
    
    return UploadResponse(
        message="Content uploaded successfully.",
        content_type="youtube",
        content_id=video_id
    )

def process_file_upload(file: Any, session_id: str) -> UploadResponse:
    """Process file upload and return response."""
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

def process_query(query: str, session_id: str) -> QueryResponse:
    """Process query and return response."""
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(status_code=404, detail="No content indexed in the session.")

    responses = []
    for content in SESSION_INDEX_CACHE[session_id]:
        llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6)
        retriever = content["index"].as_retriever()
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
        result = qa_chain.invoke({"query": query})
        responses.append(f"[{content['type']}:{content['id']}] {result}")
    
    return QueryResponse(answer="\n".join(responses))

def generate_mcqs(session_id: str, num_questions: int, difficulty: str) -> MCQResponse:
    """Generate MCQs from uploaded content."""
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(
            status_code=404,
            detail="Please upload materials before generating MCQs."
        )

    combined_context = _get_combined_context(session_id)
    prompt = _create_mcq_prompt(combined_context, num_questions, difficulty)
    
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

def generate_flashcards(session_id: str, num_flashcards: int) -> FlashcardResponse:
    """Generate flashcards from uploaded content."""
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(
            status_code=404,
            detail="Please upload materials before generating flashcards."
        )

    combined_context = _get_combined_context(session_id)
    prompt = _create_flashcard_prompt(combined_context, num_flashcards)
    
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)
    response = llm.invoke(prompt)

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

def get_materials_list(session_id: str) -> MaterialsResponse:
    """Get list of materials in session."""
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        raise HTTPException(status_code=404, detail='No content indexed in your session.')

    materials = [
        {"id": content["id"], "type": content["type"]}
        for content in SESSION_INDEX_CACHE[session_id]
    ]
    return MaterialsResponse(materials=materials)

def get_transcript_content(content_type: str, content_id: str) -> TranscriptResponse:
    """Get transcript content for specified material."""
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

def _get_combined_context(session_id: str) -> str:
    """Helper function to get combined context from all materials."""
    combined_context = ""
    for idx in SESSION_INDEX_CACHE[session_id]:
        retriever = idx['index'].as_retriever()
        retrieved_docs = retriever.get_relevant_documents("summarize")
        for doc in retrieved_docs:
            combined_context += doc.page_content + "\n"
    return combined_context

def _create_mcq_prompt(context: str, num_questions: int, difficulty: str) -> str:
    """Helper function to create MCQ generation prompt."""
    return f"""
    You are an AI assistant that generates multiple-choice questions from study material.
    Based on the following content, generate {num_questions} multiple-choice questions.
    Each question must have one correct answer and three plausible distractors.
    The questions should be at a {difficulty} difficulty level.
    Content:
    {context}
    Respond in JSON format as a list of objects. Each object must contain the keys:
    - "question": the text of the question,
    - "options": an array of answer choices,
    - "answer": the correct answer (which must be one of the options).
    """

def _create_flashcard_prompt(context: str, num_flashcards: int) -> str:
    """Helper function to create flashcard generation prompt."""
    return f"""
    You are an AI assistant specialized in creating flashcards for learning.
    Based on the following study material, generate {num_flashcards} flashcards.
    Each flashcard should consist of a 'question' that tests understanding of the material and an 'answer' providing a concise explanation.
    Content:
    {context}
    Respond in JSON format as a list of objects. Each object must contain the keys:
    - "question": the flashcard question.
    - "answer": the flashcard answer.
    """