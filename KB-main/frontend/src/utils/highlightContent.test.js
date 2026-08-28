import { describe, it, expect } from "vitest";
import { findExcerptRange, splitByExcerpts } from "./highlightContent";

describe("highlightContent", () => {
  it("finds exact excerpt", () => {
    const content = "The PTO policy allows fifteen days per year.";
    const r = findExcerptRange(content, "fifteen days per year");
    expect(r).not.toBeNull();
    expect(content.slice(r.start, r.end)).toBe("fifteen days per year");
  });

  it("splits multiple highlights", () => {
    const content = "AAAA BBBB CCCC DDDD";
    const segs = splitByExcerpts(content, ["BBBB", "DDDD"]);
    expect(segs.filter((s) => s.type === "highlight")).toHaveLength(2);
  });

  it("matches across extra whitespace", () => {
    const content = "The PTO policy allows\n\nfifteen days per year.";
    const r = findExcerptRange(content, "PTO policy allows fifteen days per year");
    expect(r).not.toBeNull();
    expect(content.slice(r.start, r.end)).toMatch(/fifteen/);
  });
});
