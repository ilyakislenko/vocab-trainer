import { screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { describe, expect, it } from "vitest";
import { renderWithProviders, server } from "@/shared/test";
import { ProgressDashboard } from "./ProgressDashboard";

const REPORT = {
  levels: [
    { level: "A1", completed: 1, total: 5 },
    { level: "B1", completed: 2, total: 10 },
  ],
  overall_percent: 20,
  streak: 3,
};

describe("ProgressDashboard", () => {
  it("renders per-level completion and overall stats", async () => {
    server.use(http.get("/api/progress", () => HttpResponse.json(REPORT)));
    renderWithProviders(<ProgressDashboard />);

    expect(await screen.findByText(/A1 •/)).toBeInTheDocument();
    expect(screen.getByText("1/5 · 20%")).toBeInTheDocument();
    expect(screen.getByText("2/10 · 20%")).toBeInTheDocument();
    expect(screen.getByText("Общий · 20%")).toBeInTheDocument();
    expect(screen.getByText("3 дней подряд")).toBeInTheDocument();
  });

  it("renders a zero state without a streak", async () => {
    server.use(
      http.get("/api/progress", () =>
        HttpResponse.json({
          levels: [],
          overall_percent: 0,
          streak: 0,
        }),
      ),
    );
    renderWithProviders(<ProgressDashboard />);

    expect(await screen.findByText("Общий · 0%")).toBeInTheDocument();
    expect(screen.queryByText(/дней подряд/)).not.toBeInTheDocument();
  });
});
