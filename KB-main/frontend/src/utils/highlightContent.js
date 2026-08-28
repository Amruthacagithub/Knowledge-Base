/**
 * Find excerpt position in document content (fuzzy match).
 */
import { excerptForHighlight } from "./citationExcerpt";

function normalizeWhitespace(s) {
  return s.replace(/\s+/g, " ").trim();
}

function escapeRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Build candidate needles (longest first) for matching a chunk in full document text.
 */
export function buildHighlightNeedles(excerpt) {
  if (!excerpt?.trim()) return [];

  const text = excerpt.trim();
  const needles = new Set();

  const add = (value) => {
    if (value?.trim()) needles.add(value.trim());
  };

  add(text);
  add(excerptForHighlight(text, 800));
  add(excerptForHighlight(text, 480));

  const strippedMd = text.replace(/^#{1,6}\s+/gm, "").trim();
  if (strippedMd !== text) {
    add(strippedMd);
    add(excerptForHighlight(strippedMd, 480));
  }

  for (const len of [400, 300, 200, 120, 80, 50]) {
    if (text.length >= len) {
      add(text.slice(0, len));
      add(text.slice(-len));
    }
  }

  return [...needles].sort((a, b) => b.length - a.length);
}

/**
 * Word-sequence match tolerates whitespace / line-break differences.
 */
function findByWordSequence(content, excerpt) {
  const words = normalizeWhitespace(excerpt).split(" ").filter((w) => w.length > 1);
  if (words.length < 4) return null;

  const pattern = words.map(escapeRegex).join("\\s+");
  try {
    const re = new RegExp(pattern, "i");
    const m = re.exec(content);
    if (m) {
      return { start: m.index, end: m.index + m[0].length, needle: m[0] };
    }
  } catch {
    return null;
  }
  return null;
}

function findExcerptRangeOnce(content, excerpt) {
  if (!content || !excerpt?.trim()) return null;

  let needle = excerpt.trim();
  let idx = content.indexOf(needle);

  if (idx === -1) {
    const nNeedle = normalizeWhitespace(needle);
    const nContent = normalizeWhitespace(content);
    const nIdx = nContent.indexOf(nNeedle);
    if (nIdx !== -1 && nNeedle.length >= 40) {
      const wordRange = findByWordSequence(content, nNeedle);
      if (wordRange) return wordRange;
    }

    for (const len of [300, 200, 120, 80, 50]) {
      if (needle.length >= len) {
        const short = needle.slice(0, len);
        idx = content.indexOf(short);
        if (idx !== -1) {
          needle = short;
          break;
        }
        const wordRange = findByWordSequence(content, short);
        if (wordRange) return wordRange;
      }
    }
  }

  if (idx === -1) {
    return findByWordSequence(content, needle);
  }

  return { start: idx, end: idx + needle.length, needle };
}

export function findExcerptRange(content, excerpt) {
  if (!content || !excerpt?.trim()) return null;

  for (const needle of buildHighlightNeedles(excerpt)) {
    const range = findExcerptRangeOnce(content, needle);
    if (range) return range;
  }
  return null;
}

/**
 * Split document text into before / match / after for a single excerpt.
 */
export function splitByExcerpt(content, excerpt) {
  const range = findExcerptRange(content, excerpt);
  if (!range) {
    return { before: content || "", match: null, after: "" };
  }
  return {
    before: content.slice(0, range.start),
    match: content.slice(range.start, range.end),
    after: content.slice(range.end),
  };
}

/**
 * Split content into alternating normal / highlight segments for multiple excerpts.
 */
export function splitByExcerpts(content, excerpts) {
  if (!content) return [{ type: "normal", text: "" }];

  const raw = Array.isArray(excerpts) ? excerpts : [excerpts];
  const list = raw
    .flatMap((e) => {
      if (typeof e !== "string" || !e.trim()) return [];
      const trimmed = e.trim();
      if (trimmed.length <= 700) return [trimmed];
      return buildHighlightNeedles(trimmed);
    })
    .filter(Boolean);

  const uniqueNeedles = [...new Set(list)];

  if (!uniqueNeedles.length) {
    return [{ type: "normal", text: content }];
  }

  const ranges = [];
  for (const excerpt of uniqueNeedles) {
    const range = findExcerptRangeOnce(content, excerpt);
    if (range) ranges.push(range);
  }

  if (!ranges.length) {
    for (const excerpt of uniqueNeedles) {
      const range = findByWordSequence(content, excerpt);
      if (range) ranges.push(range);
    }
  }

  if (!ranges.length) {
    return [{ type: "normal", text: content }];
  }

  ranges.sort((a, b) => a.start - b.start);

  const merged = [];
  for (const r of ranges) {
    const last = merged[merged.length - 1];
    if (!last || r.start > last.end) {
      merged.push({ ...r });
    } else {
      last.end = Math.max(last.end, r.end);
    }
  }

  const segments = [];
  let pos = 0;
  for (const r of merged) {
    if (r.start > pos) {
      segments.push({ type: "normal", text: content.slice(pos, r.start) });
    }
    segments.push({ type: "highlight", text: content.slice(r.start, r.end) });
    pos = r.end;
  }
  if (pos < content.length) {
    segments.push({ type: "normal", text: content.slice(pos) });
  }
  return segments;
}
