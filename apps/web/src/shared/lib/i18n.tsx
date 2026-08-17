import { createContext, type ReactNode, useCallback, useContext, useState } from "react";

type Locale = "en" | "ru";

type Translations = Record<string, Record<Locale, string>>;

const dict: Translations = {
  // Navigation
  "nav.learn": { en: "Learn", ru: "Изучение" },
  "nav.review": { en: "Review", ru: "Повторение" },
  "nav.practice": { en: "Practice", ru: "Практика" },
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
  "review.caughtUp": { en: "You're all caught up 🎉", ru: "Всё повторено 🎉" },
  "review.summary": { en: "Session complete!", ru: "Сессия завершена!" },
  "review.reviewed": { en: "Cards reviewed", ru: "Карточек пройдено" },
  "review.startAgain": { en: "Start again", ru: "Начать заново" },
  "review.ratingAgain": { en: "Again", ru: "Заново" },
  "review.ratingHard": { en: "Hard", ru: "Сложно" },
  "review.ratingGood": { en: "Good", ru: "Хорошо" },
  "review.ratingEasy": { en: "Easy", ru: "Легко" },

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
  "onboarding.step1": { en: "Create a deck", ru: "Создай колоду" },
  "onboarding.step2": { en: "Import words", ru: "Импортируй слова" },
  "onboarding.step3": { en: "Start reviewing", ru: "Начни повторять" },

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
