import { createContext, type ReactNode, useCallback, useContext, useState } from "react";

type Locale = "en" | "ru";

type Translations = Record<string, Record<Locale, string>>;

const dict: Translations = {
  // Navigation
  "nav.learn": { en: "Learn", ru: "Изучение" },
  "nav.review": { en: "Review", ru: "Повторение" },
  "nav.practice": { en: "Practice", ru: "Практика" },
  "nav.profile": { en: "Profile", ru: "Профиль" },
  "nav.tools": { en: "Tools", ru: "Инструменты" },
  "nav.import": { en: "Import", ru: "Импорт" },
  "nav.stats": { en: "Stats", ru: "Статистика" },
  "nav.dark": { en: "Dark", ru: "Тёмная" },
  "nav.light": { en: "Light", ru: "Светлая" },

  // Header
  "header.title": { en: "Vocab Trainer", ru: "Vocab Trainer" },
  "header.newDeck": { en: "New deck…", ru: "Новая колода…" },
  "header.create": { en: "Create", ru: "Создать" },
  "header.selectDeck": { en: "Select a deck", ru: "Выберите колоду" },
  "header.deckCreateError": {
    en: "Failed to create deck. Please try again.",
    ru: "Не удалось создать колоду. Попробуйте ещё раз.",
  },

  // Practice modes
  "practice.due": { en: "Due words", ru: "Изучаемые" },
  "practice.all": { en: "All words", ru: "Все слова" },
  "practice.topic": { en: "By topic", ru: "По теме" },
  "practice.allSections": { en: "All sections", ru: "Все секции" },
  "practice.section": { en: "Section", ru: "Секция" },
  "practice.sectionSelected": { en: "Section", ru: "Секция" },
  "practice.findWords": { en: "Find topic words", ru: "Найти слова" },
  "practice.topicPlaceholder": {
    en: "Describe the words you want to practise, e.g. 'travel, food, emotions'…",
    ru: "Опишите тему, например: «путешествия, еда, эмоции»…",
  },

  // Practice session
  "practice.writeSentence": { en: "Write a sentence using", ru: "Составь предложение с" },
  "practice.check": { en: "Check", ru: "Проверить" },
  "practice.getExample": { en: "Get an example", ru: "Показать пример" },
  "practice.hint": { en: "How to use", ru: "Как использовать" },
  "practice.hintLoading": { en: "Loading hint…", ru: "Загрузка подсказки…" },
  "practice.hintError": {
    en: "Couldn't load the description.",
    ru: "Не удалось загрузить описание.",
  },
  "practice.drill": { en: "💬 Train this word", ru: "💬 Тренировать это слово" },
  "practice.drillTitle": { en: "💬 Training", ru: "💬 Тренировка" },
  "practice.back": { en: "← Back", ru: "← Назад" },
  "practice.continue": { en: "Continue →", ru: "Далее →" },
  "practice.finish": { en: "Finish", ru: "Завершить" },
  "practice.summary": { en: "Run complete!", ru: "Тренировка завершена!" },
  "practice.completed": { en: "words practised", ru: "слов пройдено" },
  "practice.okCount": { en: "✓ Looks good", ru: "✓ Получилось" },
  "practice.needsWorkCount": { en: "Needs work", ru: "Подучить" },
  "practice.practiseMore": { en: "Practise more", ru: "Повторить ещё" },
  "practice.practising": { en: "Studying section", ru: "Практикуешь раздел" },
  "practice.hear": { en: "🔊 Hear it", ru: "🔊 Слушать" },
  "practice.say": { en: "🎤 Say it", ru: "🎤 Говорить" },
  "practice.saySentence": { en: "🎤 Say the sentence", ru: "🎤 Произнеси предложение" },
  "practice.nothing": { en: "Nothing to practise right now 🎉", ru: "Нечего повторять 🎉" },
  "practice.loading": { en: "Loading…", ru: "Загрузка…" },
  "practice.noDeck": {
    en: "Create a deck above first, then come back here to practise.",
    ru: "Сначала создай колоду выше, затем возвращайся сюда практиковаться.",
  },
  "practice.tabSentence": { en: "Sentence", ru: "Предложение" },
  "practice.tabSpeak": { en: "Speak", ru: "Говорение" },
  "practice.tabDrill": { en: "Drill", ru: "Дрилл" },
  "practice.hearLabel": { en: "Hear pronunciation", ru: "Прослушать произношение" },
  "practice.yourSentence": { en: "Your sentence", ru: "Твоё предложение" },
  "practice.voiceInput": { en: "Voice input", ru: "Голосовой ввод" },
  "practice.stopRecording": { en: "Stop recording", ru: "Остановить запись" },
  "practice.speechFailed": { en: "Speech recognition failed", ru: "Не удалось распознать речь" },
  "practice.examplePrefix": { en: "Example", ru: "Пример" },
  "practice.exampleLabel": { en: "Example:", ru: "Пример:" },
  "practice.everythingChecked": { en: "Everything checked!", ru: "Всё проверено!" },

  // Pronunciation feedback
  "pronounce.matched": { en: "✓ Nice — that matched!", ru: "✓ Отлично — совпало!" },
  "pronounce.notMatched": {
    en: "✗ Heard {heard}, try again.",
    ru: "✗ Распознано: {heard}. Попробуй ещё.",
  },
  "pronounce.heardNothing": { en: "nothing", ru: "ничего" },
  "pronounce.checkingGrammar": { en: "Checking grammar…", ru: "Проверяю грамматику…" },
  "pronounce.sayLike": { en: "Say it like: {text}", ru: "Говори как: {text}" },
  "pronounce.nativeWay": { en: "Native way: {text}", ru: "По-настоящему: {text}" },
  "pronounce.sentenceMatched": {
    en: "✓ Great job on the sentence!",
    ru: "✓ Отлично, предложение!",
  },
  "pronounce.sentenceNotMatched": {
    en: "✗ Not quite. Try saying the whole sentence.",
    ru: "✗ Не совсем. Попробуй произнести предложение целиком.",
  },
  "pronounce.sentenceMissed": { en: "Missing words:", ru: "Пропущенные слова:" },
  "pronounce.sentenceHeard": { en: "Heard:", ru: "Распознано:" },

  // Feedback
  "feedback.ok": { en: "✓ Looks good!", ru: "✓ Отлично!" },
  "feedback.needsWork": { en: "✗ Needs work", ru: "✗ Нужно подучить" },
  "feedback.corrected": { en: "Corrected", ru: "Исправлено" },
  "feedback.correctedLabel": { en: "Corrected:", ru: "Исправлено:" },
  "feedback.example": { en: "Example", ru: "Пример" },
  "feedback.unavailable": {
    en: "The language model is unavailable.",
    ru: "Языковая модель недоступна.",
  },
  "feedback.exampleError": {
    en: "Couldn't fetch an example.",
    ru: "Не удалось загрузить пример.",
  },
  "feedback.noFeedback": { en: "No feedback.", ru: "Без комментариев." },

  // Mascot phrases
  "mascot.happy": {
    en: "Great job! You're doing amazing!",
    ru: "Отлично! Ты молодец!",
  },
  "mascot.sad": {
    en: "Don't worry, try again! 💪",
    ru: "Не переживай, попробуй ещё! 💪",
  },
  "mascot.thinking": { en: "Hmm…", ru: "Хмм…" },

  // Drill chat
  "drill.placeholder": { en: "Write a sentence…", ru: "Напиши предложение…" },
  "drill.send": { en: "Send", ru: "Отправить" },
  "drill.greeting": { en: "Write a sentence with", ru: "Напиши предложение с" },
  "drill.reply": { en: "and I'll reply!", ru: "и я отвечу!" },
  "drill.error": { en: "Couldn't get a response. Try again.", ru: "Нет ответа. Попробуй ещё." },

  // Interview
  "nav.interview": { en: "Interview", ru: "Собеседование" },
  "interview.title": { en: "Mock interview", ru: "Собеседование" },
  "interview.subtitle": {
    en: "Practise answering real developer interview questions out loud. Pick a topic to start.",
    ru: "Потренируйся отвечать на реальные вопросы собеседования вслух. Выбери тему, чтобы начать.",
  },
  "interview.pickTopic": { en: "Topic:", ru: "Тема:" },
  "interview.langEn": { en: "EN", ru: "EN" },
  "interview.langRu": { en: "RU", ru: "RU" },
  "interview.topicReact": { en: "React", ru: "React" },
  "interview.topicTypeScript": { en: "TypeScript", ru: "TypeScript" },
  "interview.topicFrontend": { en: "Frontend", ru: "Frontend" },
  "interview.topicBackend": { en: "Backend", ru: "Backend" },
  "interview.placeholder": { en: "Type your answer…", ru: "Введи свой ответ…" },
  "interview.send": { en: "Send", ru: "Отправить" },
  "interview.thinking": { en: "The interviewer is thinking…", ru: "Интервьюер думает…" },
  "interview.error": {
    en: "The interviewer is unavailable right now. Try again.",
    ru: "Интервьюер сейчас недоступен. Попробуй ещё.",
  },
  "interview.good": { en: "Good answer!", ru: "Хороший ответ!" },
  "interview.needsWork": { en: "Needs work", ru: "Нужно подучить" },
  "interview.corrected": { en: "Better: ", ru: "Как лучше: " },
  "interview.customTopic": {
    en: "Or type any topic to switch…",
    ru: "Или введи свою тему…",
  },
  "interview.changeTopic": { en: "Switch topic", ru: "Сменить тему" },
  "interview.viewChat": { en: "Chat", ru: "Чат" },
  "interview.viewCall": { en: "Call", ru: "Звонок" },
  "interview.nextQuestion": { en: "Next question", ru: "Следующий вопрос" },
  "interview.randomQuestion": { en: "Random question", ru: "Случайный вопрос" },
  "interview.setupTitle": { en: "Set up your interview", ru: "Настрой собеседование" },
  "interview.setupSubtitle": {
    en: "Choose a topic, difficulty and how many questions to answer.",
    ru: "Выбери тему, сложность и количество вопросов.",
  },
  "interview.difficulty": { en: "Difficulty", ru: "Сложность" },
  "interview.difficultyJunior": { en: "Junior", ru: "Джун" },
  "interview.difficultyMiddle": { en: "Middle", ru: "Мидл" },
  "interview.difficultySenior": { en: "Senior", ru: "Сеньор" },
  "interview.questionCount": { en: "Questions", ru: "Вопросов" },
  "interview.countQuestions": { en: "{n} questions", ru: "{n} вопросов" },
  "interview.countUnlimited": { en: "Until I stop", ru: "Пока не остановлюсь" },
  "interview.view": { en: "Mode", ru: "Режим" },
  "interview.language": { en: "Interview language", ru: "Язык интервью" },
  "interview.scene": { en: "Scene", ru: "Локация" },
  "interview.useTopic": { en: "Use", ru: "Использовать" },
  "interview.start": { en: "Start interview", ru: "Начать собеседование" },
  "interview.sessionQuestion": { en: "Q {n}", ru: "Вопрос {n}" },
  "interview.restart": { en: "Restart", ru: "Заново" },
  "interview.finish": { en: "Finish", ru: "Завершить" },
  "interview.summaryTitle": { en: "Interview complete", ru: "Собеседование завершено" },
  "interview.summarySubtitle": {
    en: "Here is how it went.",
    ru: "Вот как всё прошло.",
  },
  "interview.ok": { en: "Good answers", ru: "Хороших ответов" },
  "interview.questions": { en: "Questions", ru: "Вопросов" },
  "interview.duration": { en: "Duration", ru: "Длительность" },
  "interview.corrections": { en: "Things to review", ru: "Что подучить" },
  "interview.noCorrections": {
    en: "No corrections this time — great job!",
    ru: "В этот раз без замечаний — отличная работа!",
  },
  "interview.startAgain": { en: "Start again", ru: "Ещё раз" },
  "interview.backToSetup": { en: "Change settings", ru: "Изменить настройки" },
  "interview.callReady": {
    en: "Tap the mic and answer aloud.",
    ru: "Нажми на микрофон и отвечай вслух.",
  },
  "interview.callListening": { en: "Listening…", ru: "Слушаю…" },
  "interview.callSpeaking": { en: "Speaking…", ru: "Говорю…" },
  "interview.callWaiting": {
    en: "The call is connecting…",
    ru: "Звонок подключается…",
  },
  "interview.chooseTopicFirst": {
    en: "Pick a topic above to start.",
    ru: "Выбери тему выше, чтобы начать.",
  },
  "interview.callEnd": { en: "End call", ru: "Завершить звонок" },
  "interview.callLive": { en: "LIVE", ru: "В ЭФИРЕ" },
  "interview.callMute": { en: "Mute", ru: "Выключить микрофон" },
  "interview.callUnmute": { en: "Unmute", ru: "Включить микрофон" },
  "interview.callMuted": { en: "Muted", ru: "Микрофон выключен" },
  "interview.callCameraOn": { en: "Camera on", ru: "Включить камеру" },
  "interview.callCameraOff": { en: "Camera off", ru: "Выключить камеру" },
  "interview.callAvatar": { en: "?", ru: "?" },
  "interview.callSceneOffice": { en: "Office", ru: "Офис" },
  "interview.callSceneCafe": { en: "Cafe", ru: "Кафе" },
  "interview.callScenePark": { en: "Park", ru: "Парк" },
  "interview.callSceneNight": { en: "Night", ru: "Ночь" },

  // Review
  "review.showAnswer": { en: "Show answer", ru: "Показать ответ" },
  "review.revealHint": { en: "Space", ru: "Пробел" },
  "review.caughtUp": { en: "You're all caught up 🎉", ru: "Всё повторено 🎉" },
  "review.summary": { en: "Session complete!", ru: "Сессия завершена!" },
  "review.reviewed": { en: "Cards reviewed", ru: "Карточек пройдено" },
  "review.startAgain": { en: "Start again", ru: "Начать заново" },
  "review.ratingAgain": { en: "Again", ru: "Заново" },
  "review.ratingHard": { en: "Hard", ru: "Сложно" },
  "review.ratingGood": { en: "Good", ru: "Хорошо" },
  "review.ratingEasy": { en: "Easy", ru: "Легко" },
  "review.left": { en: "left", ru: "осталось" },
  "review.reviewedToday": { en: "reviewed today", ru: "пройдено сегодня" },
  "review.returnsTomorrow": { en: "Returns tomorrow", ru: "Вернётся завтра" },
  "review.returnsIn": { en: "Returns in {n} d.", ru: "Вернётся через {n} дн." },
  "review.practiceMore": { en: "Practice more", ru: "Повторить ещё" },

  // Skill reviews (Phase 2)
  "skill.title": { en: "Skill reviews", ru: "Повторение навыков" },
  "skill.hint": {
    en: "Skills you got wrong in quizzes resurface here on a schedule.",
    ru: "Навыки, в которых ты ошибся в тестах, появляются здесь по расписанию.",
  },
  "skill.answers": { en: "Answer", ru: "Ответ" },
  "skill.explanation": { en: "Why", ru: "Почему" },
  "skill.reviewed": { en: "Skill items reviewed", ru: "Навыков повторено" },
  "skill.answerYourself": {
    en: "Recall it, then reveal the answer and rate yourself.",
    ru: "Вспомни, затем покажи ответ и оцени себя.",
  },

  // Focus (leech) list
  "focus.title": { en: "Focus — weak spots", ru: "Фокус — слабые места" },
  "focus.empty": {
    en: "No weak spots yet — keep quizzing!",
    ru: "Слабых мест пока нет — продолжай тесты!",
  },
  "focus.leeches": { en: "skills to drill", ru: "навыков для отработки" },
  "focus.go": { en: "Drill skills →", ru: "Тренировать навыки →" },

  // Stats
  "stats.dueToday": { en: "Due today", ru: "На сегодня" },
  "stats.totalReviews": { en: "Total reviews", ru: "Всего повторов" },
  "stats.streak": { en: "Streak", ru: "Серия" },
  "stats.cardsByState": { en: "Cards by state", ru: "Карточки по статусу" },
  "stats.last7Days": { en: "Last 7 days", ru: "Последние 7 дней" },
  "stats.new": { en: "New", ru: "Новые" },
  "stats.learning": { en: "Learning", ru: "В процессе" },
  "stats.review": { en: "Review", ru: "Повторение" },
  "stats.relearning": { en: "Relearning", ru: "Переучивание" },

  // Import
  "import.format": { en: "Format", ru: "Формат" },
  "import.dryRun": { en: "Preview", ru: "Предпросмотр" },
  "import.commit": { en: "Import words", ru: "Импортировать" },
  "import.placeholder": { en: "Paste your words here…", ru: "Вставь слова сюда…" },
  "import.csv": { en: "CSV", ru: "CSV" },
  "import.markdown": { en: "Markdown", ru: "Markdown" },
  "import.dropFile": { en: "Drop file here", ru: "Перетащите файл сюда" },
  "import.browse": {
    en: "Drop a .csv/.md file or click to browse",
    ru: "Перетащите .csv/.md или нажмите, чтобы выбрать",
  },
  "import.imported": { en: "Imported {count}", ru: "Импортировано: {count}" },
  "import.preview": { en: "Preview: {count} word(s)", ru: "Предпросмотр: {count} слов" },
  "import.lineError": { en: "line {line}: {reason}", ru: "строка {line}: {reason}" },
  "import.formatLabel": { en: "format", ru: "формат" },

  // Onboarding
  "onboarding.welcome": {
    en: "Welcome! Create a deck to get started.",
    ru: "Добро пожаловать! Создай колоду, чтобы начать.",
  },
  "onboarding.firstRun": {
    en: "Your daily review starts here — learn a few new words, then practice them.",
    ru: "Ежедневное повторение начинается здесь — выучи несколько новых слов и потренируйся.",
  },
  "onboarding.step1": { en: "Create a deck", ru: "Создай колоду" },
  "onboarding.step2": { en: "Import words", ru: "Импортируй слова" },
  "onboarding.step3": { en: "Start reviewing", ru: "Начни повторять" },

  // Empty / no-deck states
  "noDeck.title": { en: "No deck yet", ru: "Пока нет колоды" },
  "noDeck.hint": {
    en: "Create one in the sidebar, or import a ready-made word list, then come back here.",
    ru: "Создай её в сайдбаре или импортируй готовый список слов — и возвращайся сюда.",
  },
  "noDeck.import": { en: "Import words", ru: "Импортировать слова" },

  // Profile
  "profile.title": { en: "Profile", ru: "Профиль" },
  "profile.level": { en: "Estimated level", ru: "Предполагаемый уровень" },
  "profile.levelNotAssessed": { en: "Not assessed", ru: "Не определён" },
  "profile.takePlacement": { en: "Take the level test", ru: "Пройти тест уровня" },
  "profile.streak": { en: "Day streak", ru: "Серия дней" },
  "profile.totalReviews": { en: "Total reviews", ru: "Всего повторений" },
  "profile.cardsByState": { en: "Cards by state", ru: "Карточки по состоянию" },
  "profile.curriculum": { en: "Curriculum progress", ru: "Прогресс программы" },
  "profile.displayName": { en: "Display name", ru: "Имя" },
  "profile.saveName": { en: "Save", ru: "Сохранить" },
  "profile.noDeck": {
    en: "Create a deck first, then come back to see your profile.",
    ru: "Сначала создай колоду, потом возвращайся в профиль.",
  },
  "profile.stateNew": { en: "New", ru: "Новые" },
  "profile.stateLearning": { en: "Learning", ru: "В процессе" },
  "profile.stateReview": { en: "Review", ru: "На повторении" },
  "profile.stateRelearning": { en: "Relearning", ru: "Переучивание" },

  // Curriculum / Learn
  "learn.title": { en: "Curriculum", ru: "Учебный план" },
  "learn.subtitle": {
    en: "A guided path from A1 to C2 for active English mastery.",
    ru: "Пошаговый путь от A1 до C2 для уверенного владения английским.",
  },
  "learn.levelA1": { en: "A1 • Beginner", ru: "A1 • Элементарный" },
  "learn.levelA2": { en: "A2 • Elementary", ru: "A2 • Предпороговый" },
  "learn.levelB1": { en: "B1 • Intermediate", ru: "B1 • Средний" },
  "learn.levelB2": { en: "B2 • Upper-Intermediate", ru: "B2 • Выше среднего" },
  "learn.levelC1": { en: "C1 • Advanced", ru: "C1 • Продвинутый" },
  "learn.levelC2": { en: "C2 • Mastery", ru: "C2 • В совершенстве" },
  "learn.trackGrammar": { en: "Grammar", ru: "Грамматика" },
  "learn.trackVocabulary": { en: "Vocabulary", ru: "Словарный запас" },
  "learn.trackPhrasalVerbs": { en: "Phrasal Verbs", ru: "Фразовые глаголы" },
  "learn.trackCollocations": { en: "Collocations", ru: "Коллокации" },
  "learn.trackIdioms": { en: "Idioms", ru: "Идиомы" },
  "learn.trackBusiness": { en: "Business", ru: "Бизнес" },
  "learn.statusNotStarted": { en: "Not started", ru: "Не начато" },
  "learn.statusInProgress": { en: "In progress", ru: "В процессе" },
  "learn.statusCompleted": { en: "Completed", ru: "Завершено" },
  "learn.authoring": { en: "Authoring in progress", ru: "В разработке" },
  "learn.readLesson": { en: "Read lesson", ru: "Читать урок" },
  "learn.markRead": { en: "Mark as read", ru: "Отметить как прочитанное" },
  "learn.markedRead": { en: "Read ✓", ru: "Прочитано ✓" },
  "learn.backToMap": { en: "← Back to Curriculum", ru: "← Назад к плану" },
  "learn.backToLesson": { en: "← Back to lesson", ru: "← Назад к уроку" },
  "learn.startQuiz": { en: "Start quiz", ru: "Начать тест" },
  "learn.objectives": { en: "Objectives", ru: "Цели" },
  "learn.skills": { en: "Skills", ru: "Навыки" },
  "learn.references": { en: "References", ru: "Источники" },
  "learn.estMinutes": { en: "{n} min read", ru: "{n} мин чтения" },
  "learn.skillReviews": { en: "Skill reviews", ru: "Повторение навыков" },
  "learn.takePlacement": { en: "Take placement", ru: "Тест уровня" },

  // Placement (Phase 3)
  "placement.pageTitle": { en: "Placement test", ru: "Тест уровня" },
  "placement.pageHint": {
    en: "Answer each question — your level will be estimated at the end.",
    ru: "Ответь на вопросы — в конце мы определим твой уровень.",
  },
  "placement.title": { en: "Placement test", ru: "Тест уровня" },
  "placement.hint": {
    en: "Answer honestly — there is no pass or fail, only your starting point.",
    ru: "Отвечай честно — здесь нет «провала», только твоя стартовая точка.",
  },
  "placement.level": { en: "Level {level}", ru: "Уровень {level}" },
  "placement.type.mcq": { en: "Choose one", ru: "Выбери один вариант" },
  "placement.type.cloze": { en: "Fill in the gap", ru: "Заполни пропуск" },
  "placement.type.transform": { en: "Rewrite the sentence", ru: "Перепиши предложение" },
  "placement.type.error_correction": { en: "Fix the mistake", ru: "Исправь ошибку" },
  "placement.back": { en: "← Back", ru: "← Назад" },
  "placement.next": { en: "Next →", ru: "Далее →" },
  "placement.submit": { en: "Finish", ru: "Завершить" },
  "placement.doneTitle": { en: "Placement complete", ru: "Тест завершён" },
  "placement.yourLevel": { en: "Your level", ru: "Твой уровень" },
  "placement.doneHint": {
    en: "This is where your curriculum starts — you can always jump to any module from the map.",
    ru: "С этого уровня начинается твой учебный план — открыть любой модуль можно с карты.",
  },
  "placement.startLearning": { en: "Start learning →", ru: "Начать учиться →" },

  // Today
  "nav.today": { en: "Today", ru: "Сегодня" },
  "today.pageTitle": { en: "Today", ru: "Сегодня" },
  "today.pageHint": {
    en: "Your plan for the day, from warm-up to output.",
    ru: "Твой план на день: от разминки до разговорной практики.",
  },
  "today.loading": { en: "Building your plan…", ru: "Собираем план…" },
  "today.error": {
    en: "Failed to load today's plan.",
    ru: "Не удалось загрузить план на сегодня.",
  },
  "today.empty": {
    en: "All caught up — nothing due today.",
    ru: "Всё выполнено — на сегодня ничего не осталось.",
  },
  "today.review.title": { en: "Warm up", ru: "Разминка" },
  "today.review.vocab": { en: "Vocab", ru: "Слова" },
  "today.review.skills": { en: "Skills", ru: "Навыки" },
  "today.learn.readLesson": { en: "Read the lesson", ru: "Прочитай урок" },
  "today.learn.takeQuiz": { en: "Take the quiz", ru: "Пройди тест" },
  "today.learn.items": { en: "Items", ru: "Вопросов" },
  "today.produce.title": { en: "Produce", ru: "Продукция" },
  "today.produce.prompt": { en: "Write a sentence with", ru: "Составь предложение со словом" },
  "today.produce.go": { en: "Open practice →", ru: "К практике →" },
  "today.produce.vocabPrompt": {
    en: "Practice the module's word set:",
    ru: "Потренируй словарный набор модуля:",
  },
  "today.produce.section": { en: "Section", ru: "Раздел" },
  "today.produce.interviewPrompt": {
    en: "Prepare a job-interview topic:",
    ru: "Потренируй тему для собеседования:",
  },
  "today.focus.title": { en: "Focus", ru: "Фокус" },
  "today.focus.leeches": { en: "weak spots", ru: "слабых мест" },
  "today.focus.go": { en: "Drill skills →", ru: "Тренировать навыки →" },
  "progress.title": { en: "Progress", ru: "Прогресс" },
  "progress.hint": {
    en: "A1 → C2. Every level is one step on the path.",
    ru: "A1 → C2. Каждый уровень — шаг на пути.",
  },
  "progress.overall": { en: "Overall", ru: "Общий" },
  "progress.streak": { en: "streak", ru: "дней подряд" },
  "progress.completed": { en: "completed", ru: "пройдено" },
  "progress.loading": { en: "Loading progress…", ru: "Загружаем прогресс…" },
  "progress.error": { en: "Failed to load progress.", ru: "Не удалось загрузить прогресс." },
  "learn.practiceSection": { en: "Practice section", ru: "Раздел практики" },
  "learn.interviewTopic": { en: "Interview topic", ru: "Тема собеседования" },

  // Quiz
  "quiz.title": { en: "Quiz", ru: "Тест" },
  "quiz.hint": {
    en: "Answer every item, then check. Number keys pick options, Enter submits.",
    ru: "Ответь на все пункты, затем проверь. Цифровые клавиши выбирают вариант, Enter отправляет.",
  },
  "quiz.answered": { en: "{n}/{total} answered", ru: "Отвечено: {n}/{total}" },
  "quiz.question": { en: "Question {n}", ru: "Вопрос {n}" },
  "quiz.type.mcq": { en: "Choose one", ru: "Выбери один вариант" },
  "quiz.type.cloze": { en: "Fill in the gap", ru: "Заполни пропуск" },
  "quiz.type.transform": { en: "Rewrite the sentence", ru: "Перепиши предложение" },
  "quiz.type.error_correction": { en: "Fix the mistake", ru: "Исправь ошибку" },
  "quiz.submit": { en: "Check answers", ru: "Проверить" },
  "quiz.resultTitle": { en: "Your results", ru: "Твой результат" },
  "quiz.score": { en: "Score: {score}%", ru: "Результат: {score}%" },
  "quiz.correct": { en: "{n}/{total} correct", ru: "Верно: {n}/{total}" },
  "quiz.completed": { en: "Module completed ✓", ru: "Модуль завершён ✓" },
  "quiz.right": { en: "Correct!", ru: "Верно!" },
  "quiz.wrong": { en: "Not quite.", ru: "Не совсем." },
  "quiz.backToMap": { en: "← Back to Curriculum", ru: "← Назад к плану" },
  "quiz.nextModule": { en: "Next module →", ru: "Следующий модуль →" },

  // Misc
  "misc.translation": { en: "Translation…", ru: "Перевод…" },
  "misc.translationError": { en: "Translation error", ru: "Ошибка перевода" },
  "misc.learn": { en: "Learn a language", ru: "Учи язык" },
  "misc.error": { en: "Error", ru: "Ошибка" },
  "misc.e.g.": { en: "e.g.", ru: "напр." },
};

type I18nValue = {
  t: (key: string) => string;
  locale: Locale;
  setLocale: (l: Locale) => void;
};

const I18nCtx = createContext<I18nValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocale] = useState<Locale>(() => {
    try {
      return (localStorage.getItem("vt_locale") as Locale) || "ru";
    } catch {
      return "ru";
    }
  });

  const setLocaleAndSave = (l: Locale) => {
    setLocale(l);
    try {
      localStorage.setItem("vt_locale", l);
    } catch {}
  };

  const t = useCallback((key: string): string => dict[key]?.[locale] ?? key, [locale]);

  return (
    <I18nCtx.Provider value={{ t, locale, setLocale: setLocaleAndSave }}>
      {children}
    </I18nCtx.Provider>
  );
}

export function useI18n(): I18nValue {
  const ctx = useContext(I18nCtx);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
