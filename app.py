import os
import re
import tempfile
import json
import hashlib
import uuid
from flask import Flask, request, jsonify, session
from flasgger import Swagger, swag_from
from langchain_community.document_loaders import YoutubeLoader,TextLoader,PyPDFLoader, UnstructuredWordDocumentLoader, UnstructuredPowerPointLoader

from langchain.indexes import VectorstoreIndexCreator
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import FAISS
import constants

# Set your OpenAI API key
os.environ["OPENAI_API_KEY"] = constants.APIKEY

app = Flask(__name__)
# A secret key is required for session handling
app.secret_key = 'your-very-secret-key'
swagger = Swagger(app)

# Directory storage for persisted indexes
BASE_DIR = "index_storage"
YOUTUBE_DIR = os.path.join(BASE_DIR, "youtube")
DOCUMENT_DIR = os.path.join(BASE_DIR, "document")
os.makedirs(YOUTUBE_DIR, exist_ok=True)
os.makedirs(DOCUMENT_DIR, exist_ok=True)

# Global cache: mapping session_id -> list of index objects
# Each index object is a dictionary with keys: "type" (youtube/document),
# "id" (unique identifier), and "index" (the persisted index)
SESSION_INDEX_CACHE = {}

def get_hash(text):
    """Return a SHA256 hash of the given text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def get_youtube_index_path(youtube_url):
    """Return the file path for a YouTube video's persisted index."""
    filename = f"{get_hash(youtube_url)}.faiss"
    return os.path.join(YOUTUBE_DIR, filename)

def get_document_index_path(document_id):
    """Return the file path for a document's persisted index."""
    filename = f"{get_hash(document_id)}.faiss"
    return os.path.join(DOCUMENT_DIR, filename)

def fix_json_string(raw_string):
    # Remove any backslashes that precede a double quote
    fixed = re.sub(r'\\+"', '"', raw_string)
    return fixed

def load_and_vectorize_youtube(youtube_url):
    """Loads a YouTube video transcript and vectorizes it using FAISS."""
    loader = YoutubeLoader.from_youtube_url(youtube_url, add_video_info=False)
    docs = loader.load()
    embeddings = OpenAIEmbeddings()
    index = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=FAISS).from_documents(docs)
    return index

def load_and_vectorize_document(file_obj, original_filename):
    """Processes a document (PDF, DOCX, PPTX, TXT) and indexes it using FAISS for retrieval."""
    suffix = os.path.splitext(original_filename)[1].lower()  # Extracts file extension

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

    # Load document contents
    docs = loader.load()

    # Create embeddings and FAISS index
    embeddings = OpenAIEmbeddings()
    index = VectorstoreIndexCreator(embedding=embeddings, vectorstore_cls=FAISS).from_documents(docs)

    # Cleanup: remove temporary file
    os.remove(tmp_filename)

    return index

def get_youtube_index(youtube_url):
    """Retrieves or creates a persisted YouTube index from disk."""
    index_path = get_youtube_index_path(youtube_url)
    embeddings = OpenAIEmbeddings()
    if os.path.exists(index_path):
        vectorstore = FAISS.load_local(index_path, embeddings,allow_dangerous_deserialization=True)
        # Wrap it in a simple dict so we can access .vectorstore later
        return {"type": "youtube", "id": youtube_url, "index": vectorstore}
    else:
        index_obj = load_and_vectorize_youtube(youtube_url)
        index_obj.vectorstore.save_local(index_path)
        return {"type": "youtube", "id": youtube_url, "index": index_obj.vectorstore}

def get_document_index(document_id, file_obj=None, original_filename=None):
    """
    Retrieves or creates a persisted document index from disk.
    If the index does not exist and file_obj is provided, it creates and saves the index.
    """
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
        <p>This API allows you to upload content (YouTube videos or documents such as PPT, PDF, DOC) and query them.</p>
        <ul>
          <li><b>/upload</b>: Upload a YouTube URL or a document. Uploaded content is associated with your session.</li>
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
                    "content_type": "youtube",
                    "content_id": "https://www.youtube.com/watch?v=abc123"
                }
            }
        },
        400: {'description': 'Missing content (youtube_url or file) in the request.'}
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
            'description': 'A document file (PPT, PDF, DOC) to index.'
        },
        {
            'name': 'document_id',
            'in': 'formData',
            'type': 'string',
            'required': False,
            'description': 'Optional ID for the document. Defaults to the filename if not provided.'
        }
    ],
    'tags': ['Upload']
})
def upload_content():
    """
    Uploads content (YouTube URL or document file) and adds its index to the user's session.
    """
    session_id = get_session_id()
    if session_id not in SESSION_INDEX_CACHE:
        SESSION_INDEX_CACHE[session_id] = []  # initialize a list for this session

    # Check if a JSON payload with a YouTube URL was provided
    # Determine the content type and extract data accordingly
    if request.content_type.startswith("application/json"):
        data = request.get_json()
    elif request.content_type.startswith("multipart/form-data"):
        data = request.form.to_dict()
    else:
        data = {}

    if data and 'youtube_url' in data:
        youtube_url = data['youtube_url']
        try:
            index_obj = get_youtube_index(youtube_url)
            # Initialize session cache if not already present
            if session_id not in SESSION_INDEX_CACHE:
                SESSION_INDEX_CACHE[session_id] = []
            SESSION_INDEX_CACHE[session_id].append(index_obj)
            return jsonify({
                "message": "Content uploaded successfully.",
                "content_type": "youtube",
                "content_id": youtube_url
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Otherwise, check for a file upload (multipart/form-data)
    if 'file' in request.files:
        file_obj = request.files['file']
        if file_obj.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        document_id = request.form.get('document_id', file_obj.filename)
        try:
            index_obj = get_document_index(document_id, file_obj, file_obj.filename)
            if index_obj is None:
                return jsonify({"error": "Failed to index document."}), 500
            SESSION_INDEX_CACHE[session_id].append(index_obj)
            return jsonify({
                "message": "Content uploaded successfully.",
                "content_type": "document",
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
        # For each uploaded content index, run the query and store the response
        for content in SESSION_INDEX_CACHE[session_id]:
            llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.6)
            retriever = content["index"].as_retriever()
            qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=retriever)
            result = qa_chain.invoke({"query": query_text})
            responses.append(f"[{content['type']}:{content['id']}] {result}")
        # Combine responses from each content source
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

    # Check if there are any uploaded materials in the session.
    if session_id not in SESSION_INDEX_CACHE or not SESSION_INDEX_CACHE[session_id]:
        return jsonify({'error': 'Please upload materials before generating MCQs.'}), 404

    # Use all materials in the session
    selected_indexes = SESSION_INDEX_CACHE[session_id]

    combined_context = ""
    # Retrieve context from each indexed material
    for idx in selected_indexes:
        retriever = idx['index'].as_retriever()
        retrieved_docs = retriever.get_relevant_documents("summarize")
        for doc in retrieved_docs:
            combined_context += doc.page_content + "\n"

    # Construct the AI prompt directly for LLM invocation.
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
    
    # If response is an AIMessage, extract its content.
    if hasattr(response, "content"):
        response = response.content.strip()
        fixed_string = fix_json_string(response)
    # Attempt to parse the response string as JSON.
    try:
        parsed_response = json.loads(fixed_string)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"mcqs": parsed_response})



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
              {"id": "example_document.pdf", "type": "document"}
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

    # Create a list of materials with their id and type.
    materials = [
        {"id": content["id"], "type": content["type"]}
        for content in SESSION_INDEX_CACHE[session_id]
    ]
    return jsonify({"materials": materials})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
