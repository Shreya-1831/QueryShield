import pytest
from app.ai.intent_classifier import IntentClassifier, QueryIntent, Sensitivity

classifier = IntentClassifier()


@pytest.mark.parametrize("prompt,expected", [
    ("What is my salary?", QueryIntent.SALARY),
    ("Show me my email address", QueryIntent.PERSONAL_INFORMATION),
    ("Show employee details", QueryIntent.EMPLOYEE_SEARCH),
    ("How many employees are there?", QueryIntent.AGGREGATION),
    ("Compare the salaries of employees", QueryIntent.SALARY),
    ("Show employees in the IT department", QueryIntent.EMPLOYEE_SEARCH),
    ("Show employees who joined after 2025", QueryIntent.EMPLOYEE_SEARCH),
    ("Show the employee distribution by department", QueryIntent.EMPLOYEE_SEARCH),
    ("Tell me a joke", QueryIntent.UNSUPPORTED),
    ("", QueryIntent.UNSUPPORTED),
])
def test_intent(prompt, expected):
    assert classifier.classify(prompt).intent == expected


def test_sensitive_intents():
    assert classifier.classify("What is my salary?").sensitivity == Sensitivity.HIGH
    assert classifier.classify("Show me my email address").sensitivity == Sensitivity.HIGH