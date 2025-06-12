from typing import List, Optional, Dict
from pydantic import BaseModel, Field, HttpUrl

class UploadResponse(BaseModel):
    message: str
    content_type: str
    content_id: str

class QueryRequest(BaseModel):
    query: str = Field(..., example="What is this content about?")

class QueryResponse(BaseModel):
    answer: str

class MCQRequest(BaseModel):
    num_questions: int = Field(default=5, example=5)
    difficulty: str = Field(default="medium", example="medium")

class MCQOption(BaseModel):
    question: str
    options: List[str]
    answer: str

class MCQResponse(BaseModel):
    mcqs: List[MCQOption]

class FlashcardRequest(BaseModel):
    num_flashcards: int = Field(default=5, example=5)

class Flashcard(BaseModel):
    question: str
    answer: str

class FlashcardResponse(BaseModel):
    flashcards: List[Flashcard]

class TranscriptResponse(BaseModel):
    transcript: str
    content_type: str
    content_id: str

class ErrorResponse(BaseModel):
    error: str

class MaterialsResponse(BaseModel):
    materials: List[Dict[str, str]]
    
    
class SummaryResponse(BaseModel):
    summary: dict
    
