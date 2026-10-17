"""
QueryShield - Local NLP Prompt Threat Detector

Development/interim implementation using:

    ProtectAI DeBERTa-v3-base Prompt Injection v2

The model is loaded entirely from the local filesystem.
No network access is required during inference.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
)


MODEL_PATH = (
    Path(__file__).resolve().parents[2]
    / "models"
    / "deberta-prompt-injection"
)

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)


@dataclass
class NLPDetectionResult:
    malicious: bool
    confidence: float
    label: str


@lru_cache(maxsize=1)
def _load_model():
    """
    Load tokenizer and model once.

    The model is loaded strictly from the local directory.
    """

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Prompt injection model not found: {MODEL_PATH}"
        )

    tokenizer = AutoTokenizer.from_pretrained(
        str(MODEL_PATH),
        local_files_only=True,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        str(MODEL_PATH),
        local_files_only=True,
        use_safetensors=True,
    )

    model.to(DEVICE)
    model.eval()

    print(
        f"QueryShield Prompt Detector loaded on: {DEVICE}"
    )

    return tokenizer, model


def detect_prompt_threat(
    prompt: str,
) -> NLPDetectionResult:
    """
    Detect prompt injection using the local classifier.
    """

    if not isinstance(prompt, str):
        return NLPDetectionResult(
            malicious=True,
            confidence=1.0,
            label="INVALID",
        )

    prompt = prompt.strip()

    if not prompt:
        return NLPDetectionResult(
            malicious=False,
            confidence=1.0,
            label="SAFE",
        )

    tokenizer, model = _load_model()

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512,
    )

    inputs = {
        key: value.to(DEVICE)
        for key, value in inputs.items()
    }

    with torch.no_grad():
        outputs = model(**inputs)

    probabilities = torch.softmax(
        outputs.logits,
        dim=-1,
    )[0]

    predicted_class = int(
        torch.argmax(probabilities).item()
    )

    confidence = float(
        probabilities[predicted_class].item()
    )

    label = model.config.id2label.get(
        predicted_class,
        str(predicted_class),
    ).upper()

    malicious = label == "INJECTION"

    return NLPDetectionResult(
        malicious=malicious,
        confidence=confidence,
        label=label,
    )