import { codePointOffsetMap, type TextSegment } from "./highlights";
import type { Evidence, ReviewSection } from "./types";

export interface ReadingBlockView {
  kind: "paragraph" | "heading";
  segments: TextSegment[];
}

/** Layout ranges are code-point offsets into the unchanged scoring text. */
export function readingBlockViews(
  section: ReviewSection,
  segments: TextSegment[],
): ReadingBlockView[] {
  const text = section.cleaned_text;
  const ranges = section.reading_blocks;
  const codePoints = [...text];
  const offsets = codePointOffsetMap(text);
  const valid =
    ranges?.length &&
    ranges.every(
      (block, index) =>
        Number.isInteger(block.start) &&
        Number.isInteger(block.end) &&
        block.start >= 0 &&
        block.end <= codePoints.length &&
        block.end > block.start &&
        (index === 0 || block.start > ranges[index - 1].end),
    ) &&
    ranges.map((block) => codePoints.slice(block.start, block.end).join("")).join(" ") === text;
  const source = valid
    ? ranges
    : [{ start: 0, end: codePoints.length, kind: "paragraph" as const }];
  return source.map((block) => {
    const start = offsets[block.start];
    const end = offsets[block.end];
    return {
      kind: block.kind,
      segments: segments
        .filter((segment) => segment.start < end && segment.end > start)
        .map((segment) => {
          const sliceStart = Math.max(start, segment.start);
          const sliceEnd = Math.min(end, segment.end);
          return {
            ...segment,
            start: sliceStart,
            end: sliceEnd,
            text: text.slice(sliceStart, sliceEnd),
          };
        }),
    };
  });
}

export interface EvidenceGroup {
  key: string;
  section: string;
  sentence: string;
  hits: Evidence[];
}

export function groupEvidence(evidence: Evidence[]): EvidenceGroup[] {
  const groups = new Map<string, EvidenceGroup>();
  for (const hit of evidence) {
    const key =
      hit.sentence_start != null && hit.sentence_end != null
        ? `${hit.section}:${hit.sentence_start}-${hit.sentence_end}`
        : hit.id;
    const existing = groups.get(key);
    if (existing) {
      existing.hits.push(hit);
    } else {
      groups.set(key, {
        key,
        section: hit.section,
        sentence: hit.sentence,
        hits: [hit],
      });
    }
  }
  return [...groups.values()];
}
