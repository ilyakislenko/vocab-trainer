import "@testing-library/jest-dom/vitest";
import { afterAll, afterEach } from "vitest";
import { server } from "@/shared/test/server";

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
