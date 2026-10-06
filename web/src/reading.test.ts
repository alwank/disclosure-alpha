import { describe, expect, it } from "vitest";
import { buildSegments } from "./highlights";
import { groupEvidence, readingBlockViews } from "./reading";
import type { Evidence, ReviewSection } from "./types";

describe("source-backed reading layout", () => {
  it("keeps a Unicode evidence highlight when a source block follows it", () => {
    const text = "😀 Alpha. Beta phrase.";
    const section = {
      cleaned_text: text,
      reading_blocks: [
        { start: 0, end: 8, kind: "heading" },
        { start: 9, end: 21, kind: "paragraph" },
      ],
    } as ReviewSection;
    const evidence = [{ id: "hit", start: 14, end: 20 }] as Evidence[];
    const views = readingBlockViews(section, buildSegments(text, evidence, ""));
    expect(views).toHaveLength(2);
    expect(views[0].kind).toBe("heading");
    expect(views[1].segments.find((part) => part.evidenceIds.includes("hit"))?.text)
      .toBe("phrase");
  });

  it("falls back to continuous text when layout data is absent", () => {
    const section = { cleaned_text: "Source text." } as ReviewSection;
    const views = readingBlockViews(section, buildSegments(section.cleaned_text, [], ""));
    expect(views).toHaveLength(1);
    expect(views[0].segments.map((part) => part.text).join("")).toBe("Source text.");
  });

  it("groups only hits from the same source sentence span", () => {
    const evidence = [
      { id: "a", section: "risk", sentence: "Same text", sentence_start: 1, sentence_end: 10 },
      { id: "b", section: "risk", sentence: "Same text", sentence_start: 1, sentence_end: 10 },
      { id: "c", section: "risk", sentence: "Same text", sentence_start: 40, sentence_end: 49 },
    ] as Evidence[];
    expect(groupEvidence(evidence).map((group) => group.hits.map((hit) => hit.id)))
      .toEqual([["a", "b"], ["c"]]);
  });
});
