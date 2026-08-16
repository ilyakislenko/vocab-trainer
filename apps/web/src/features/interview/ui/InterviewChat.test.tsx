import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { HttpResponse, http } from "msw";
import { describe, expect, it, vi } from "vitest";
import { renderWithProviders, server } from "@/shared/test";

vi.mock("@/shared/lib/speech", () => ({
  speak: vi.fn(),
  recognizeOnce: vi.fn(),
  startRecognition: vi.fn(),
  isSpeechRecognitionSupported: vi.fn(() => false),
}));

import { isSpeechRecognitionSupported, speak, startRecognition } from "@/shared/lib/speech";
import { InterviewChat } from "./InterviewChat";

async function startInterview() {
  renderWithProviders(<InterviewChat />);
  await userEvent.click(
    screen.getByRole("button", { name: /start interview|начать собеседование/i }),
  );
  await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
}

describe("InterviewChat", () => {
  it("asks the opening question after starting from setup", async () => {
    await startInterview();
    expect(speak).toHaveBeenCalled();
  });

  it("starts with the selected topic and difficulty", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({ question: "What are props?", question_id: 1 });
      }),
    );
    renderWithProviders(<InterviewChat />);
    await userEvent.click(screen.getByRole("button", { name: /^TypeScript$/ }));
    await userEvent.click(screen.getByRole("button", { name: /^(Senior|Сеньор)$/ }));
    await userEvent.click(screen.getByRole("button", { name: /5 questions|5 вопросов/ }));
    await userEvent.click(
      screen.getByRole("button", { name: /start interview|начать собеседование/i }),
    );
    await waitFor(() => expect(seen).toHaveLength(1));
    const opening = seen[0] as { topic: string; difficulty: string; used_question_ids: number[] };
    expect(opening.topic).toBe("TypeScript");
    expect(opening.difficulty).toBe("senior");
    expect(opening.used_question_ids).toEqual([]);
  });

  it("sends an answer and appends feedback plus the next question", async () => {
    server.use(
      http.post("/api/practice/interview", () =>
        HttpResponse.json({
          verdict: "needs_work",
          feedback: "Отвечай полнее.",
          corrected: "A component is a reusable piece of UI.",
          question: "What are props?",
          question_id: 1,
        }),
      ),
    );
    await startInterview();
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "it is a thing");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() => expect(screen.getByText(/Отвечай полнее/)).toBeInTheDocument());
    expect(screen.getByText(/needs work|нужно подучить/i)).toBeInTheDocument();
    expect(screen.getByText(/Better:|Как лучше:/i)).toBeInTheDocument();
  });

  it("puts a spoken answer into the input instead of sending immediately", async () => {
    vi.mocked(isSpeechRecognitionSupported).mockReturnValue(true);
    vi.mocked(startRecognition).mockReturnValue({
      result: Promise.resolve("a component is reusable"),
      stop: vi.fn(),
    });
    await startInterview();
    await userEvent.click(screen.getByRole("button", { name: /voice input|голосовой ввод/i }));
    await userEvent.click(screen.getByRole("button", { name: /stop recording|остановить/i }));
    await waitFor(() =>
      expect(screen.getByPlaceholderText(/answer|ответ/i)).toHaveValue("a component is reusable"),
    );
  });

  it("sends the used question ids so the bank never repeats a question", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: null,
          corrected: null,
          question: "What are props?",
          question_id: 1,
        });
      }),
    );
    await startInterview();
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "a function");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const [opening, followUp] = seen as { used_question_ids: number[] }[];
    expect(opening.used_question_ids).toEqual([]);
    expect(followUp.used_question_ids).toEqual([1]);
  });

  it("sends the chosen question language", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: null,
          corrected: null,
          question: "What are props?",
          question_id: 1,
        });
      }),
    );
    renderWithProviders(<InterviewChat />);
    await userEvent.click(screen.getByRole("button", { name: /^RU$/ }));
    await userEvent.click(
      screen.getByRole("button", { name: /start interview|начать собеседование/i }),
    );
    await waitFor(() => expect(seen).toHaveLength(1));
    const opening = seen[0] as { lang: string };
    expect(opening.lang).toBe("ru");
  });

  it("steers the conversation to a custom topic", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: null,
          corrected: null,
          question: "What are props?",
          question_id: 1,
        });
      }),
    );
    await startInterview();
    await userEvent.type(screen.getByPlaceholderText(/any topic|свою тему/i), "SQL");
    await userEvent.click(screen.getByRole("button", { name: /switch topic|сменить тему/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const steering = seen[1] as { messages: { role: string; content: string }[] };
    const last = steering.messages[steering.messages.length - 1];
    expect(last.role).toBe("user");
    expect(last.content).toBe("Let's talk about SQL.");
  });

  it("requests the next bank question without evaluating an answer", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: null,
          corrected: null,
          question: seen.length === 1 ? "What are props?" : "What is state?",
          question_id: seen.length === 1 ? 1 : 2,
        });
      }),
    );
    await startInterview();
    await userEvent.click(screen.getByRole("button", { name: /next question|следующий вопрос/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const nextReq = seen[1] as { mode: string; messages: unknown[] };
    expect(nextReq.mode).toBe("next");
    expect(nextReq.messages).toEqual([]);
    expect(screen.getByText("What is state?")).toBeInTheDocument();
  });

  it("requests a random bank question", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: null,
          corrected: null,
          question: seen.length === 1 ? "What are props?" : "What is state?",
          question_id: seen.length === 1 ? 1 : 2,
        });
      }),
    );
    await startInterview();
    await userEvent.click(
      screen.getByRole("button", { name: /random question|случайный вопрос/i }),
    );
    await waitFor(() => expect(seen).toHaveLength(2));
    const randReq = seen[1] as { mode: string };
    expect(randReq.mode).toBe("random");
    expect(screen.getByText("What is state?")).toBeInTheDocument();
  });

  it("switches to call view and submits an answer by voice", async () => {
    vi.mocked(isSpeechRecognitionSupported).mockReturnValue(true);
    vi.mocked(startRecognition).mockReturnValue({
      result: Promise.resolve("it is a function"),
      stop: vi.fn(),
    });
    vi.mocked(speak).mockImplementation((_text, onEnd) => onEnd?.());
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: "ok",
          feedback: "Хорошо.",
          corrected: null,
          question: seen.length === 1 ? "What are props?" : "What is state?",
          question_id: seen.length === 1 ? 1 : 2,
        });
      }),
    );
    await startInterview();
    await userEvent.click(screen.getByRole("button", { name: /^Call$|^Звонок$/ }));
    expect(screen.getByText(/tap the mic|микрофон и отвечай/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /voice input|голосовой ввод/i }));
    await userEvent.click(screen.getByRole("button", { name: /stop recording|остановить/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const answer = seen[1] as { messages: { role: string; content: string }[] };
    const last = answer.messages[answer.messages.length - 1];
    expect(last.role).toBe("user");
    expect(last.content).toBe("it is a function");
  });

  it("renders an explanation without a needs-work banner", async () => {
    const seen: unknown[] = [];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: null,
          feedback: "Props это свойства компонента.",
          corrected: null,
          question: seen.length === 1 ? "What are props?" : "What are props used for?",
          question_id: seen.length === 1 ? 1 : null,
        });
      }),
    );
    await startInterview();
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "объясни");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() =>
      expect(screen.getByText("Props это свойства компонента.")).toBeInTheDocument(),
    );
    expect(screen.queryByText(/needs work|нужно подучить/i)).not.toBeInTheDocument();
  });

  it("shows a summary with good/needs-work counts after a bounded session", async () => {
    const seen: unknown[] = [];
    const questions = ["What are props?", "What is state?", "What is a hook?"];
    server.use(
      http.post("/api/practice/interview", async ({ request }) => {
        const body = await request.json();
        seen.push(body);
        return HttpResponse.json({
          verdict: "ok",
          feedback: "Хорошо.",
          corrected: null,
          question: questions[seen.length - 1],
          question_id: seen.length,
        });
      }),
    );
    renderWithProviders(<InterviewChat />);
    await userEvent.click(screen.getByRole("button", { name: /3 questions|3 вопросов/ }));
    await userEvent.click(
      screen.getByRole("button", { name: /start interview|начать собеседование/i }),
    );
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
    for (const question of ["What are props?", "What is state?"]) {
      await waitFor(() => expect(screen.getByText(question)).toBeInTheDocument());
      await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "a function");
      await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    }
    await waitFor(() =>
      expect(screen.getByText(/interview complete|собеседование завершено/i)).toBeInTheDocument(),
    );
    expect(screen.getByText(/good answers|хороших ответов/i)).toBeInTheDocument();
    expect(screen.getByText(/start again|ещё раз/i)).toBeInTheDocument();
  });

  it("finishes the session from the header and starts again from the summary", async () => {
    await startInterview();
    await userEvent.click(screen.getByRole("button", { name: /finish|завершить/i }));
    await waitFor(() =>
      expect(screen.getByText(/interview complete|собеседование завершено/i)).toBeInTheDocument(),
    );
    await userEvent.click(screen.getByRole("button", { name: /start again|ещё раз/i }));
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
  });

  it("returns to setup from the summary", async () => {
    await startInterview();
    await userEvent.click(screen.getByRole("button", { name: /finish|завершить/i }));
    await waitFor(() =>
      expect(screen.getByText(/interview complete|собеседование завершено/i)).toBeInTheDocument(),
    );
    await userEvent.click(
      screen.getByRole("button", { name: /change settings|изменить настройки/i }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /start interview|начать собеседование/i }),
      ).toBeInTheDocument(),
    );
  });
});
