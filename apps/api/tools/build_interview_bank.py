"""Build the bilingual interview question bank.

Reads three sources and writes ``src/vocab_api/seed/data/interview-questions.json``:

1. ``tools/data/interview_questions_2000_bilingual.csv`` — RU+EN pairs (native).
2. ``tools/data/interview_questions_2000.csv`` — RU questions whose EN is produced
   deterministically through the 158-template table in this module.
3. ``tools/data/frontend_500.md`` — EN questions from the GitHub repo
   (Saran-pariyar/100_Days_Of_Frontend_Interview_Questions); RU comes from
   ``tools/data/github_ru.json``.

Every question ends up as::

    {"id": int, "topics": [str, ...], "level": str, "ru": str, "en": str}

``topics`` is the list of interview directions the question can be used for
(one or more of "React", "TypeScript", "Frontend", "Backend").
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
TARGET = ROOT.parent / "src" / "vocab_api" / "seed" / "data" / "interview-questions.json"

BILINGUAL_CSV = DATA / "interview_questions_2000_bilingual.csv"
FULL_CSV = DATA / "interview_questions_2000.csv"
GITHUB_MD = DATA / "frontend_500.md"
GITHUB_RU_JSON = DATA / "github_ru.json"

_TERM = re.compile(r"[A-Za-z0-9]+[\w\-/\+\.]*")

# ---------------------------------------------------------------------------
# EN templates for the CSV skeleton questions.
#
# Each key is the Russian question with the latin terms replaced by "X"
# (one X per latin token, punctuation kept as in the source). Values are
# English templates whose {0}, {1}, ... placeholders receive the latin terms
# in order. The two cyrillic-containing terms are translated in _term_en.
# ---------------------------------------------------------------------------

SKELETON_EN: dict[str, str] = {
    # --- 1 term ---
    "Что такое X?": "What is {0}?",
    "Как оптимизировать X?": "How do you optimize {0}?",
    "Как X влияет на производительность?": "How does {0} affect performance?",
    "Как протестировать X?": "How do you test {0}?",
    "Сравните X с альтернативой.": "Compare {0} with an alternative.",
    "Как мониторить X?": "How do you monitor {0}?",
    "Когда использовать X?": "When should you use {0}?",
    "Какие ошибки бывают при использовании X?": "What mistakes can occur when using {0}?",
    "Когда применять X?": "When should you apply {0}?",
    "Объясните X": "Explain {0}.",
    "Как проверить и отладить X?": "How do you check and debug {0}?",
    "Сравните X с альтернативным подходом.": "Compare {0} with an alternative approach.",
    "Какие ошибки часто допускают при работе с X?": (
        "What mistakes do people often make when working with {0}?"
    ),
    "Как тема X связана с производительностью?": "How is the topic of {0} related to performance?",
    "Как тема X связана с безопасностью?": "How is the topic of {0} related to security?",
    "Как улучшить доступность решения с X?": (
        "How do you improve the accessibility of a solution with {0}?"
    ),
    "Как отладить проблему, связанную с X?": "How do you debug a problem related to {0}?",
    "Приведите практический пример использования X": "Give a practical example of using {0}.",
    "Как найти ошибку в коде с X?": "How do you find a bug in code with {0}?",
    "Как использовать X в большом приложении?": "How do you use {0} in a large application?",
    "Какие проблемы вызывает неправильное использование X?": (
        "What problems does incorrect use of {0} cause?"
    ),
    "Приведите пример реализации X": "Give an example of implementing {0}.",
    "Как протестировать решение с X?": "How do you test a solution with {0}?",
    "Как X влияет на консистентность?": "How does {0} affect consistency?",
    "Как проверить X?": "How do you check {0}?",
    "Как применить X в высоконагруженной системе?": "How do you apply {0} in a high-load system?",
    "Как безопасно настроить X?": "How do you configure {0} securely?",
    "Какие уязвимости связаны с X?": "What vulnerabilities are related to {0}?",
    "Спроектируйте сервис с использованием X": "Design a service using {0}.",
    "Как оптимизировать решение с использованием X?": "How do you optimize a solution using {0}?",
    "Как протестировать код, связанный с X?": "How do you test code related to {0}?",
    "Какие проблемы возникают при использовании X?": "What problems can arise when using {0}?",
    "Какие ошибки проектирования связаны с X?": "What design mistakes are related to {0}?",
    "Как оптимизировать запросы с X?": "How do you optimize queries with {0}?",
    "Какие ошибки часто встречаются в X?": "What mistakes are common in {0}?",
    "Как диагностировать проблему с X?": "How do you diagnose a problem with {0}?",
    "Как настроить X?": "How do you set up {0}?",
    "Какие риски безопасности связаны с X?": "What security risks are related to {0}?",
    "Сравните X с похожей конструкцией.": "Compare {0} with a similar construct.",
    "Как использовать X в большом проекте?": "How do you use {0} in a large project?",
    "Как тестировать код с X?": "How do you test code with {0}?",
    "Как типизировать решение с помощью X?": "How do you type a solution with {0}?",
    "Какие ошибки компилятора помогает обнаружить X?": (
        "What compiler errors does {0} help to detect?"
    ),
    "Какие ограничения есть у X?": "What limitations does {0} have?",
    "Приведите пример сложного случая с X": "Give an example of a complex case with {0}.",
    "Когда следует использовать X?": "When should you use {0}?",
    "Как работает X в браузере?": "How does {0} work in the browser?",
    "Как X связан с жизненным циклом компонента?": (
        "How is {0} related to the component lifecycle?"
    ),
    "Как X ведёт себя под нагрузкой?": "How does {0} behave under load?",
    "Как безопасно использовать X?": "How do you use {0} safely?",
    "Как обеспечить отказоустойчивость при использовании X?": (
        "How do you ensure fault tolerance when using {0}?"
    ),
    # --- 2 terms ---
    "Что такое X X?": "What is {0} {1}?",
    "Как мониторить X X?": "How do you monitor {0} {1}?",
    "Как протестировать X X?": "How do you test {0} {1}?",
    "Как работает X в X?": "How does {0} work in {1}?",
    "Сравните X X с альтернативой.": "Compare {0} {1} with an alternative.",
    "Когда применять X X?": "When should you apply {0} {1}?",
    "Как спроектировать систему с X X?": "How do you design a system with {0} {1}?",
    "Как X X помогает масштабированию?": "How does {0} {1} help with scaling?",
    "Приведите пример инцидента, связанного с X X": (
        "Give an example of an incident related to {0} {1}."
    ),
    "Какие X есть у X?": "What {0} does {1} have?",
    "Как отлаживать X в X?": "How do you debug {0} in {1}?",
    "Как работает X X в браузере?": "How does {0} {1} work in the browser?",
    "Какие ошибки бывают при использовании X X?": "What mistakes can occur when using {0} {1}?",
    "Как X X влияет на производительность?": "How does {0} {1} affect performance?",
    "Приведите X с X": "Give a {0} with {1}.",
    "Как X X связан с жизненным циклом компонента?": (
        "How is {0} {1} related to the component lifecycle?"
    ),
    "Как X X ведёт себя под нагрузкой?": "How does {0} {1} behave under load?",
    "Как безопасно использовать X X?": "How do you use {0} {1} safely?",
    "Когда использовать X X?": "When should you use {0} {1}?",
    "Как обеспечить отказоустойчивость при использовании X X?": (
        "How do you ensure fault tolerance when using {0} {1}?"
    ),
    "Когда следует использовать X X?": "When should you use {0} {1}?",
    "Как X используется в X?": "How is {0} used in {1}?",
    "Какие ограничения есть у X X?": "What limitations does {0} {1} have?",
    "Как типизировать решение с помощью X X?": "How do you type a solution with {0} {1}?",
    "Какие ошибки компилятора помогает обнаружить X X?": (
        "What compiler errors does {0} {1} help to detect?"
    ),
    "Приведите пример сложного случая с X X": "Give an example of a complex case with {0} {1}.",
    "Как использовать X X в большом проекте?": "How do you use {0} {1} in a large project?",
    "Как тестировать код с X X?": "How do you test code with {0} {1}?",
    "Сравните X X с похожей конструкцией.": "Compare {0} {1} with a similar construct.",
    "Приведите X использования X": "Give a {0} of using {1}.",
    "Как протестировать код, связанный с X X?": "How do you test code related to {0} {1}?",
    "Как оптимизировать решение с использованием X X?": (
        "How do you optimize a solution using {0} {1}?"
    ),
    "Как оптимизировать X X?": "How do you optimize {0} {1}?",
    "Как X влияет на X?": "How does {0} affect {1}?",
    "Какие риски безопасности связаны с X X?": "What security risks are related to {0} {1}?",
    "Как оптимизировать запросы с X X?": "How do you optimize queries with {0} {1}?",
    "Какие ошибки проектирования связаны с X X?": "What design mistakes are related to {0} {1}?",
    "Какие ошибки часто встречаются в X X?": "What mistakes are common in {0} {1}?",
    "Как настроить X X?": "How do you set up {0} {1}?",
    "Как применить X в X?": "How do you apply {0} in {1}?",
    "Как диагностировать проблему с X X?": "How do you diagnose a problem with {0} {1}?",
    "Как проверить X в X?": "How do you check {0} in {1}?",
    "Спроектируйте сервис с использованием X X": "Design a service using {0} {1}.",
    "Какие уязвимости связаны с X X?": "What vulnerabilities are related to {0} {1}?",
    "Как безопасно настроить X X?": "How do you configure {0} {1} securely?",
    "Как мигрировать к X с X?": "How do you migrate to {0} from {1}?",
    "Как применить X X в высоконагруженной системе?": (
        "How do you apply {0} {1} in a high-load system?"
    ),
    "Какие проблемы возникают при использовании X X?": (
        "What problems can arise when using {0} {1}?"
    ),
    "Как тема X X связана с безопасностью?": "How is the topic of {0} {1} related to security?",
    "Какие ошибки часто допускают при работе с X X?": (
        "What mistakes do people often make when working with {0} {1}?"
    ),
    "Объясните X X": "Explain {0} {1}.",
    "Как проверить и отладить X X?": "How do you check and debug {0} {1}?",
    "Сравните X X с альтернативным подходом.": "Compare {0} {1} with an alternative approach.",
    "Как тема X X связана с производительностью?": (
        "How is the topic of {0} {1} related to performance?"
    ),
    "Как улучшить доступность решения с X X?": (
        "How do you improve the accessibility of a solution with {0} {1}?"
    ),
    "Как отладить проблему, связанную с X X?": "How do you debug a problem related to {0} {1}?",
    "Приведите практический пример использования X X": (
        "Give a practical example of using {0} {1}."
    ),
    "Какие проблемы вызывает неправильное использование X X?": (
        "What problems does incorrect use of {0} {1} cause?"
    ),
    "Сравните X с альтернативным подходом в X": "Compare {0} with an alternative approach in {1}.",
    "Как найти ошибку в коде с X X?": "How do you find a bug in code with {0} {1}?",
    "Как использовать X X в большом приложении?": "How do you use {0} {1} in a large application?",
    "Приведите пример реализации X X": "Give an example of implementing {0} {1}.",
    "Как X X влияет на консистентность?": "How does {0} {1} affect consistency?",
    "Как протестировать решение с X X?": "How do you test a solution with {0} {1}?",
    "Как проверить X X?": "How do you check {0} {1}?",
    # --- 3 terms ---
    "Приведите X использования X X": "Give a {0} of using {1} {2}.",
    "Как отлаживать X X в X?": "How do you debug {0} {1} in {2}?",
    "Какие X есть у X X?": "What {0} does {1} {2} have?",
    "Сравните X X с альтернативным подходом в X": (
        "Compare {0} {1} with an alternative approach in {2}."
    ),
    "Как работает X X в X?": "How does {0} {1} work in {2}?",
    "Сравните X в X и X": "Compare {0} in {1} and {2}.",
    "Как мигрировать к X X с X?": "How do you migrate to {0} {1} from {2}?",
    "Как проверить X X в X?": "How do you check {0} {1} in {2}?",
    "Как X X влияет на X?": "How does {0} {1} affect {2}?",
    "Как применить X X в X?": "How do you apply {0} {1} in {2}?",
    "Что такое X X X?": "What is {0} {1} {2}?",
    "Какие проблемы возникают при использовании X X X?": (
        "What problems can arise when using {0} {1} {2}?"
    ),
    "Какие ошибки бывают при использовании X X X?": (
        "What mistakes can occur when using {0} {1} {2}?"
    ),
    "Приведите X с X X": "Give a {0} with {1} {2}.",
    "Как X X используется в X?": "How is {0} {1} used in {2}?",
    "Как мониторить X X X?": "How do you monitor {0} {1} {2}?",
    "Как проверить X X X?": "How do you check {0} {1} {2}?",
    "Какие уязвимости связаны с X X X?": "What vulnerabilities are related to {0} {1} {2}?",
    "Сравните X X X с альтернативой.": "Compare {0} {1} {2} with an alternative.",
    "Как безопасно настроить X X X?": "How do you configure {0} {1} {2} securely?",
    "Как применить X X X в высоконагруженной системе?": (
        "How do you apply {0} {1} {2} in a high-load system?"
    ),
    "Спроектируйте сервис с использованием X X X": "Design a service using {0} {1} {2}.",
    "Приведите пример сложного случая с X X X": (
        "Give an example of a complex case with {0} {1} {2}."
    ),
    "Как тестировать код с X X X?": "How do you test code with {0} {1} {2}?",
    "Как использовать X X X в большом проекте?": "How do you use {0} {1} {2} in a large project?",
    "Сравните X X X с похожей конструкцией.": "Compare {0} {1} {2} with a similar construct.",
    "Какие ошибки компилятора помогает обнаружить X X X?": (
        "What compiler errors does {0} {1} {2} help to detect?"
    ),
    "Как типизировать решение с помощью X X X?": "How do you type a solution with {0} {1} {2}?",
    "Какие ограничения есть у X X X?": "What limitations does {0} {1} {2} have?",
    "Когда следует использовать X X X?": "When should you use {0} {1} {2}?",
    "Какие риски безопасности связаны с X X X?": (
        "What security risks are related to {0} {1} {2}?"
    ),
    "Как диагностировать проблему с X X X?": "How do you diagnose a problem with {0} {1} {2}?",
    "Как протестировать X X X?": "How do you test {0} {1} {2}?",
    "Как настроить X X X?": "How do you set up {0} {1} {2}?",
    "Как X X X влияет на производительность?": "How does {0} {1} {2} affect performance?",
    # --- 4 terms ---
    "Сравните X X в X и X": "Compare {0} {1} in {2} and {3}.",
    "Как X X X используется в X?": "How is {0} {1} {2} used in {3}?",
    "Как отлаживать X X X в X?": "How do you debug {0} {1} {2} in {3}?",
    "Как мигрировать к X X X с X?": "How do you migrate to {0} {1} {2} from {3}?",
    "Как проверить X X X в X?": "How do you check {0} {1} {2} in {3}?",
    "Как применить X X X в X?": "How do you apply {0} {1} {2} in {3}?",
    "Какие X есть у X X X?": "What {0} does {1} {2} {3} have?",
}

_SECTION_TOPICS: dict[str, list[str]] = {
    "Frontend / JavaScript": ["Frontend"],
    "Frontend / TypeScript": ["Frontend", "TypeScript"],
    "Frontend / HTML CSS Browser": ["Frontend"],
    "Frontend / React": ["Frontend", "React"],
    "Frontend / Next.js Performance Testing Security": ["Frontend"],
    "Backend / Node.js API": ["Backend"],
    "Backend / Databases": ["Backend"],
    "Backend / Architecture Distributed Systems": ["Backend"],
    "Backend / Security DevOps System Design": ["Backend"],
    # GitHub repo sections (frontend only).
    "HTML": ["Frontend"],
    "CSS": ["Frontend"],
    "Javascript": ["Frontend"],
    "React": ["Frontend", "React"],
    "Typescript": ["Frontend", "TypeScript"],
}

_TERM_EN = {
    "production-пример": "production example",
    "SSR-приложении": "SSR application",
}

_LEVEL_ORDER = {"Junior": 0, "Middle": 1, "Senior": 2}


def skeleton_and_terms(question: str) -> tuple[str, list[str]]:
    """Return (skeleton, terms) for a Russian question.

    Skeleton keeps Cyrillic words and punctuation; every latin token becomes
    "X". Terms are the latin tokens in order, punctuation stripped.
    """
    parts: list[str] = []
    terms: list[str] = []
    for token in re.findall(r"[\w\-/\+\.]+|[^\w\s]", question):
        if _TERM.fullmatch(token):
            parts.append("X")
            terms.append(token.strip(".,!?;:"))
        else:
            parts.append(token)
    skeleton = " ".join(parts)
    for mark in (",", ".", "?", "!", ";", ":"):
        skeleton = skeleton.replace(f" {mark}", mark)
    return skeleton, terms


def _term_en(term: str) -> str:
    return _TERM_EN.get(term, term)


def translate_en(question: str) -> str:
    skeleton, terms = skeleton_and_terms(question)
    template = SKELETON_EN[skeleton]
    return template.format(*[_term_en(t) for t in terms])


def read_bilingual() -> list[dict]:
    """Read the bilingual CSV: 234 unique RU+EN questions.

    A question may appear in several (section, level) rows; the row with the
    highest level wins, and topics are the union over all its rows.
    """
    rows = list(csv.DictReader(open(BILINGUAL_CSV, encoding="utf-8")))
    best: dict[str, dict] = {}
    for r in rows:
        ru = r["question"].strip()
        en = r["question_en"].strip()
        section = f"{r['area']} / {r['section']}"
        level = r["level"].strip()
        key = ru
        current = best.get(key)
        if current is None or _LEVEL_ORDER.get(level, 0) > _LEVEL_ORDER.get(
            current["level"], 0
        ):
            best[key] = {"ru": ru, "en": en, "level": level, "_topics": set()}
        for topic in _SECTION_TOPICS.get(section, ["Frontend"]):
            best[key]["_topics"].add(topic)
    result: list[dict] = []
    for data in best.values():
        topics = sorted(data.pop("_topics"))
        data["topics"] = topics
        result.append(data)
    return result


def read_full_csv() -> list[dict]:
    """Read the 9000-row CSV, dedupe to unique RU texts, EN via templates."""
    rows = list(csv.DictReader(open(FULL_CSV, encoding="utf-8")))
    best: dict[str, dict] = {}
    for r in rows:
        ru = r["question"].strip()
        section = r["section"].strip()
        level = r["level"].strip()
        current = best.get(ru)
        if current is None or _LEVEL_ORDER.get(level, 0) > _LEVEL_ORDER.get(
            current["level"], 0
        ):
            best[ru] = {"ru": ru, "level": level, "topics": _SECTION_TOPICS.get(section, ["Frontend"])}
    result: list[dict] = []
    for data in best.values():
        data["en"] = translate_en(data["ru"])
        result.append(data)
    return result


def read_github() -> list[dict]:
    """Read the GitHub repo questions (EN native) with RU from github_ru.json."""
    ru_map = json.loads(GITHUB_RU_JSON.read_text(encoding="utf-8"))
    text = GITHUB_MD.read_text(encoding="utf-8")
    anchors = [
        ("HTML", r"\n# HTML\n", r"\n# CSS\n"),
        ("CSS", r"\n# CSS\n", r"\n# Javascript\n"),
        ("Javascript", r"\n# Javascript\n", r"\n# ReactJS\n"),
        ("React", r"\n# ReactJS\n", r"\n# Typescript\n"),
        ("Typescript", r"\n# Typescript\n", r"\Z"),
    ]
    seen: set[str] = set()
    result: list[dict] = []
    for section, start_pat, end_pat in anchors:
        start = re.search(start_pat, text)
        end = re.search(end_pat, text)
        if start is None or end is None:
            continue
        chunk = text[start.end(): end.start() if end.start() > start.end() else len(text)]
        for m in re.finditer(r"^\s*\d+\.\s+###\s+(.+)$", chunk, re.MULTILINE):
            en = re.sub(r"[`*\\]", "", m.group(1)).strip()
            en = (
                en.replace("\u2019", "'")
                .replace("\u2018", "'")
                .replace("\u201c", '"')
                .replace("\u201d", '"')
                .replace("\u2033", '"')
            )
            key = en.lower()
            if key in seen:
                continue
            seen.add(key)
            ru = ru_map.get(en)
            if not ru:
                raise KeyError(f"Missing RU translation for: {en}")
            result.append(
                {
                    "ru": ru,
                    "en": en,
                    "level": "General",
                    "topics": _SECTION_TOPICS[section],
                }
            )
    return result


def main() -> None:
    bilingual = read_bilingual()
    full = read_full_csv()
    github = read_github()

    known_ru = {q["ru"] for q in bilingual}
    full_extra = [q for q in full if q["ru"] not in known_ru]

    combined = bilingual + full_extra + github
    combined.sort(key=lambda q: (q["ru"], q["en"]))

    for index, q in enumerate(combined, start=1):
        q["id"] = index

    payload = [
        {"id": q["id"], "topics": q["topics"], "level": q["level"], "ru": q["ru"], "en": q["en"]}
        for q in combined
    ]
    TARGET.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"bilingual: {len(bilingual)} unique")
    print(f"full csv:   {len(full)} unique, {len(full_extra)} not in bilingual")
    print(f"github:     {len(github)}")
    print(f"total:      {len(payload)} -> {TARGET}")


if __name__ == "__main__":
    main()