import { describe, expect, it } from "vitest";
import { buildSegments, codePointOffsetMap, searchRanges } from "./highlights";
import type { Evidence } from "./types";

describe("filing highlights", () => {
  it("maps Python code-point offsets after an astral Unicode character", () => {
    const text = "😀 material weakness";
    const evidence = [{ id: "hit", start: 2, end: 19 }] as Evidence[];
    const marked = buildSegments(text, evidence, "");
    expect(codePointOffsetMap(text)[2]).toBe(3);
    expect(marked.find((part) => part.evidenceIds.includes("hit"))?.text).toBe(
      "material weakness",
    );
  });

  it("keeps independent search ranges alongside flag ranges", () => {
    const text = "subpoena and subpoena";
    const evidence = [{ id: "flag", start: 0, end: 8 }] as Evidence[];
    expect(searchRanges(text, "subpoena")).toHaveLength(2);
    const parts = buildSegments(text, evidence, "subpoena");
    expect(
      parts.find((part) => part.evidenceIds.includes("flag"))?.search,
    ).toBe(true);
    expect(
      parts.filter((part) => part.search && !part.evidenceIds.length),
    ).toHaveLength(1);
  });
});
