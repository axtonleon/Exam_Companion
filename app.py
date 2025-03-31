import os
import json
import uuid
from flask import Flask, request, jsonify, session
from flasgger import Swagger, swag_from
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from dotenv import load_dotenv

from utils import (
    get_youtube_index, get_document_index, get_audio_index,
    fix_json_string
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
swagger = Swagger(app)

# Global cache: mapping session_id -> list of index objects
SESSION_INDEX_CACHE = {}

def get_session_id():
    """Get or create a unique session ID for the current user session."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@app.route('/', methods=['GET'])
def home():
    """
    Home route that explains the API and provides a link to the Swagger UI.
    ---
    responses:
      200:
        description: API Information page.
    """
    info_html = """
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
        <a href="/apidocs" target="_blank">Swagger UI</a>
      </body>
    </html>
    """
    return info_html

@app.route('/upload', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Content uploaded and indexed successfully.',
            'examples': {
                'application/json': {
                    "message": "Content uploaded successfully.",
                    "content_type": "youtube/document/audio",
                    "content_id": "https://www.youtube.com/watch?v=abc123 or document_id or audio filename"
                }
            }
        },
        400: {'description': 'Missing content (youtube_url, file, or audio) in the request.'}
    },
    'consumes': ['multipart/form-data', 'application/json'],
    'parameters': [
        {
            'name': 'youtube_url',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'The YouTube URL to index.'
        },
        {
            'name': 'file',
            'in': 'formData',
            'type': 'file',
            'required': False,
            'description': 'A document or audio file to index.'
        },
        {
            'name': 'document_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Optional ID for the document/audio. Defaults to the filename if not provided.'
        }
    ],
    'tags': ['Upload']
})
def upload_content():
    """
    Uploads content (YouTube URL, document file, or audio file) and adds its index to the user's session.
    """
    session_id = get_session_id()
    if session_id not in SESSION_INDEX_CACHE:
        SESSION_INDEX_CACHE[session_id] = []

    if request.content_type.startswith("application/json"):
        data = request.get_json()
    elif request.content_type.startswith("multipart/form-data"):
        data = request.form.to_dict()
    else:
        data = {}

    # Check if a YouTube URL is provided
    if data and 'youtube_url' in data:
        youtube_url = data['youtube_url']
        try:
            index_obj = get_youtube_index(youtube_url)
            SESSION_INDEX_CACHE[session_id].append(index_obj)
            return jsonify({
                "message": "Content uploaded successfully.",
                "content_type": "youtube",
                "content_id": youtube_url
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Check for file upload (document or audio)
    if 'file' in request.files:
        file_obj = request.files['file']
        if file_obj.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        document_id = request.form.get('document_id', file_obj.filename)
        suffix = os.path.splitext(file_obj.filename)[1].lower()
        try:
            if suffix in [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".txt"]:
                index_obj = get_document_index(document_id, file_obj, file_obj.filename)
                content_type = "document"
            elif suffix in [".mp3", ".wav", ".m4a", ".ogg"]:
                index_obj = get_audio_index(document_id, file_obj, file_obj.filename)
                content_type = "audio"
            else:
                return jsonify({'error': 'Unsupported file type'}), 400

            if index_obj is None:
                return jsonify({"error": "Failed to index file."}), 500

            SESSION_INDEX_CACHE[session_id].append(index_obj)
            return jsonify({
                "message": "Content uploaded successfully.",
                "content_type": content_type,
                "content_id": document_id
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({'error': 'No content provided. Please supply a youtube_url or upload a file.'}), 400

@app.route('/query', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Combined answer from all uploaded content.',
            'examples': {
                'application/json': {
                    "answer": "Answer from video: ... \nAnswer from document: ..."
                }
            }
        },
        400: {'description': 'Missing query in the request.'},
        404: {'description': 'No content indexed in the session.'}
    },
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'example': 'What is this content about?'
                    }
                },
                'required': ['query']
            }
        }
    ],
    'tags': ['Query']
})
def query_content():
    """
    Runs a query across all content uploaded in the user's session.
    """
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing query in request body'}), 400

    session_id = get_session_id()
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        return jsonify({'error': 'No content indexed in your session.'}), 404

    query_text = data['query']
    responses = []

    try:
        # Run the query on each content index and aggregate responses.
        for content in SESSION_INDEX_CACHE[session_id]:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6)
            retriever = content["index"].as_retriever()
            qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
            result = qa_chain.invoke({"query": query_text})
            responses.append(f"[{content['type']}:{content['id']}] {result}")
        combined_response = "\n".join(responses)
        return jsonify({"answer": combined_response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate/mcq', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Multiple-choice questions generated successfully.',
            'examples': {
                'application/json': {
                    "mcqs": [
                        {
                            "question": "What is the capital of France?",
                            "options": ["Paris", "London", "Rome", "Berlin"],
                            "answer": "Paris"
                        }
                    ]
                }
            }
        },
        400: {'description': 'Invalid request payload.'},
        404: {'description': 'Please upload materials before generating MCQs.'}
    },
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'num_questions': {
                        'type': 'integer',
                        'example': 5
                    },
                    'difficulty': {
                        'type': 'string',
                        'example': "medium"
                    }
                }
            }
        }
    ],
    'tags': ['Generate MCQ']
})
def generate_mcq():
    data = request.get_json()
    num_questions = data.get('num_questions', 5)
    difficulty = data.get('difficulty', "medium")
    session_id = get_session_id()

    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        return jsonify({'error': 'Please upload materials before generating MCQs.'}), 404

    selected_indexes = SESSION_INDEX_CACHE[session_id]
    combined_context = ""
    for idx in selected_indexes:
        retriever = idx['index'].as_retriever()
        retrieved_docs = retriever.get_relevant_documents("summarize")
        for doc in retrieved_docs:
            combined_context += doc.page_content + "\n"

    prompt = f"""
You are an AI assistant that generates multiple-choice questions from study material.
Based on the following content, generate {num_questions} multiple-choice questions.
Each question must have one correct answer and three plausible distractors.
The questions should be at a {difficulty} difficulty level.
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
        return jsonify({"error": str(e)}), 500

    return jsonify({"mcqs": parsed_response})

@app.route('/generate/flashcards', methods=['POST'])
@swag_from({
    'responses': {
        200: {
            'description': 'Flashcards generated successfully.',
            'examples': {
                'application/json': {
                    "flashcards": [
                        {
                            "question": "What is photosynthesis?",
                            "answer": "Photosynthesis is the process by which plants convert sunlight, water, and CO2 into energy."
                        },
                        {
                            "question": "What is the capital of France?",
                            "answer": "Paris is the capital of France."
                        }
                    ]
                }
            }
        },
        400: {'description': 'Invalid request payload.'},
        404: {'description': 'Please upload materials before generating flashcards.'}
    },
    'parameters': [
        {
            'name': 'body',
            'in': 'body',
            'required': True,
            'schema': {
                'type': 'object',
                'properties': {
                    'num_flashcards': {
                        'type': 'integer',
                        'example': 5
                    }
                }
            }
        }
    ],
    'tags': ['Generate Flashcards']
})
def generate_flashcards():
    data = request.get_json()
    num_flashcards = data.get('num_flashcards', 5)
    session_id = get_session_id()

    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        return jsonify({'error': 'Please upload materials before generating flashcards.'}), 404

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
Based on the following study material, generate {num_flashcards} flashcards.
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
        return jsonify({"error": str(e)}), 500

    return jsonify({"flashcards": parsed_response})


@app.route('/materials', methods=['GET'])
def get_materials():
    """
    Retrieve a list of all study materials uploaded in the current session.
    ---
    responses:
      200:
        description: A list of uploaded materials with their IDs and types.
        examples:
          application/json: {
            "materials": [
              {"id": "https://www.youtube.com/watch?v=abc123", "type": "youtube"},
              {"id": "example_document.pdf", "type": "document"},
              {"id": "lecture_audio.mp3", "type": "audio"}
            ]
          }
      404:
        description: No content indexed in your session.
    tags:
      - Materials
    """
    session_id = get_session_id()
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        return jsonify({'error': 'No content indexed in your session.'}), 404

    materials = [
        {"id": content["id"], "type": content["type"]}
        for content in SESSION_INDEX_CACHE[session_id]
    ]
    return jsonify({"materials": materials})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
