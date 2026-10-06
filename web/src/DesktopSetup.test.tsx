import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { App } from "./App";

beforeEach(() => {
  window.history.replaceState({}, "", "/app/");
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("portable desktop setup", () => {
  it("collects the SEC contact on first launch and then shows filing review", async () => {
    const fetchMock = vi.fn().mockImplementation((url: string, init?: RequestInit) => {
      if (url === "/v1/desktop/settings" && !init?.method) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ configured: false, display_name: null }),
        });
      }
      if (url === "/v1/desktop/settings" && init?.method === "PUT") {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({ configured: true, display_name: "Jane Analyst" }),
        });
      }
      return Promise.resolve({ ok: true, status: 204, json: async () => ({}) });
    });
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);
    await screen.findByRole("heading", { name: "Set up SEC filing access" });
    fireEvent.change(screen.getByLabelText("Your name"), {
      target: { value: "Jane Analyst" },
    });
    fireEvent.change(screen.getByLabelText("Contact email"), {
      target: { value: "jane@example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: /continue to filing review/i }));

    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Select a company filing" }),
      ).toBeInTheDocument(),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      "/v1/desktop/settings",
      expect.objectContaining({ method: "PUT" }),
    );
  });

  it("keeps the self-hosted UI available when desktop routes are absent", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 404, json: async () => ({}) }),
    );

    render(<App />);
    await waitFor(() =>
      expect(
        screen.getByRole("heading", { name: "Select a company filing" }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.queryByRole("heading", { name: "Set up SEC filing access" }),
    ).not.toBeInTheDocument();
  });
});
