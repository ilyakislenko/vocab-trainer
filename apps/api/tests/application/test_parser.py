from vocab_api.application.importing.parser import ParsedRow, RowError, parse_words


def test_csv_three_columns():
    rows, errors = parse_words("run,rʌn,бежать\njump,dʒʌmp,прыгать", "csv")
    assert errors == []
    assert rows == [
        ParsedRow(word="run", translation="бежать", transcription="rʌn"),
        ParsedRow(word="jump", translation="прыгать", transcription="dʒʌmp"),
    ]


def test_csv_two_columns_has_no_transcription():
    rows, errors = parse_words("run,бежать", "csv")
    assert rows == [ParsedRow(word="run", translation="бежать", transcription=None)]
    assert errors == []


def test_markdown_table_skips_header_and_separator():
    md = "| word | ipa | translation |\n|---|---|---|\n| run | rʌn | бежать |"
    rows, errors = parse_words(md, "markdown")
    assert rows == [ParsedRow(word="run", translation="бежать", transcription="rʌn")]
    assert errors == []


def test_row_missing_word_is_reported_but_others_parse():
    rows, errors = parse_words(",ipa,бежать\njump,dʒʌmp,прыгать", "csv")
    assert rows == [ParsedRow(word="jump", translation="прыгать", transcription="dʒʌmp")]
    assert errors == [RowError(line=1, raw=",ipa,бежать", reason="empty word")]
