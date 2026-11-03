"""Loads the Hugging Face model and runs inference."""

from transformers import pipeline

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
MODEL_URL = f"https://huggingface.co/distilbert/{MODEL_NAME}"


class SentimentModel:
    def __init__(self) -> None:
        self._classifier = None

    @property
    def is_loaded(self) -> bool:
        return self._classifier is not None

    def load(self) -> None:
        self._classifier = pipeline("text-classification", model=f"distilbert/{MODEL_NAME}")

    def predict(self, text: str) -> dict:
        if self._classifier is None:
            raise RuntimeError("model is not loaded")
        # The model accepts at most 512 tokens, so longer inputs are truncated
        # instead of failing during inference.
        result = self._classifier(text, truncation=True)[0]
        return {"label": result["label"], "score": round(float(result["score"]), 4)}


sentiment_model = SentimentModel()
