# Exam Companion

A powerful Flask-based API that helps students and educators process, analyze, and generate questions from various study materials including YouTube videos, PDFs, Word documents, and PowerPoint presentations.

## Features

- **Multi-Content Processing**: Upload and process various types of study materials:

  - YouTube videos (with transcript extraction)
  - PDF documents
  - Word documents (DOCX)
  - PowerPoint presentations (PPTX)
  - Text files

- **Intelligent Querying**: Ask questions about your study materials and get AI-powered answers

- **MCQ Generation**: Automatically generate multiple-choice questions from your study materials

- **Session Management**: Maintain separate sessions for different users

- **API Documentation**: Built-in Swagger UI for easy API exploration and testing

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- pip (Python package manager)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd Exam_Companion
```

2. Create and activate a virtual environment (recommended):

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Unix/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your OpenAI API key:

```
OPENAI_API_KEY=your-api-key-here
```

## Usage

1. Start the Flask server:

```bash
python app.py
```

2. Open your web browser and navigate to:

```
http://localhost:5000
```

3. Access the Swagger UI documentation at:

```
http://localhost:5000/apidocs
```

## API Endpoints

### 1. Upload Content

- **Endpoint**: `/upload`
- **Method**: POST
- **Content Types**: multipart/form-data, application/json
- **Parameters**:
  - `youtube_url` (optional): YouTube video URL
  - `file` (optional): Document file (PDF, DOCX, PPTX, TXT)
  - `document_id` (optional): Custom ID for the document

### 2. Query Content

- **Endpoint**: `/query`
- **Method**: POST
- **Content Type**: application/json
- **Parameters**:
  - `query`: Your question about the uploaded content

### 3. Generate MCQs

- **Endpoint**: `/generate/mcq`
- **Method**: POST
- **Content Type**: application/json
- **Parameters**:
  - `num_questions`: Number of questions to generate
  - `difficulty`: Difficulty level (e.g., "easy", "medium", "hard")

### 4. List Materials

- **Endpoint**: `/materials`
- **Method**: GET
- **Returns**: List of all uploaded materials in the current session

## Example Usage

### Upload a YouTube Video

```bash
curl -X POST http://localhost:5000/upload \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=example"}'
```

### Upload a Document

```bash
curl -X POST http://localhost:5000/upload \
  -F "file=@/path/to/your/document.pdf" \
  -F "document_id=my_document"
```

### Query Content

```bash
curl -X POST http://localhost:5000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main topics covered?"}'
```

### Generate MCQs

```bash
curl -X POST http://localhost:5000/generate/mcq \
  -H "Content-Type: application/json" \
  -d '{"num_questions": 5, "difficulty": "medium"}'
```

## Security Considerations

- Store your OpenAI API key securely in the `.env` file
- Never commit the `.env` file to version control
- The application uses session-based authentication for managing user sessions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request



## Acknowledgments

- OpenAI for providing the GPT models
- LangChain for the document processing framework
- Flask and its extensions for the web framework
