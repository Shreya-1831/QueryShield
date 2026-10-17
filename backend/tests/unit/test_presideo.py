from presidio_analyzer import AnalyzerEngine


def test_presidio_detects_email():
    analyzer = AnalyzerEngine()

    results = analyzer.analyze(
        text="Contact me at priya@company.com",
        language="en",
    )

    entity_types = {
        result.entity_type
        for result in results
    }

    assert "EMAIL_ADDRESS" in entity_types