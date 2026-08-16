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

describe("InterviewChat", () => {
  it("asks the opening question when a topic is picked", async () => {
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
    expect(speak).toHaveBeenCalled();
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "a function");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const [opening, followUp] = seen as {
      used_question_ids: number[];
    }[];
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: /^RU$/ }));
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "a function");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() => expect(seen).toHaveLength(2));
    const opening = seen[0] as { lang: string };
    const followUp = seen[1] as { lang: string };
    expect(opening.lang).toBe("en");
    expect(followUp.lang).toBe("ru");
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
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
    renderWithProviders(<InterviewChat topic="React" onTopicChange={() => {}} />);
    await waitFor(() => expect(screen.getByText("What are props?")).toBeInTheDocument());
    await userEvent.type(screen.getByPlaceholderText(/answer|ответ/i), "объясни");
    await userEvent.click(screen.getByRole("button", { name: /send|отправить/i }));
    await waitFor(() =>
      expect(screen.getByText("Props это свойства компонента.")).toBeInTheDocument(),
    );
    expect(screen.queryByText(/needs work|нужно подучить/i)).not.toBeInTheDocument();
  });
});
