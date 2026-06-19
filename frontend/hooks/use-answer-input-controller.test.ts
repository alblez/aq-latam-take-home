import { describe, expect, it } from "vitest";
import {
  buildAnswerContent,
  computeAudioDuration,
  computeIsDoneDisabled,
  mergeTranscript,
} from "@/hooks/use-answer-input-controller";

describe("buildAnswerContent", () => {
  it("combines base and interim with space", () => {
    expect(buildAnswerContent("hello", "world")).toBe("hello world");
  });

  it("trims outer whitespace but preserves inner from concatenation", () => {
    expect(buildAnswerContent("  hello  ", "  world  ")).toBe("hello     world");
  });

  it("handles empty base", () => {
    expect(buildAnswerContent("", "interim")).toBe("interim");
  });

  it("handles empty interim", () => {
    expect(buildAnswerContent("base text", "")).toBe("base text");
  });

  it("handles both empty", () => {
    expect(buildAnswerContent("", "")).toBe("");
  });

  it("treats falsy base as empty string", () => {
    expect(buildAnswerContent("", "word")).toBe("word");
  });
});

describe("mergeTranscript", () => {
  it("returns transcript when base is empty", () => {
    expect(mergeTranscript("", "new words")).toBe("new words");
  });

  it("appends with space when base does not end in space", () => {
    expect(mergeTranscript("hello", "world")).toBe("hello world");
  });

  it("appends without extra space when base already ends in space", () => {
    expect(mergeTranscript("hello ", "world")).toBe("hello world");
  });

  it("handles single-word base", () => {
    expect(mergeTranscript("I", "think")).toBe("I think");
  });

  it("preserves existing spacing in base", () => {
    expect(mergeTranscript("I think ", "so")).toBe("I think so");
  });
});

describe("computeAudioDuration", () => {
  it("returns elapsed ms when voice was used (not editing, voice available)", () => {
    const result = computeAudioDuration(false, true, 1000, 4500);
    expect(result).toBe(3500);
  });

  it("returns undefined when user is editing (text fallback)", () => {
    const result = computeAudioDuration(true, true, 1000, 4500);
    expect(result).toBeUndefined();
  });

  it("returns undefined when voice is not available (forced text fallback)", () => {
    const result = computeAudioDuration(false, false, 1000, 4500);
    expect(result).toBeUndefined();
  });

  it("returns undefined when both editing and voice unavailable", () => {
    const result = computeAudioDuration(true, false, 1000, 4500);
    expect(result).toBeUndefined();
  });

  it("returns 0 when now equals micStartTime (immediate submit)", () => {
    const result = computeAudioDuration(false, true, 5000, 5000);
    expect(result).toBe(0);
  });

  it("clamps negative durations to 0 under clock skew", () => {
    const result = computeAudioDuration(false, true, 5000, 4000);
    expect(result).toBe(0);
  });
});

describe("source semantics after recorder deletion", () => {
  it("voice path returns numeric duration → drives inputMode:voice", () => {
    // STT-01: Web Speech final transcript is canonical answerText with inputMode:'voice'
    const result = computeAudioDuration(false, true, 1000, 4500);
    expect(result).toBe(3500);
  });

  it("editing returns undefined → drives inputMode:text", () => {
    // D-02: explicit text fallback when user edits STT-seeded content
    const result = computeAudioDuration(true, true, 1000, 4500);
    expect(result).toBeUndefined();
  });

  it("voice unavailable returns undefined → drives inputMode:text fallback", () => {
    // STT-03: text fallback when mic/STT not available
    const result = computeAudioDuration(false, false, 1000, 4500);
    expect(result).toBeUndefined();
  });

  it("edited STT-seeded text submits as text, not voice", () => {
    // SESS-04 / D-02: candidate edits the STT-seeded textarea then hits Done;
    // source attribution must be text (isEditing=true → undefined duration → inputMode:'text')
    const result = computeAudioDuration(true, true, 1000, 4500);
    expect(result).toBeUndefined();
  });
});

describe("computeIsDoneDisabled", () => {
  it("disabled when no text and no interim", () => {
    expect(computeIsDoneDisabled("", "")).toBe(true);
  });

  it("disabled when text is whitespace only", () => {
    expect(computeIsDoneDisabled("   ", "")).toBe(true);
  });

  it("enabled when answerText has content", () => {
    expect(computeIsDoneDisabled("I think microservices...", "")).toBe(false);
  });

  it("enabled when interimTranscript has content (voice still active)", () => {
    expect(computeIsDoneDisabled("", "some interim words")).toBe(false);
  });

  it("enabled when both have content", () => {
    expect(computeIsDoneDisabled("typed text", "interim")).toBe(false);
  });
});
