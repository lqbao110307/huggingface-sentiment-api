"""FastAPI application exposing a Hugging Face sentiment analysis model."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.model import MODEL_NAME, MODEL_URL, sentiment_model
from app.schemas import ErrorResponse, HealthResponse, PredictRequest, PredictResponse

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # A failed load keeps the server up so /health can report the problem.
    try:
        sentiment_model.load()
        logger.info("Model loaded: %s", MODEL_NAME)
    except Exception:
        logger.exception("Could not load model: %s", MODEL_NAME)
    yield


app = FastAPI(
    title="Hugging Face Sentiment Analysis API",
    description=f"Classifies English text as POSITIVE or NEGATIVE using {MODEL_NAME}.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Report missing or malformed input in the same format as other errors."""
    details = []
    for error in exc.errors():
        # For malformed JSON, the location holds a character offset rather than a field name.
        field = "body" if error["type"] == "json_invalid" else ".".join(
            str(part) for part in error["loc"] if part != "body"
        ) or "body"
        details.append(f"{field}: {error['msg']}")
    body = ErrorResponse(error="Invalid input", detail=details)
    return JSONResponse(status_code=422, content=body.model_dump())


@app.get("/")
def read_root() -> dict:
    return {
        "name": app.title,
        "description": "Send English text to POST /predict to get its sentiment.",
        "model": MODEL_NAME,
        "model_url": MODEL_URL,
        "endpoints": {
            "GET /": "Introduction to the API",
            "GET /health": "Operational status of the system",
            "POST /predict": 'Sentiment of a text, for example {"text": "I love it"}',
            "GET /docs": "Interactive API documentation",
        },
    }


@app.get("/health", response_model=HealthResponse, responses={503: {"model": HealthResponse}})
def read_health() -> JSONResponse:
    loaded = sentiment_model.is_loaded
    body = HealthResponse(
        status="ok" if loaded else "unavailable",
        model=MODEL_NAME,
        model_loaded=loaded,
    )
    return JSONResponse(status_code=200 if loaded else 503, content=body.model_dump())


# Declared with `def` so FastAPI runs the blocking inference in a worker thread.
@app.post(
    "/predict",
    response_model=PredictResponse,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
def predict(request: PredictRequest) -> PredictResponse | JSONResponse:
    if not sentiment_model.is_loaded:
        body = ErrorResponse(error="Model unavailable", detail="The model could not be loaded.")
        return JSONResponse(status_code=503, content=body.model_dump())

    try:
        result = sentiment_model.predict(request.text)
    except Exception:
        logger.exception("Inference failed")
        body = ErrorResponse(error="Inference failed", detail="The model could not process this input.")
        return JSONResponse(status_code=500, content=body.model_dump())

    return PredictResponse(text=request.text, model=MODEL_NAME, **result)
