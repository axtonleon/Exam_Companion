from fastapi import APIRouter, File, UploadFile, Request, Response, HTTPException
from typing import Optional
import uuid

from schemas import (
    UploadResponse, QueryRequest, QueryResponse,
    MCQRequest, MCQResponse, FlashcardRequest,
    FlashcardResponse, MaterialsResponse, TranscriptResponse
)
from services import (
    process_youtube_upload, process_file_upload, process_query,
    generate_mcqs, generate_flashcards, get_materials_list,
    get_transcript_content, SESSION_INDEX_CACHE
)

router = APIRouter()

async def get_session_id(request: Request) -> str:
    """Get or create a unique session ID for the current user session."""
    if not request.cookies.get("session_id"):
        return str(uuid.uuid4())
    return request.cookies.get("session_id")

@router.post("/upload", response_model=UploadResponse, tags=["upload"])
async def upload_content(
    request: Request,
    response: Response,
    youtube_url: Optional[str] = File(None),
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
            return process_youtube_upload(youtube_url, session_id)
        return process_file_upload(file, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query", response_model=QueryResponse, tags=["query"])
async def query_content(
    request: Request,
    response: Response,
    query_request: QueryRequest
):
    """Query all content uploaded in the session."""
    session_id = await get_session_id(request)
    response.set_cookie(key="session_id", value=session_id)
    return process_query(query_request.query, session_id)

@router.post("/generate/mcq", response_model=MCQResponse, tags=["generate"])
async def generate_mcq(request: Request, mcq_request: MCQRequest):
    """Generate multiple-choice questions from uploaded content."""
    session_id = await get_session_id(request)
    return generate_mcqs(session_id, mcq_request.num_questions, mcq_request.difficulty)

@router.post("/generate/flashcards", response_model=FlashcardResponse, tags=["generate"])
async def generate_flashcards_endpoint(request: Request, flashcard_request: FlashcardRequest):
    """Generate flashcards from uploaded content."""
    session_id = await get_session_id(request)
    return generate_flashcards(session_id, flashcard_request.num_flashcards)

@router.get("/materials", response_model=MaterialsResponse, tags=["materials"])
async def get_materials(request: Request, response: Response):
    """Retrieve a list of all study materials uploaded in the current session."""
    session_id = await get_session_id(request)
    response.set_cookie(key="session_id", value=session_id)
    return get_materials_list(session_id)

@router.get("/transcript/{content_type}/{content_id}", response_model=TranscriptResponse, tags=["materials"])
async def get_transcript(
    request: Request,
    content_type: str,
    content_id: str
):
    """Retrieve the transcript for a YouTube video or audio file using its ID."""
    return get_transcript_content(content_type, content_id)