from fastapi import FastAPI

app = FastAPI(
    title="Adaptive Assessment Platform",
    description="Backend API for the Adaptive RAG-Powered Assessment & Learning Platform",
    version="0.1.0",
)


@app.get("/")
def read_root():
    """Basic root endpoint to confirm the API is running."""
    return {"message": "Adaptive Assessment Platform API is running"}