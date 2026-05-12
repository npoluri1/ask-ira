
from src.config import get_settings
from src.config.prompts import (
    ANALYSIS_TASK_TEMPLATE,
    RESEARCH_TASK_TEMPLATE,
    REVIEW_TASK_TEMPLATE,
    WRITING_TASK_TEMPLATE,
)
from src.config.validation import validate_config


def test_settings_defaults():
    settings = get_settings()
    assert settings.llm_provider is not None
    assert settings.environment is not None
    assert settings.cache_enabled is True


def test_settings_can_be_configured():
    settings = get_settings()
    assert hasattr(settings, "chroma_persist_dir")
    assert hasattr(settings, "embedding_model")
    assert hasattr(settings, "rate_limit_max")
    assert hasattr(settings, "rate_limit_window")


def test_validate_config_runs_without_error():
    validate_config()


def test_research_template_format():
    result = RESEARCH_TASK_TEMPLATE.format(topic="AAPL", num_queries=5)
    assert "AAPL" in result
    assert "5" in result


def test_analysis_template_format():
    result = ANALYSIS_TASK_TEMPLATE.format(
        topic="MSFT",
        research_data="Revenue growing at 15%",
    )
    assert "MSFT" in result
    assert "15%" in result


def test_writing_template_format():
    result = WRITING_TASK_TEMPLATE.format(
        topic="GOOGL",
        analysis_data="Strong ad revenue",
        num_sections=5,
        target_words=2000,
    )
    assert "GOOGL" in result
    assert "2000" in result


def test_review_template_format():
    result = REVIEW_TASK_TEMPLATE.format(
        topic="AMZN",
        report_content="AWS is growing rapidly",
    )
    assert "AMZN" in result
    assert "AWS" in result
