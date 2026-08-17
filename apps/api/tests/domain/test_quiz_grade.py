from vocab_api.domain.curriculum.quiz import QuizItem, QuizItemType, grade


def _item(
    item_type: QuizItemType,
    *,
    options: tuple[str, ...] | None = None,
    answer_index: int | None = None,
    answers: tuple[str, ...] | None = None,
    llm_gradable: bool = False,
) -> QuizItem:
    return QuizItem(
        id="q1",
        module_id="b1.grammar.articles",
        type=item_type,
        skill="art.indefinite",
        prompt="Prompt",
        explanation="Explanation",
        options=options,
        answer_index=answer_index,
        answers=answers,
        llm_gradable=llm_gradable,
    )


def test_mcq_grades_selected_index():
    item = _item(QuizItemType.MCQ, options=("a", "an", "the"), answer_index=1)
    assert grade(item, "1").correct is True
    assert grade(item, "0").correct is False


def test_mcq_accepts_whitespace_around_index():
    item = _item(QuizItemType.MCQ, options=("a", "an", "the"), answer_index=1)
    assert grade(item, " 1 ").correct is True


def test_mcq_without_answer_index_never_grades_correct():
    item = _item(QuizItemType.MCQ, options=("a", "an", "the"))
    assert grade(item, "1").correct is False


def test_cloze_is_case_insensitive_and_trimmed():
    item = _item(QuizItemType.CLOZE, answers=("the",))
    assert grade(item, "The").correct is True
    assert grade(item, "  the  ").correct is True
    assert grade(item, "a").correct is False


def test_cloze_accepts_any_accepted_answer():
    item = _item(QuizItemType.CLOZE, answers=("momentum", "traction"))
    assert grade(item, "TRACTION").correct is True


def test_transform_ignores_trailing_punctuation_and_case():
    item = _item(
        QuizItemType.TRANSFORM,
        answers=("I have eaten sushi",),
    )
    assert grade(item, "I have eaten sushi.").correct is True
    assert grade(item, "i have eaten sushi").correct is True
    assert grade(item, "I have ate sushi").correct is False


def test_error_correction_grade_exact():
    item = _item(
        QuizItemType.ERROR_CORRECTION,
        answers=("I go to work by train every day",),
    )
    assert grade(item, "I go to work by train every day").correct is True
    assert grade(item, "I go to work every day by train").correct is False


def test_error_correction_miss_flags_llm_when_gradable():
    item = _item(
        QuizItemType.ERROR_CORRECTION,
        answers=("I go to work by train every day",),
        llm_gradable=True,
    )
    result = grade(item, "I go to work every day by train")
    assert result.correct is False
    assert result.needs_llm is True


def test_error_correction_hit_does_not_flag_llm():
    item = _item(
        QuizItemType.ERROR_CORRECTION,
        answers=("I go to work by train every day",),
        llm_gradable=True,
    )
    result = grade(item, "I go to work by train every day")
    assert result.correct is True
    assert result.needs_llm is False
