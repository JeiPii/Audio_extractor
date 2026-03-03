from app.formats import format_srt_timestamp, format_vtt_timestamp


def test_srt_timestamp_formatting() -> None:
    assert format_srt_timestamp(0.0) == "00:00:00,000"
    assert format_srt_timestamp(61.234) == "00:01:01,234"
    assert format_srt_timestamp(3661.9) == "01:01:01,900"


def test_vtt_timestamp_formatting() -> None:
    assert format_vtt_timestamp(0.0) == "00:00:00.000"
    assert format_vtt_timestamp(61.234) == "00:01:01.234"
    assert format_vtt_timestamp(3661.9) == "01:01:01.900"
