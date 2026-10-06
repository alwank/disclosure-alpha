import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { App } from "./App";
import { makeReview } from "../tests/fixture";

beforeEach(() => {
  window.history.replaceState({}, "", "/app/");
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, json: async () => makeReview() }),
  );
  HTMLElement.prototype.scrollIntoView = vi.fn();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

async function loadReview() {
  render(<App />);
  fireEvent.click(screen.getByRole("button", { name: /open filing/i }));
  await screen.findByRole("heading", { name: "Marked language" });
}

describe("filing review", () => {
  it("selects evidence, switches section, and highlights the exact phrase", async () => {
    await loadReview();
    fireEvent.click(
      screen.getAllByRole("button", { name: /material weakness: material weakness/i })[0],
    );
    expect(screen.getByText("2 / 3")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Item 9A Controls" }),
    ).toBeInTheDocument();
    await waitFor(() =>
      expect(
        document.querySelector('[data-selected-hit="true"]'),
      ).toHaveTextContent("material weakness"),
    );
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    expect(screen.getByText("3 / 3")).toBeInTheDocument();
  });

  it("shows missing score context, provenance, and separate search results", async () => {
    await loadReview();
    expect(
      screen.getByText(/missing scores are not zero/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/no prior comparison available/i),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /risk-factor tone/i }));
    expect(screen.getByText(/negative word ratio/i)).toBeInTheDocument();
    fireEvent.change(
      screen.getByRole("searchbox", { name: "Search text" }),
      { target: { value: "subpoena" } },
    );
    expect(document.querySelector(".search-highlight")).toHaveTextContent(
      "subpoena",
    );
    expect(
      screen.getByRole("link", { name: /original sec filing/i }),
    ).toHaveAttribute("href", expect.stringContaining("www.sec.gov"));
  });

  it("requires a quarter before requesting a 10-Q", () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Form"), {
      target: { value: "10-Q" },
    });
    fireEvent.click(screen.getByRole("button", { name: /open filing/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose Q1, Q2, or Q3");
    expect(
      vi.mocked(fetch).mock.calls.some(([url]) =>
        String(url).includes("/filing-review"),
      ),
    ).toBe(false);
  });

  it("renders filing markup as text rather than executable HTML", async () => {
    const fixture = makeReview();
    fixture.sections[0].cleaned_text = '<script>alert("unsafe")</script> subpoena';
    fixture.evidence = [];
    fixture.display.flag_summary = [];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }),
    );
    await loadReview();
    const article = screen.getByRole("article", {
      name: "Item 1A Risk Factors filing text",
    });
    expect(article).toHaveTextContent('<script>alert("unsafe")</script>');
    expect(article.querySelector("script")).toBeNull();
  });

  it("shows loading and EDGAR errors with retry", async () => {
    let rejectRequest: (reason: Error) => void = () => {};
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(
        () =>
          new Promise((_resolve, reject) => {
            rejectRequest = reject;
          }),
      ),
    );
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: /open filing/i }));
    expect(screen.getByRole("status")).toHaveTextContent(
      "Fetching and analyzing filing",
    );
    rejectRequest(new Error("SEC HTTP 503"));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("SEC HTTP 503"),
    );
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
