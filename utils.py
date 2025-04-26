import os
import re
import hashlib
import tempfile
from typing import Dict, Any, Optional
from langchain_community.document_loaders import (
    YoutubeLoader, TextLoader, PyPDFLoader,
    UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader,
    AssemblyAIAudioTranscriptLoader
)
from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from schemas import TranscriptResponse
from fastapi import HTTPException, Request

load_dotenv()


# Custom Exceptions
class FileProcessingError(Exception):
    """Base exception for file processing errors."""
    pass

class FileTypeError(FileProcessingError):
    """Raised when an unsupported file type is encountered."""
    pass

class FileNotFoundError(FileProcessingError):
    """Raised when a required file is not found."""
    pass

class IndexCreationError(FileProcessingError):
    """Raised when there's an error creating or loading an index."""
    pass

class YouTubeProcessingError(FileProcessingError):
    """Raised when there's an error processing a YouTube video."""
    pass

class AudioProcessingError(FileProcessingError):
    """Raised when there's an error processing an audio file."""
    pass

# Directory storage for persisted indexes and transcripts
BASE_DIR = "index_storage"
YOUTUBE_DIR = os.path.join(BASE_DIR, "youtube")
DOCUMENT_DIR = os.path.join(BASE_DIR, "document")
AUDIO_DIR = os.path.join(BASE_DIR, "audio")
TRANSCRIPT_DIR = os.path.join(BASE_DIR, "transcripts")

# Create necessary directories
try:
    os.makedirs(YOUTUBE_DIR, exist_ok=True)
    os.makedirs(DOCUMENT_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)
    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
except OSError as e:
    raise FileProcessingError(f"Failed to create storage directories: {str(e)}")

def get_hash(text: str) -> str:
    """
    Return a SHA256 hash of the given text.
    
    Args:
        text (str): The text to hash
        
    Returns:
        str: The SHA256 hash of the text
        
    Raises:
        FileProcessingError: If hashing fails
    """
    try:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
    except Exception as e:
        raise FileProcessingError(f"Failed to generate hash: {str(e)}")

def get_youtube_index_path(youtube_url: str) -> str:
    """
    Return the file path for a YouTube video's persisted index.
    
    Args:
        youtube_url (str): The YouTube URL
        
    Returns:
        str: The path to the index file
        
    Raises:
        FileProcessingError: If path generation fails
    """
    try:
        filename = f"{get_hash(youtube_url)}.faiss"
        return os.path.join(YOUTUBE_DIR, filename)
    except Exception as e:
        raise FileProcessingError(f"Failed to generate YouTube index path: {str(e)}")

def get_document_index_path(document_id: str) -> str:
    """
    Return the file path for a document's persisted index.
    
    Args:
        document_id (str): The document ID
        
    Returns:
        str: The path to the index file
        
    Raises:
        FileProcessingError: If path generation fails
    """
    try:
        filename = f"{get_hash(document_id)}.faiss"
        return os.path.join(DOCUMENT_DIR, filename)
    except Exception as e:
        raise FileProcessingError(f"Failed to generate document index path: {str(e)}")

def get_audio_index_path(audio_id: str) -> str:
    """
    Return the file path for an audio file's persisted index.
    
    Args:
        audio_id (str): The audio file ID
        
    Returns:
        str: The path to the index file
        
    Raises:
        FileProcessingError: If path generation fails
    """
    try:
        filename = f"{get_hash(audio_id)}.faiss"
        return os.path.join(AUDIO_DIR, filename)
    except Exception as e:
        raise FileProcessingError(f"Failed to generate audio index path: {str(e)}")

def fix_json_string(raw_string: str) -> str:
    """
    Fix JSON string formatting by removing unnecessary backslashes.
    
    Args:
        raw_string (str): The raw JSON string
        
    Returns:
        str: The fixed JSON string
        
    Raises:
        FileProcessingError: If string processing fails
    """
    try:
        return re.sub(r'\\+"', '"', raw_string)
    except Exception as e:
        raise FileProcessingError(f"Failed to fix JSON string: {str(e)}")

def save_transcript(content: str, source_id: str, source_type: str) -> str:
    """
    Saves transcript content to a text file.
    """
    try:
        os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
        
        if source_type == "youtube":
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(source_id)
            video_id = parse_qs(parsed_url.query).get('v', [''])[0]
            if not video_id:
                raise FileProcessingError("Could not extract video ID from URL")
            filename = f"{video_id}_{source_type}.txt"
        else:
            filename = f"{get_hash(source_id)}_{source_type}.txt"
            
        filepath = os.path.join(TRANSCRIPT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        if not os.path.exists(filepath):
            raise FileProcessingError("Failed to verify transcript file creation")
            
        return filepath
    except Exception as e:
        raise FileProcessingError(f"Failed to save transcript: {str(e)}")

def load_and_vectorize_youtube(youtube_url: str) -> Any:
    """
    Loads a YouTube video transcript and vectorizes it using FAISS.
    Also saves the transcript as a text file.
    """
    try:
        loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
        docs = loader.load()
        
        if not docs:
            raise YouTubeProcessingError("No content loaded from YouTube")
            
        transcript_content = "\n\n".join(doc.page_content for doc in docs)
        if not transcript_content.strip():
            raise YouTubeProcessingError("Empty transcript content")
            
        transcript_path = save_transcript(transcript_content, youtube_url, "youtube")
        
        embeddings = OpenAIEmbeddings()
        index = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=FAISS).from_documents(docs)
        return index
    except Exception as e:
        if "youtube" in str(e).lower():
            raise YouTubeProcessingError(f"Failed to process YouTube video: {str(e)}")
        raise IndexCreationError(f"Failed to create index for YouTube video: {str(e)}")

def load_and_vectorize_document(file_obj: Any, original_filename: str) -> Any:
    """
    Processes a document and indexes it using FAISS for retrieval.
    
    Args:
        file_obj: The file object to process
        original_filename (str): The original filename
        
    Returns:
        Any: The vectorized index
        
    Raises:
        FileTypeError: If file type is not supported
        FileProcessingError: If file processing fails
        IndexCreationError: If index creation fails
    """
    suffix = os.path.splitext(original_filename)[1].lower()
    if suffix not in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"]:
        raise FileTypeError(f"Unsupported file type: {suffix}")

    tmp_filename = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_obj.read())
            tmp_filename = tmp.name

        # Choose the appropriate loader based on file type
        if suffix == ".pdf":
            loader = PyPDFLoader(tmp_filename)
        elif suffix in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(tmp_filename)
        elif suffix in [".ppt", ".pptx"]:
            loader = UnstructuredPowerPointLoader(tmp_filename)
        elif suffix == ".txt":
            loader = TextLoader(tmp_filename)

        docs = loader.load()
        embeddings = OpenAIEmbeddings()
        index = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=FAISS).from_documents(docs)
        return index
    except Exception as e:
        if "file" in str(e).lower():
            raise FileProcessingError(f"Failed to process document: {str(e)}")
        raise IndexCreationError(f"Failed to create index for document: {str(e)}")
    finally:
        if tmp_filename and os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except OSError:
                pass

def load_and_vectorize_audio(file_obj: Any, original_filename: str) -> Any:
    suffix = os.path.splitext(original_filename)[1].lower()
    if suffix not in [".mp3", ".wav", ".m4a", ".ogg"]:
        raise FileTypeError(f"Unsupported audio file type: {suffix}")

    tmp_filename = None
    try:
        # Read bytes synchronously from the underlying file
        data = file_obj.file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(data)
            tmp_filename = tmp.name

        loader = AssemblyAIAudioTranscriptLoader(file_path=tmp_filename)
        docs = loader.load()

        transcript_content = "\n\n".join(doc.page_content for doc in docs)
        save_transcript(transcript_content, original_filename, "audio")

        embeddings = OpenAIEmbeddings()
        index = VectorstoreIndexCreator(
            embedding=embeddings,
            vectorstore_cls=FAISS
        ).from_documents(docs)
        return index

    except Exception as e:
        if "audio" in str(e).lower() or "transcript" in str(e).lower():
            raise AudioProcessingError(f"Failed to process audio file: {e}")
        raise IndexCreationError(f"Failed to create index for audio file: {e}")

    finally:
        if tmp_filename and os.path.exists(tmp_filename):
            try:
                os.remove(tmp_filename)
            except OSError:
                pass


def get_youtube_index(youtube_url: str) -> Dict[str, Any]:
    """
    Retrieves or creates a persisted YouTube index from disk.
    """
    try:
        # Extract video ID from URL
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(youtube_url)
        video_id = parse_qs(parsed_url.query).get('v', [''])[0]
        if not video_id:
            raise YouTubeProcessingError("Could not extract video ID from URL")

        index_path = get_youtube_index_path(youtube_url)
        embeddings = OpenAIEmbeddings()
        
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            return {"type": "youtube", "id": video_id, "index": vectorstore}
        else:
            index_obj = load_and_vectorize_youtube(youtube_url)
            index_obj.vectorstore.save_local(index_path)
            return {"type": "youtube", "id": video_id, "index": index_obj.vectorstore}
            
    except Exception as e:
        if "youtube" in str(e).lower():
            raise YouTubeProcessingError(f"Failed to process YouTube video: {str(e)}")
        raise IndexCreationError(f"Failed to create/load index for YouTube video: {str(e)}")

def get_document_index(document_id: str, file_obj: Optional[Any] = None, original_filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves or creates a persisted document index from disk.
    
    Args:
        document_id (str): The document ID
        file_obj: Optional file object for creating new index
        original_filename: Optional original filename
        
    Returns:
        Optional[Dict[str, Any]]: The index object with metadata or None
        
    Raises:
        FileTypeError: If file type is not supported
        FileProcessingError: If file processing fails
        IndexCreationError: If index creation or loading fails
    """
    try:
        index_path = get_document_index_path(document_id)
        embeddings = OpenAIEmbeddings()
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            return {"type": "document", "id": document_id, "index": vectorstore}
        elif file_obj and original_filename:
            index_obj = load_and_vectorize_document(file_obj, original_filename)
            index_obj.vectorstore.save_local(index_path)
            return {"type": "document", "id": document_id, "index": index_obj.vectorstore}
        else:
            return None
    except Exception as e:
        if "file" in str(e).lower():
            raise FileProcessingError(f"Failed to process document: {str(e)}")
        raise IndexCreationError(f"Failed to create/load index for document: {str(e)}")

def get_audio_index(audio_id: str, file_obj: Optional[Any] = None, original_filename: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieves or creates a persisted audio index from disk.
    
    Args:
        audio_id (str): The audio file ID
        file_obj: Optional file object for creating new index
        original_filename: Optional original filename
        
    Returns:
        Optional[Dict[str, Any]]: The index object with metadata or None
        
    Raises:
        FileTypeError: If file type is not supported
        AudioProcessingError: If audio processing fails
        IndexCreationError: If index creation or loading fails
    """
    try:
        index_path = get_audio_index_path(audio_id)
        embeddings = OpenAIEmbeddings()
        if os.path.exists(index_path):
            vectorstore = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
            return {"type": "audio", "id": audio_id, "index": vectorstore}
        elif file_obj and original_filename:
            index_obj = load_and_vectorize_audio(file_obj, original_filename)
            index_obj.vectorstore.save_local(index_path)
            return {"type": "audio", "id": audio_id, "index": index_obj.vectorstore}
        else:
            return None
    except Exception as e:
        if "audio" in str(e).lower() or "transcript" in str(e).lower():
            raise AudioProcessingError(f"Failed to process audio file: {str(e)}")
        raise IndexCreationError(f"Failed to create/load index for audio file: {str(e)}") 
