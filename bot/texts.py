import json
from functools import lru_cache
from pathlib import Path


TOTAL_WEEKS = 4680
CONTENT_DIR = Path(__file__).resolve().parent / "content"


def _normalise_language(language_code: str) -> str:
    if not language_code:
        return "en"
    return "ru" if language_code.lower().startswith("ru") else "en"


@lru_cache(maxsize=2)
def _load_phrases(language: str) -> list[str]:
    path = CONTENT_DIR / f"weekly_phrases_{language}.json"
    with path.open(encoding="utf-8") as file:
        phrases = json.load(file)

    _validate_phrases(language, phrases)
    return phrases


def _validate_phrases(language: str, phrases: list[str]) -> None:
    if not isinstance(phrases, list) or not phrases:
        raise RuntimeError(f"{language}: phrases must be a non-empty list")

    cleaned_phrases = [phrase.strip() for phrase in phrases]
    if any(not phrase for phrase in cleaned_phrases):
        raise RuntimeError(f"{language}: phrases must not contain empty strings")

    if len(cleaned_phrases) != len(set(cleaned_phrases)):
        raise RuntimeError(f"{language}: phrases must be unique")


def get_week_phrase(language_code: str, weeks_passed: int) -> str:
    language = _normalise_language(language_code)
    phrases = _load_phrases(language)
    week_index = min(max(weeks_passed, 0), TOTAL_WEEKS - 1)
    return phrases[week_index % len(phrases)]
