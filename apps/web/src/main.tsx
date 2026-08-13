import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./app";
import "./app/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

// Only started for local dev/e2e runs (VITE_ENABLE_MSW=true); production
// builds never bundle or start the mock worker.
async function enableMocking() {
  if (import.meta.env.VITE_ENABLE_MSW !== "true") return;
  const { worker } = await import("./shared/test/browser");
  await worker.start({ onUnhandledRequest: "bypass" });
}

enableMocking().then(() => {
  createRoot(rootElement).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
});
