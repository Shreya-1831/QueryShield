from dataclasses import dataclass
from enum import Enum


class QueryIntent(str, Enum):
    PERSONAL_INFORMATION = "personal_information"
    EMPLOYEE_SEARCH = "employee_search"
    AGGREGATION = "aggregation"
    COMPARISON = "comparison"
    ANALYTICS = "analytics"
    SALARY = "salary"
    DEPARTMENT = "department"
    DATE = "date"
    UNAUTHORIZED = "unauthorized"
    UNSUPPORTED = "unsupported"


class Sensitivity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True)
class IntentResult:
    intent: QueryIntent
    sensitivity: Sensitivity


RULES = {
    QueryIntent.SALARY: (("salary", "salaries", "pay", "compensation", "income"), Sensitivity.HIGH),
    QueryIntent.PERSONAL_INFORMATION: (("my details", "my information", "my profile", "my email", "my phone", "my address", "my designation", "my joining date", "my department"), Sensitivity.HIGH),
    QueryIntent.AGGREGATION: (("count", "total", "sum", "average", "avg", "maximum", "minimum", "max", "min", "number of", "how many"), Sensitivity.MEDIUM),
    QueryIntent.COMPARISON: (("compare", "comparison", "difference between", "higher than", "lower than", "greater than", "less than"), Sensitivity.MEDIUM),
    QueryIntent.EMPLOYEE_SEARCH: (("employee", "employees", "staff", "person", "people", "worker"), Sensitivity.MEDIUM),
    QueryIntent.DEPARTMENT: (("department", "departments", "team"), Sensitivity.MEDIUM),
    QueryIntent.DATE: (("date", "joining", "joined", "join date", "when did", "before", "after", "between", "this year", "last year"), Sensitivity.MEDIUM),
    QueryIntent.ANALYTICS: (("trend", "analytics", "analysis", "distribution", "breakdown", "statistics", "statistical"), Sensitivity.MEDIUM),
}


class IntentClassifier:
    def classify(self, prompt: str) -> IntentResult:
        text = prompt.strip().lower()
        if not text:
            return IntentResult(QueryIntent.UNSUPPORTED, Sensitivity.LOW)

        for intent, (keywords, sensitivity) in RULES.items():
            if any(k in text for k in keywords):
                return IntentResult(intent, sensitivity)

        return IntentResult(QueryIntent.UNSUPPORTED, Sensitivity.LOW)


intent_classifier = IntentClassifier()