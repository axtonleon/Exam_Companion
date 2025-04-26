from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from router import router

load_dotenv()

app = FastAPI(
    title="Exam Companion API",
    description="A powerful API that helps students and educators process, analyze, and generate questions from various study materials.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Redirect root URL to API documentation."""
    return RedirectResponse(url="/docs")

# Include router
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
