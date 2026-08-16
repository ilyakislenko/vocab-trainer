import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach, beforeAll, beforeEach } from "vitest";
import { llmCache } from "@/shared/lib/llm-cache";
import { server } from "@/shared/test/server";

// Reset the persistent LLM cache so one test's cached explanation/example does
// not leak into another test's assertions.
beforeEach(() => void llmCache.clear());

// Mock Web Audio API for sound effects (jsdom has no AudioContext)
beforeAll(() => {
  (globalThis as any).AudioContext = class {
    createOscillator() {
      return { connect: () => ({ connect: () => {} }), start: () => {}, stop: () => {} };
    }
    createGain() {
      return { gain: { setValueAtTime: () => {}, exponentialRampToValueAtTime: () => {} } };
    }
    get currentTime() {
      return 0;
    }
    get destination() {
      return {};
    }
  };
});

// Node's native fetch/Request (unlike a real browser) cannot resolve relative
// URLs against a page origin, but the api client intentionally uses a relative
// baseUrl ("/api") so the Vite dev proxy works in the browser. Resolve relative
// input against jsdom's window.location before it reaches the native Request
// constructor, so MSW's fetch interceptor gets an absolute, matchable URL.
const NativeRequest = globalThis.Request;

class ResolvedRequest extends NativeRequest {
  constructor(input: RequestInfo | URL, init?: RequestInit) {
    super(typeof input === "string" ? new URL(input, window.location.href) : input, init);
  }
}

globalThis.Request = ResolvedRequest as typeof Request;

// openapi-fetch's client binds `globalThis.fetch` once at import time, so the
// server must patch fetch synchronously here rather than inside beforeAll —
// beforeAll only runs after every test file's top-level imports (and thus the
// api client's module-scope `createClient()` call) have already evaluated.
server.listen({ onUnhandledRequest: "error" });
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
