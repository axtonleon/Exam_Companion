import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import HTTPException
from langchain_openai import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from urllib.parse import urlparse, parse_qs
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from utils import (
    get_youtube_index, get_document_index, get_audio_index,
    fix_json_string, get_hash, TRANSCRIPT_DIR, text_splitter, _get_content_filepath
)
from schemas import (
    UploadResponse, QueryResponse, MCQResponse,
    FlashcardResponse, MaterialsResponse, TranscriptResponse, SummaryResponse
)

logging.basicConfig(level=logging.DEBUG)

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

async def process_file_upload(file: Any, session_id: str) -> UploadResponse:
    """Process file upload and return response."""
    if file.filename == '':
        raise HTTPException(status_code=400, detail="No file selected")

    document_id = file.filename
    
    suffix = os.path.splitext(file.filename)[1].lower()

    if suffix in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"]:
        index_obj = await get_document_index(document_id, file, file.filename)
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
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.6)
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
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.6)
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
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.6)
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
        transcript_filename = f"{content_id}_audio.txt"

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
    


def standardize_json_response(response: str) -> dict:
    """Helper function to standardize any JSON output from LLM responses.
    Args:
        response (str): The raw response string from the LLM
        
    Returns:
        dict: Standardized JSON structure, always returns a dictionary
        
    Raises:
        HTTPException: If the response cannot be parsed into valid JSON
    """
    try:
        # Remove any markdown code block indicators and extra whitespace
        cleaned_response = response.strip()
        if cleaned_response.startswith("```"):
            # Remove language identifier if present
            first_newline = cleaned_response.find('\n')
            if first_newline != -1:
                cleaned_response = cleaned_response[first_newline:].strip()
            # Remove ending ```
            cleaned_response = cleaned_response.replace("```", "").strip()
        
        def ensure_dict(data):
            """Helper function to ensure the result is a dictionary."""
            if isinstance(data, dict):
                return data
            return {"content": data}
        
        def extract_json_content(data):
            """Helper function to extract actual JSON content from nested structures."""
            if isinstance(data, dict):
                # If there's a single key with a string value that looks like JSON
                if len(data) == 1:
                    key, value = next(iter(data.items()))
                    if isinstance(value, str):
                        # Try to parse the string as JSON
                        try:
                            parsed = json.loads(value)
                            # If successful, return the parsed content
                            return ensure_dict(parsed)
                        except json.JSONDecodeError:
                            pass
                # If no single JSON string found, process all values
                return {k: extract_json_content(v) for k, v in data.items()}
            elif isinstance(data, list):
                return {"content": [extract_json_content(item) for item in data]}
            return ensure_dict(data)
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(cleaned_response)
            # Extract actual content from nested structures
            result = extract_json_content(parsed_json)
            # If the result is still a dict with a single 'summary' key, extract its value
            if isinstance(result, dict) and len(result) == 1 and 'summary' in result:
                if isinstance(result['summary'], str):
                    try:
                        return ensure_dict(json.loads(result['summary']))
                    except json.JSONDecodeError:
                        return {"content": result['summary']}
                return ensure_dict(result['summary'])
            return ensure_dict(result)
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from the text
            # Look for JSON-like structure between curly braces
            start_idx = cleaned_response.find('{')
            end_idx = cleaned_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = cleaned_response[start_idx:end_idx + 1]
                parsed_json = json.loads(json_str)
                result = extract_json_content(parsed_json)
                # Handle the same summary case as above
                if isinstance(result, dict) and len(result) == 1 and 'summary' in result:
                    if isinstance(result['summary'], str):
                        try:
                            return ensure_dict(json.loads(result['summary']))
                        except json.JSONDecodeError:
                            return {"content": result['summary']}
                    return ensure_dict(result['summary'])
                return ensure_dict(result)
            else:
                # If no JSON structure found, return the cleaned response as content
                return {"content": cleaned_response}
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse response: {str(e)}"
        )

async def generate_summary(content_type: str, content_id: str) -> SummaryResponse:
    """
    Generates a structured summary from uploaded content using a robust two-step process.
    Step 1: Create a high-quality text summary using map-reduce.
    Step 2: Format that text summary into the desired JSON structure.
    """
    # if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
    #     raise HTTPException(
    #         status_code=404,
    #         detail="Please upload materials before generating a summary."
    #     )
    transcript_filename = f"{content_id}_{content_type}.txt"
    logging.info(f"DEBUG: Looking for transcript file: {transcript_filename}") # For debugging
    transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_filename)

    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_content = f.read()
    # Load all content chunks from saved text files
    
    docs = [Document(page_content=transcript_content, metadata={"source": f"{content_type}:{content_id}"})]
    logging.info(f"DEBUG: Total chunks loaded for summary: {len(docs)}")

    if not docs:
        raise HTTPException(
            status_code=404,
            detail="No content could be loaded for summarisation. Check if text files were saved during upload."
        )

    # Use a lower temperature for factual summaries and a different one for formatting
    summarization_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2)
    formatting_llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)

    # --- STEP 1: Get the high-quality TEXT summary using map-reduce ---
    logging.info("Starting Step 1: Generating text summary with map-reduce...")
    try:
        # Create the chain with prompts that ask for TEXT, not JSON.
        summarize_chain = load_summarize_chain(
            llm=summarization_llm,
            chain_type="map_reduce",
            map_prompt=_create_text_map_prompt(),
            combine_prompt=_create_text_combine_prompt(),
            verbose=True # Helpful for debugging
        )

        # Run the chain. The result is a dictionary.
        summary_result = await summarize_chain.ainvoke(docs)
        
        # Extract the final text summary from the result dictionary.
        summary_text = summary_result['output_text']
        logging.info(f"DEBUG: Text summary: {summary_text}") # For debugging    

    except Exception as e:
        logging.info(f"Error during map-reduce text summarizatio:n: {e}")
        raise HTTPException(status_code=500, detail=f"LLM text summarisation failed: {e}")


    # --- STEP 2: Format the text summary into JSON ---
    logging.info("Starting Step 2: Formatting text summary into JSON...")
    try:
        # Create the second prompt, feeding it the `summary_text` from Step 1.
        format_prompt = _create_json_formatting_prompt(summary_text)

        # Make a separate, simple LLM call for the formatting task.
        json_response_obj = await formatting_llm.ainvoke(format_prompt)
        response_content = json_response_obj.content
        if "```json\n" in response_content:
            response_content = response_content.split("```json\n")[1]
        if "\n```" in response_content:
            response_content = response_content.split("\n```")[0]
            
        response_content = json.loads(response_content)
        # Use your robust parser to clean and load the JSON string.
        
        logging.info(f"DEBUG: Final JSON summary: {response_content}") # For debugging
        
        # Return the final, structured response.
        return SummaryResponse(summary=response_content)

    except HTTPException as e:
        # Pass through exceptions from your JSON parser
        raise e
    except Exception as e:
        print(f"Error during JSON formatting: {e}")
        # If formatting fails, you could return the plain text as a fallback
        # or raise an error. Raising an error is often better for debugging.
        raise HTTPException(
            status_code=500,
            detail=f"Failed to format summary text into JSON. Raw text available for debugging.",
            headers={"X-Raw-Summary-Text": summary_text[:1000]} # Send text snippet in header
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
    



def _create_text_map_prompt() -> PromptTemplate:
    """
    Prompt for Step 1 (Map): Summarizes a single chunk of text into plain text.
    Asks the LLM to focus on content extraction, not formatting.
    """
    template = """
    You are an expert at summarizing study material.
    The following is a chunk of a larger document. Create a detailed summary of this specific chunk.
    Extract all key facts, definitions, concepts, and main points.

    Chunk:
    "{text}"

    DETAILED SUMMARY OF THIS CHUNK:
    """
    return PromptTemplate(template=template, input_variables=["text"])

def _create_text_combine_prompt() -> PromptTemplate:
    """
    Step 1 (Combine): Synthesizes chunk summaries into a structured Markdown summary.
    This version asks for nested bullet points for richer detail.
    """
    template = """
    You are an expert at synthesizing information. The following are summaries from different parts of a study guide.
    Your task is to create a single, unified, and comprehensive summary from them.

    Structure your final summary using Markdown headings for clarity:
    - Start with a "## Overview" section.
    - Create several "## [Descriptive Section Title]" sections for the main topics.
    - Create a "## Key Concepts" section. For each concept:
        - Start with the concept name as a main bullet point.
        - Underneath, create a nested bullet point for "Definition:" with detailed points.
        - Underneath, create another nested bullet point for "Importance:" with detailed points.
    - End with a "## Conclusion" section.

    Ensure a logical flow and smooth transitions between sections.

    EXAMPLE for Key Concepts section:
    ## Key Concepts
    - Photosynthesis
        - Definition:
            - A process used by plants, algae, and some bacteria.
            - Converts light energy into chemical energy.
            - Utilizes water, carbon dioxide, and sunlight.
        - Importance:
            - Forms the base of most food chains.
            - Produces oxygen, which is essential for aerobic life.
            - Plays a crucial role in the global carbon cycle.

    Summaries:
    "{text}"

    FINAL COMPREHENSIVE SUMMARY (IN MARKDOWN):
    """
    return PromptTemplate(template=template, input_variables=["text"])

def _create_json_formatting_prompt(summary_text: str) -> str:
    """
    Step 2: Formats the Markdown summary (with nested bullets) into the desired JSON.
    This version expects 'definition' and 'importance' to be lists of strings.
    """
    return f"""
    You are a data formatting expert. Your task is to convert the provided text summary into a single, valid JSON object.
    Do not add any text, explanations, or apologies before or after the JSON.
    The text is structured with Markdown headings (##) and nested bullet points. Use these to populate the JSON.

    - The content under "## Overview" goes into the `overview` key as a single string.
    - Each "## [Section Title]" and its content goes into an object in the `sections` list.
    - The content under "## Conclusion" goes into the `conclusion` key as a single string.
    - For the "## Key Concepts" section:
        - Each main bullet point becomes an object in the `key_concepts` list.
        - The text of the main bullet is the `concept` name.
        - All nested bullet points under "Definition:" must be gathered into a LIST of strings for the `definition` key.
        - All nested bullet points under "Importance:" must be gathered into a LIST of strings for the `importance` key.

    <TEXT_SUMMARY_TO_CONVERT>
    {summary_text}
    </TEXT_SUMMARY_TO_CONVERT>

    <REQUIRED_JSON_STRUCTURE_AND_EXAMPLE>
    {{
        "overview": "...",
        "sections": [{{ "heading": "...", "content": "..." }}],
        "key_concepts": [
            {{
                "concept": "Photosynthesis",
                "definition": [
                    "A process used by plants, algae, and some bacteria.",
                    "Converts light energy into chemical energy.",
                    "Utilizes water, carbon dioxide, and sunlight."
                ],
                "importance": [
                    "Forms the base of most food chains.",
                    "Produces oxygen, which is essential for aerobic life.",
                    "Plays a crucial role in the global carbon cycle."
                ]
            }}
        ],
        "conclusion": "..."
    }}
    </REQUIRED_JSON_STRUCTURE_AND_EXAMPLE>
    """