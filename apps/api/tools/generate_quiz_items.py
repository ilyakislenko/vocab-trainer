"""LLM-assisted quiz item generation — offline dev tool (human review gate).

Drafts candidate quiz items for one module from a short **skeleton note**
(the grammar point and the structures to cover, in the owner's own words)
plus the module's declared skills from its lesson frontmatter. The model
re-words and varies structures; the tool never feeds copyrighted exercise
text in and never writes to the live quiz.

Output is written next to the module's quiz as ``<module>.draft.json`` —
the live ``quizzes/<module>.json`` is never overwritten and nothing is
committed. A human must review, edit/cull, and merge the reviewed items
into the live quiz file (see ``tools/README.md`` for the loop).

Usage (from ``apps/api``)::

    uv run python tools/generate_quiz_items.py \\
        --module a2.grammar.past-simple \\
        --types mcq cloze word_order \\
        --count 8 \\
        --skeleton "past simple: regular and irregular forms, yes/no questions, negatives"

The model endpoint mirrors the app's OpenAiCompatibleProvider wire format
and reads the same env config (``VOCAB_LLM_BASE_URL``, ``VOCAB_LLM_MODEL``,
``VOCAB_LLM_API_KEY``).
"""

import argparse
import asyncio
import json
import re
from pathlib import Path

import httpx

from vocab_api.config.settings import Settings
from vocab_api.domain.curriculum.quiz import QuizItemType
from vocab_api.infrastructure.curriculum.content_loader import ContentBundle

QUIZZES_DIR = (
    Path(__file__).resolve().parent.parent / "src" / "vocab_api" / "seed" / "content" / "quizzes"
)

_SYSTEM = (
    "You are an ESL exercise author writing original English grammar/vocabulary items. "
    "The owner gives you a module, the module's declared skills, and a skeleton note "
    "(the grammar point and the structures to cover). "
    "Write items strictly for those skills and structures, in your own words — "
    "re-word and vary the structures; never copy exercises from textbooks. "
    "Each item must be self-contained and unambiguous. "
    "Reply with ONLY a JSON array of items, each with keys: "
    '"type" ("mcq" | "cloze" | "transform" | "error_correction" | "word_order" | '
    '"listening"), "skill" (one of the declared skills), '
    '"prompt" (the question or instruction for the learner), "explanation" (1-2 sentences), '
    'and, by type: mcq -> "options" (array of 3-5 strings) and "answer_index" (0-based); '
    'cloze -> "answers" (array of accepted answers); transform/error_correction -> '
    '"answers" (array with the one correct rewritten sentence); word_order -> "tokens" '
    '(array of shuffled words) and "answers" (array with the one correct ordering as a '
    'space-joined string); listening -> "prompt" is the sentence to speak, plus either '
    '"answers" (dictation) or "options"/"answer_index" (choose what you heard). '
    "Do not leak the answer inside the prompt."
)


def _parse_items(raw: str) -> list[object]:
    """Extract the JSON array from a chat reply, tolerating code fences."""
    text = raw.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("[")
        end = text.rfind("]")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, list):
        raise ValueError("expected a JSON array of items")
    return parsed


def _leaks_answer(item: dict) -> str | None:
    """Mirror the loader's leak guard: a long answer variant must not appear
    in the prompt. Listening prompts are the dictated audio text, so the
    check is skipped for them."""
    if item.get("type") == QuizItemType.LISTENING.value:
        return None
    variants: list[str] = []
    if item.get("options") and isinstance(item.get("answer_index"), int):
        options = item["options"]
        index = item["answer_index"]
        if isinstance(options, list) and 0 <= index < len(options):
            variants.append(str(options[index]))
    elif item.get("answers"):
        variants.extend(str(a) for a in item["answers"])
    prompt = str(item.get("prompt", "")).lower()
    for variant in variants:
        words = variant.split()
        if len(words) < 2 and len(variant) < 8:
            continue
        if variant.lower() in prompt:
            return variant
    return None


def _validate_item(raw: object, module_id: str, skills: set[str]) -> tuple[str | None, dict | None]:
    """Validate a draft item against the module's declared skills and the
    loader's shape rules. Returns (reason, item) where item is a cleaned dict
    (or None if the reason is a rejection)."""
    context = f"{module_id} draft"
    if not isinstance(raw, dict):
        return f"{context}: item is not an object", None
    item_type_raw = raw.get("type")
    try:
        item_type = QuizItemType(item_type_raw)
    except ValueError:
        return f"{context}: invalid type {item_type_raw!r}", None
    skill = raw.get("skill")
    if skill not in skills:
        return f"{context}: skill {skill!r} not declared in lesson skills", None
    prompt = raw.get("prompt")
    explanation = raw.get("explanation")
    if not isinstance(prompt, str) or not prompt.strip():
        return f"{context}: prompt must be a non-empty string", None
    if not isinstance(explanation, str) or not explanation.strip():
        return f"{context}: explanation must be a non-empty string", None

    item: dict = {
        "type": item_type.value,
        "skill": skill,
        "prompt": prompt.strip(),
        "explanation": explanation.strip(),
    }
    if item_type is QuizItemType.MCQ:
        options = raw.get("options")
        index = raw.get("answer_index")
        if (
            not isinstance(options, list)
            or not options
            or not all(isinstance(o, str) and o.strip() for o in options)
        ):
            return f"{context}: mcq needs non-empty string options", None
        if not isinstance(index, int) or not 0 <= index < len(options):
            return f"{context}: mcq needs a valid answer_index", None
        item["options"] = [o.strip() for o in options]
        item["answer_index"] = index
    elif item_type is QuizItemType.LISTENING:
        options = raw.get("options")
        if options is not None:
            index = raw.get("answer_index")
            if (
                not isinstance(options, list)
                or not options
                or not all(isinstance(o, str) and o.strip() for o in options)
            ):
                return f"{context}: listening mcq needs non-empty string options", None
            if not isinstance(index, int) or not 0 <= index < len(options):
                return f"{context}: listening mcq needs a valid answer_index", None
            item["options"] = [o.strip() for o in options]
            item["answer_index"] = index
        else:
            answers = raw.get("answers")
            if (
                not isinstance(answers, list)
                or not answers
                or not all(isinstance(a, str) and a.strip() for a in answers)
            ):
                return f"{context}: listening dictation needs non-empty string answers", None
            item["answers"] = [a.strip() for a in answers]
    elif item_type is QuizItemType.WORD_ORDER:
        tokens = raw.get("tokens")
        answers = raw.get("answers")
        if (
            not isinstance(tokens, list)
            or not tokens
            or not all(isinstance(t, str) and t.strip() for t in tokens)
        ):
            return f"{context}: word_order needs non-empty string tokens", None
        if (
            not isinstance(answers, list)
            or not answers
            or not all(isinstance(a, str) and a.strip() for a in answers)
        ):
            return f"{context}: word_order needs non-empty string answers", None
        item["tokens"] = [t.strip() for t in tokens]
        item["answers"] = [a.strip() for a in answers]
    else:
        answers = raw.get("answers")
        if (
            not isinstance(answers, list)
            or not answers
            or not all(isinstance(a, str) and a.strip() for a in answers)
        ):
            return f"{context}: {item_type.value} needs non-empty string answers", None
        item["answers"] = [a.strip() for a in answers]

    leak = _leaks_answer(item)
    if leak is not None:
        return f"{context}: prompt leaks the answer {leak!r}", None
    return None, item


async def _chat(base_url: str, model: str, api_key: str | None, user: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7,
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/chat/completions", json=payload, headers=headers
        )
        response.raise_for_status()
        data = response.json()
        return str(data["choices"][0]["message"]["content"])


def _build_user_prompt(
    module_id: str, title: str, skills: list[str], types: list[str], count: int, skeleton: str
) -> str:
    types_line = ", ".join(f'"{t}"' for t in types)
    skills_line = ", ".join(f'"{s}"' for s in skills)
    return (
        f"Module: {module_id} ({title})\n"
        f"Declared skills: {skills_line}\n"
        f"Requested types: [{types_line}]\n"
        f"Number of items: {count}\n"
        f"Skeleton note (topic outline, in the owner's words):\n{skeleton}\n"
        "Return ONLY the JSON array of items."
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Draft quiz items for a module with LLM assistance (human review required)."
    )
    parser.add_argument("--module", required=True, help="Module id, e.g. a2.grammar.past-simple")
    parser.add_argument("--types", nargs="+", required=True, help="Quiz item types to draft")
    parser.add_argument("--count", type=int, default=10, help="Number of items to draft")
    parser.add_argument("--skeleton", required=True, help="Topic outline / structures to cover")
    args = parser.parse_args()

    bundle = ContentBundle.from_files()
    lesson = bundle.lesson(args.module)
    if lesson is None:
        raise SystemExit(f"module {args.module!r} not found in the content bundle")

    existing = bundle.quiz(args.module)
    seen_prompts: set[str] = set()
    if existing is not None:
        seen_prompts = {item.prompt.lower() for item in existing.items}

    user = _build_user_prompt(
        args.module,
        lesson.title,
        list(lesson.skills),
        args.types,
        args.count,
        args.skeleton,
    )
    settings = Settings()
    print(f"Calling {settings.llm_base_url} model {settings.llm_model}...")
    raw = asyncio.run(_chat(settings.llm_base_url, settings.llm_model, settings.llm_api_key, user))

    drafted: list[dict] = []
    dropped: list[str] = []
    for raw_item in _parse_items(raw):
        reason, item = _validate_item(raw_item, args.module, set(lesson.skills))
        if reason is not None:
            dropped.append(reason)
            continue
        prompt_key = item["prompt"].lower()
        if prompt_key in seen_prompts:
            dropped.append(f"{args.module}: duplicate prompt {item['prompt']!r}")
            continue
        seen_prompts.add(prompt_key)
        drafted.append(item)

    if drafted:
        next_index = 1
        if existing is not None:
            for item in existing.items:
                match = re.match(rf"{re.escape(args.module)}\.q(\d+)$", item.id)
                if match:
                    next_index = max(next_index, int(match.group(1)) + 1)
        for offset, item in enumerate(drafted):
            item["id"] = f"{args.module}.q{next_index + offset}"
        draft_path = QUIZZES_DIR / f"{args.module}.draft.json"
        payload = {
            "module_id": args.module,
            "skeleton": args.skeleton,
            "items": drafted,
        }
        draft_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"drafted {len(drafted)} items -> {draft_path}")
    else:
        print("no items survived validation; nothing written")

    if dropped:
        print("dropped:")
        for reason in dropped:
            print(f"  - {reason}")


if __name__ == "__main__":
    main()
