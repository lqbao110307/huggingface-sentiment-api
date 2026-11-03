"""Request and response contracts of the API."""

from pydantic import BaseModel, Field, field_validator

MAX_TEXT_LENGTH = 2000


class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        description="English text to analyse.",
        max_length=MAX_TEXT_LENGTH,
        examples=["I absolutely love this product, it works perfectly!"],
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("text must not be empty or whitespace only")
        return cleaned


class PredictResponse(BaseModel):
    text: str = Field(..., description="The analysed text, after trimming whitespace.")
    label: str = Field(..., description="Predicted sentiment: POSITIVE or NEGATIVE.")
    score: float = Field(..., description="Model confidence for the label, from 0 to 1.")
    model: str = Field(..., description="Hugging Face model that produced the result.")


class HealthResponse(BaseModel):
    status: str
    model: str
    model_loaded: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | list[str]
