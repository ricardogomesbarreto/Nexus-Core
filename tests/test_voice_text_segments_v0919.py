"""Limites de narração offline e preservação de palavras/ordem."""
import pytest

from nexus.voice.text_segments import speech_segments


def test_segments_preserve_text_and_word_boundaries():
    phrase = "A fotossíntese depende de energia luminosa. "
    text = phrase * 50
    segments = speech_segments(text, size=160, limit=4)
    assert 1 < len(segments) <= 4
    assert all(0 < len(chunk) <= 160 for chunk in segments)
    assert all(chunk[0] != " " and chunk[-1] != " " for chunk in segments)
    assert "fotossíntese" in segments[0]
    assert " ".join(segments) in " ".join(text.split())


def test_bounded_long_words_are_split_only_at_character_limit():
    chunks = speech_segments("A" * 3200, size=2400, limit=4)
    assert chunks == ("A" * 2400, "A" * 800)


def test_boundaries_and_empty_text():
    assert speech_segments("   ") == ()
    assert speech_segments("  olá \n mundo ") == ("olá mundo",)
    assert len(speech_segments("x" * 50000)) == 4
    assert sum(len(x) for x in speech_segments("x" * 50000)) == 9600


@pytest.mark.parametrize("size,limit", [
    (0, 1), (2401, 1), (True, 1), (2400, 0), (2400, 5),
    (2400, False), (2400, 1.2),
])
def test_reject_bad_limits(size, limit):
    with pytest.raises(ValueError):
        speech_segments("Olá", size=size, limit=limit)
