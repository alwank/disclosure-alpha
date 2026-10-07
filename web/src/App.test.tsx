import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { App } from "./App";
import { makeReview, makeReviewWithChanges } from "../tests/fixture";

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
      screen.getAllByRole("button", {
        name: /material weakness: material weakness/i,
      })[0],
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
    fireEvent.click(screen.getByRole("button", { name: "Next →" }));
    expect(screen.getByText("3 / 3")).toBeInTheDocument();
  });

  it("shows section counts, including zero, and opens sections from the rail", async () => {
    const fixture = makeReview();
    fixture.sections.push({
      section_name: "item_7_mdna",
      cleaned_text: "No marked phrases here.",
      word_count: 4,
      extraction_confidence: 0.9,
      parser_version: "section_extractor_v1",
      warnings: [],
    });
    fixture.display.section_labels.item_7_mdna = "Item 7 MD&A";
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }),
    );
    await loadReview();
    const rail = screen.getByRole("navigation", { name: "Filing sections" });
    expect(within(rail).getByRole("button", { name: /item 1a risk factors.*1/i })).toBeInTheDocument();
    const emptySection = within(rail).getByRole("button", { name: /item 7 md&a.*0/i });
    fireEvent.click(emptySection);
    expect(emptySection).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("article", { name: "Item 7 MD&A filing text" })).toHaveTextContent(
      "No marked phrases here.",
    );
  });

  it("combines evidence filters, clears hidden selection, and restores all hits", async () => {
    await loadReview();
    fireEvent.click(screen.getAllByRole("button", {
      name: /material weakness: material weakness/i,
    })[0]);
    expect(document.querySelector('[data-selected-hit="true"]')).not.toBeNull();
    fireEvent.change(screen.getByRole("combobox", { name: "Filter evidence by section" }), {
      target: { value: "item_9a_controls" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: "Section" }), {
      target: { value: "item_1a_risk_factors" },
    });
    expect(screen.getByRole("combobox", { name: "Filter evidence by section" }))
      .toHaveValue("item_9a_controls");
    fireEvent.change(screen.getByRole("combobox", { name: "Filter evidence by flag" }), {
      target: { value: "investigation_flag" },
    });
    expect(screen.getByText("No phrases match these filters.")).toBeInTheDocument();
    expect(screen.getByText("0 of 3 phrases")).toBeInTheDocument();
    expect(document.querySelector('[data-selected-hit="true"]')).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
    expect(screen.getByText("3 of 3 phrases")).toBeInTheDocument();
    expect(screen.queryByText("No phrases match these filters.")).toBeNull();
  });

  it("navigates only filtered evidence and reveals overview hits hidden by filters", async () => {
    await loadReview();
    fireEvent.change(screen.getByRole("combobox", { name: "Filter evidence by flag" }), {
      target: { value: "material_weakness_flag" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Next →" }));
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next →" }));
    expect(screen.getByText("2 / 2")).toBeInTheDocument();
    const overview = screen.getByRole("region", { name: "Review overview" });
    fireEvent.click(within(overview).getByRole("button", { name: /investigation/i }));
    expect(screen.getByRole("combobox", { name: "Filter evidence by flag" })).toHaveValue("");
    expect(screen.getByText("1 / 3")).toBeInTheDocument();
  });

  it("orders evidence navigation by section and text position", async () => {
    const fixture = makeReview();
    fixture.evidence.reverse();
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => fixture }),
    );
    await loadReview();
    fireEvent.click(screen.getByRole("button", { name: "Next →" }));
    expect(screen.getByText("1 / 3")).toBeInTheDocument();
    expect(document.querySelector('[data-selected-hit="true"]')).toHaveTextContent("subpoena");
  });

  it("wraps search matches, supports keyboard navigation, and resets on section change", async () => {
    await loadReview();
    fireEvent.change(screen.getByRole("combobox", { name: "Section" }), {
      target: { value: "item_9a_controls" },
    });
    const searchbox = screen.getByRole("searchbox", { name: "Search text" });
    fireEvent.change(searchbox, { target: { value: "material weakness" } });
    expect(screen.getByText("2 matches")).toBeInTheDocument();
    fireEvent.keyDown(searchbox, { key: "Enter" });
    expect(screen.getByText("1 of 2")).toBeInTheDocument();
    expect(document.querySelector(".flag-highlight.search-highlight.active-search-highlight"))
      .toHaveTextContent("material weakness");
    fireEvent.click(screen.getByRole("button", { name: "Previous search match" }));
    expect(screen.getByText("2 of 2")).toBeInTheDocument();
    fireEvent.keyDown(searchbox, { key: "Enter" });
    expect(screen.getByText("1 of 2")).toBeInTheDocument();
    fireEvent.keyDown(searchbox, { key: "Enter", shiftKey: true });
    expect(screen.getByText("2 of 2")).toBeInTheDocument();
    expect(searchbox).toHaveValue("material weakness");
    fireEvent.change(screen.getByRole("combobox", { name: "Section" }), {
      target: { value: "item_1a_risk_factors" },
    });
    expect(searchbox).toHaveValue("material weakness");
    expect(screen.getByText("0 matches")).toBeInTheDocument();
  });

  it("resets navigator state when another filing is opened", async () => {
    await loadReview();
    fireEvent.change(screen.getByRole("combobox", { name: "Filter evidence by flag" }), {
      target: { value: "material_weakness_flag" },
    });
    fireEvent.change(screen.getByRole("searchbox", { name: "Search text" }), {
      target: { value: "subpoena" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Next search match" }));
    fireEvent.change(screen.getByRole("spinbutton", { name: "Fiscal year" }), {
      target: { value: "2024" },
    });
    fireEvent.click(screen.getByRole("button", { name: /open filing/i }));
    await screen.findByText("3 of 3 phrases");
    expect(screen.getByRole("combobox", { name: "Filter evidence by flag" }))
      .toHaveValue("");
    expect(screen.getByRole("searchbox", { name: "Search text" })).toHaveValue("");
    expect(screen.queryByText("1 of 1")).toBeNull();
  });

  it("shows missing score context, provenance, and separate search results", async () => {
    await loadReview();
    expect(
      screen.getByText(/missing scores are shown as/i),
    ).toBeInTheDocument();
    expect(
      screen.getAllByText(/no prior comparison available/i).length,
    ).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole("button", { name: /risk-factor tone/i }));
    expect(screen.getByText(/negative word ratio/i)).toBeInTheDocument();
    fireEvent.change(screen.getByRole("searchbox", { name: "Search text" }), {
      target: { value: "subpoena" },
    });
    expect(document.querySelector(".search-highlight")).toHaveTextContent(
      "subpoena",
    );
    expect(
      screen.getByRole("link", { name: /original sec filing/i }),
    ).toHaveAttribute("href", expect.stringContaining("www.sec.gov"));
  });

  it("ranks section changes and reveals signed drivers without marking text as a diff", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue({
          ok: true,
          json: async () => makeReviewWithChanges(),
        }),
    );
    await loadReview();
    const bars = screen.getAllByRole("button", {
      name: /change magnitude .* out of 100/i,
    });
    expect(bars[0]).toHaveAccessibleName(
      /item 1a risk factors, change magnitude 72.1/i,
    );
    fireEvent.click(bars[0]);
    expect(screen.getByText("0000320193-24-000077")).toBeInTheDocument();
    expect(screen.getByText("+1.25 pp")).toBeInTheDocument();
    expect(screen.getByText("-0.75 pp")).toBeInTheDocument();
    expect(screen.getByText(/sentences added/i)).toBeInTheDocument();
    expect(
      screen.getByText(/change score measures magnitude/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/current filing text · no passage diff/i),
    ).toBeInTheDocument();
    expect(document.querySelector('[data-selected-hit="true"]')).toBeNull();
    expect(document.querySelector(".flag-highlight")).toBeNull();
  });

  it("requires a quarter before requesting a 10-Q", () => {
    render(<App />);
    fireEvent.change(screen.getByLabelText("Form"), {
      target: { value: "10-Q" },
    });
    fireEvent.click(screen.getByRole("button", { name: /open filing/i }));
    expect(screen.getByRole("alert")).toHaveTextContent("Choose Q1, Q2, or Q3");
    expect(
      vi
        .mocked(fetch)
        .mock.calls.some(([url]) => String(url).includes("/filing-review")),
    ).toBe(false);
  });

  it("renders filing markup as text rather than executable HTML", async () => {
    const fixture = makeReview();
    fixture.sections[0].cleaned_text =
      '<script>alert("unsafe")</script> subpoena';
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
