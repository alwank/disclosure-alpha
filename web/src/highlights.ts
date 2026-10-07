import type { Evidence } from "./types";

export interface TextSegment {
  start: number;
  end: number;
  text: string;
  evidenceIds: string[];
  search: boolean;
}

/** Python offsets count Unicode code points; DOM strings use UTF-16 positions. */
export function codePointOffsetMap(text: string): number[] {
  const offsets = [0];
  let utf16 = 0;
  for (const character of text) {
    utf16 += character.length;
    offsets.push(utf16);
  }
  return offsets;
}

export function searchRanges(
  text: string,
  query: string,
): Array<[number, number]> {
  if (!query.trim()) return [];
  const escaped = query.trim().replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const matches: Array<[number, number]> = [];
  for (const match of text.matchAll(new RegExp(escaped, "gi"))) {
    matches.push([match.index, match.index + match[0].length]);
  }
  return matches;
}

export function buildSegments(
  text: string,
  evidence: Evidence[],
  query: string,
): TextSegment[] {
  const offsetMap = codePointOffsetMap(text);
  const marked = evidence
    .map((item) => ({
      id: item.id,
      start: offsetMap[item.start],
      end: offsetMap[item.end],
    }))
    .filter(
      (item) =>
        item.start !== undefined &&
        item.end !== undefined &&
        item.start < item.end,
    );
  const searched = searchRanges(text, query);
  const boundaries = new Set([0, text.length]);
  for (const item of marked) {
    boundaries.add(item.start);
    boundaries.add(item.end);
  }
  for (const [start, end] of searched) {
    boundaries.add(start);
    boundaries.add(end);
  }
  const positions = [...boundaries].sort((a, b) => a - b);
  const segments: TextSegment[] = [];
  for (let index = 0; index < positions.length - 1; index += 1) {
    const start = positions[index];
    const end = positions[index + 1];
    if (start === end) continue;
    segments.push({
      start,
      end,
      text: text.slice(start, end),
      evidenceIds: marked
        .filter((item) => item.start < end && item.end > start)
        .map((item) => item.id),
      search: searched.some(
        ([searchStart, searchEnd]) => searchStart < end && searchEnd > start,
      ),
    });
  }
  return segments;
}
