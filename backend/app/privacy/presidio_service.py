from typing import Any

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine


class PresidioService:
    """
    Local PII detection and anonymization service.

    Microsoft Presidio runs locally and is used only for
    privacy processing. It is not an authorization authority.
    """

    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

    # ---------------------------------------------------------
    # PII DETECTION
    # ---------------------------------------------------------

    def analyze(
        self,
        text: str,
        language: str = "en",
    ) -> list[dict[str, Any]]:
        """
        Detect PII entities in text.

        Returns a serializable list of detected entities.
        """

        if not text:
            return []

        results = self.analyzer.analyze(
            text=text,
            language=language,
        )

        return [
            {
                "entity_type": result.entity_type,
                "start": result.start,
                "end": result.end,
                "score": result.score,
            }
            for result in results
        ]

    # ---------------------------------------------------------
    # PII ANONYMIZATION
    # ---------------------------------------------------------

    def anonymize(
        self,
        text: str,
        language: str = "en",
    ) -> str:
        """
        Detect and anonymize PII in text.
        """

        if not text:
            return text

        results = self.analyzer.analyze(
            text=text,
            language=language,
        )

        if not results:
            return text

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
        )

        return anonymized.text

    # ---------------------------------------------------------
    # DETECTION + ANONYMIZATION
    # ---------------------------------------------------------

    def protect_text(
        self,
        text: str,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Detect PII and return both the findings and
        anonymized text.
        """

        entities = self.analyze(
            text=text,
            language=language,
        )

        if not entities:
            return {
                "text": text,
                "pii_detected": False,
                "entities": [],
            }

        anonymized_text = self.anonymize(
            text=text,
            language=language,
        )

        return {
            "text": anonymized_text,
            "pii_detected": True,
            "entities": entities,
        }