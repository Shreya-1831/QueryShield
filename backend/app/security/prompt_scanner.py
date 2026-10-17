"""
QueryShield - Hybrid Prompt Security Scanner

Security layers:
1. Input validation
2. Deterministic security rules
3. Optional local NLP threat detection

The NLP detector is used in production.
Deterministic rules provide a fast, explainable security layer.

SQL authorization remains a separate security boundary.
"""

from dataclasses import dataclass, field
from enum import Enum
import re

from app.security.prompt_nlp_detector import detect_prompt_threat


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class PromptCategory(str, Enum):
    PROMPT_INJECTION = "PROMPT_INJECTION"
    SYSTEM_PROMPT_EXTRACTION = "SYSTEM_PROMPT_EXTRACTION"
    SECURITY_BYPASS = "SECURITY_BYPASS"
    SQL_INJECTION = "SQL_INJECTION"
    EMPTY_PROMPT = "EMPTY_PROMPT"
    EXCESSIVE_LENGTH = "EXCESSIVE_LENGTH"


@dataclass
class PromptScanResult:
    allowed: bool
    risk_level: RiskLevel
    categories: list[str] = field(default_factory=list)
    reason: str = ""
    nlp_confidence: float | None = None


MAX_PROMPT_LENGTH = 2000


# =========================================================
# PROMPT INJECTION RULES
# =========================================================

PROMPT_INJECTION_PATTERNS = [
    r"\bignore\s+(all\s+)?previous\s+instructions\b",
    r"\bignore\s+(all\s+)?prior\s+instructions\b",
    r"\bdisregard\s+(all\s+)?previous\s+instructions\b",
    r"\bdisregard\s+(all\s+)?prior\s+instructions\b",
    r"\bforget\s+(all\s+)?previous\s+instructions\b",
    r"\bforget\s+(all\s+)?prior\s+instructions\b",
    r"\bnew\s+instructions\b",
    r"\boverride\s+(the\s+)?instructions\b",
    r"\bdo\s+not\s+follow\s+(the\s+)?instructions\b",
]


# =========================================================
# SYSTEM PROMPT EXTRACTION RULES
# =========================================================

SYSTEM_PROMPT_PATTERNS = [
    r"\breveal\s+(the\s+)?system\s+prompt\b",
    r"\bshow\s+(me\s+)?(the\s+)?system\s+prompt\b",
    r"\bdisplay\s+(the\s+)?system\s+prompt\b",
    r"\bprint\s+(the\s+)?system\s+prompt\b",
    r"\bwhat\s+is\s+(your\s+)?system\s+prompt\b",
    r"\bshow\s+your\s+instructions\b",
    r"\breveal\s+your\s+instructions\b",
    r"\bwhat\s+are\s+your\s+instructions\b",
]


# =========================================================
# SECURITY BYPASS RULES
# =========================================================

SECURITY_BYPASS_PATTERNS = [
    r"\bbypass\s+(the\s+)?security\b",
    r"\bdisable\s+(the\s+)?security\b",
    r"\bdisable\s+(the\s+)?authorization\b",
    r"\bbypass\s+(the\s+)?authorization\b",
    r"\bignore\s+(the\s+)?access\s+control\b",
    r"\bignore\s+(the\s+)?permissions\b",
    r"\bskip\s+(the\s+)?permission\s+check\b",
    r"\bwithout\s+(any\s+)?permission\b",
    r"\bwithout\s+(any\s+)?authorization\b",
]


# =========================================================
# SQL INJECTION RULES
# =========================================================

SQL_INJECTION_PATTERNS = [
    r";\s*(drop|delete|truncate|alter|update|insert|create)\b",
    r"\bunion\s+(all\s+)?select\b",
    r"\bor\s+1\s*=\s*1\b",
    r"\band\s+1\s*=\s*1\b",
    r"'\s*or\s*'[^']*'\s*=\s*'[^']*'",
    r"--\s*$",
    r"/\*.*\*/",
]


# =========================================================
# HELPER
# =========================================================

def _matches_any(prompt: str, patterns: list[str]) -> bool:
    """
    Check whether any security pattern matches the prompt.
    """

    return any(
        re.search(
            pattern,
            prompt,
            flags=re.IGNORECASE | re.DOTALL,
        )
        for pattern in patterns
    )


# =========================================================
# MAIN SCANNER
# =========================================================

def scan_prompt(
    prompt: str,
    use_nlp: bool = True,
) -> PromptScanResult:
    """
    Scan a natural-language prompt.

    Parameters
    ----------
    prompt:
        User's natural-language query.

    use_nlp:
        Whether to use the local NLP threat detector.

        True:
            Production / full security scan.

        False:
            Deterministic unit testing without loading the NLP model.
    """

    # =====================================================
    # 1. INPUT VALIDATION
    # =====================================================

    if prompt is None:
        return PromptScanResult(
            allowed=False,
            risk_level=RiskLevel.HIGH,
            categories=[
                PromptCategory.EMPTY_PROMPT.value
            ],
            reason="Prompt cannot be empty.",
        )

    normalized_prompt = prompt.strip()

    if not normalized_prompt:
        return PromptScanResult(
            allowed=False,
            risk_level=RiskLevel.HIGH,
            categories=[
                PromptCategory.EMPTY_PROMPT.value
            ],
            reason="Prompt cannot be empty.",
        )

    if len(normalized_prompt) > MAX_PROMPT_LENGTH:
        return PromptScanResult(
            allowed=False,
            risk_level=RiskLevel.MEDIUM,
            categories=[
                PromptCategory.EXCESSIVE_LENGTH.value
            ],
            reason=(
                f"Prompt exceeds the maximum allowed length "
                f"of {MAX_PROMPT_LENGTH} characters."
            ),
        )

    # =====================================================
    # 2. DETERMINISTIC RULE ENGINE
    # =====================================================

    detected_categories: list[str] = []

    if _matches_any(
        normalized_prompt,
        PROMPT_INJECTION_PATTERNS,
    ):
        detected_categories.append(
            PromptCategory.PROMPT_INJECTION.value
        )

    if _matches_any(
        normalized_prompt,
        SYSTEM_PROMPT_PATTERNS,
    ):
        detected_categories.append(
            PromptCategory.SYSTEM_PROMPT_EXTRACTION.value
        )

    if _matches_any(
        normalized_prompt,
        SECURITY_BYPASS_PATTERNS,
    ):
        detected_categories.append(
            PromptCategory.SECURITY_BYPASS.value
        )

    if _matches_any(
        normalized_prompt,
        SQL_INJECTION_PATTERNS,
    ):
        detected_categories.append(
            PromptCategory.SQL_INJECTION.value
        )

    # =====================================================
    # 3. NLP THREAT DETECTION
    # =====================================================

    nlp_confidence = None

    if use_nlp:

        nlp_result = detect_prompt_threat(
            normalized_prompt
        )

        nlp_confidence = nlp_result.confidence

        if nlp_result.malicious:

            if (
                PromptCategory.PROMPT_INJECTION.value
                not in detected_categories
            ):
                detected_categories.append(
                    PromptCategory.PROMPT_INJECTION.value
                )

    # =====================================================
    # 4. SECURITY DECISION
    # =====================================================

    high_risk_categories = {
        PromptCategory.SQL_INJECTION.value,
        PromptCategory.SECURITY_BYPASS.value,
        PromptCategory.SYSTEM_PROMPT_EXTRACTION.value,
    }

    if detected_categories:

        if any(
            category in high_risk_categories
            for category in detected_categories
        ):
            risk_level = RiskLevel.HIGH

        else:
            risk_level = RiskLevel.MEDIUM

        return PromptScanResult(
            allowed=False,
            risk_level=risk_level,
            categories=detected_categories,
            reason="Prompt failed security validation.",
            nlp_confidence=nlp_confidence,
        )

    # =====================================================
    # 5. SAFE PROMPT
    # =====================================================

    return PromptScanResult(
        allowed=True,
        risk_level=RiskLevel.LOW,
        categories=[],
        reason="Prompt passed security validation.",
        nlp_confidence=nlp_confidence,
    )