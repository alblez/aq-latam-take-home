import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { clearPendingTurn, readPendingTurn, writePendingTurn } from "./pending-turn";

// --- In-memory localStorage stub ---

function createLocalStorageStub(): Storage {
  const store = new Map<string, string>();
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
    clear: () => store.clear(),
    get length() {
      return store.size;
    },
    key: (index: number) => [...store.keys()][index] ?? null,
  };
}

describe("pending-turn localStorage record", () => {
  let stub: Storage;

  beforeEach(() => {
    stub = createLocalStorageStub();
    Object.defineProperty(globalThis, "localStorage", {
      value: stub,
      writable: true,
      configurable: true,
    });
  });

  afterEach(() => {
    Object.defineProperty(globalThis, "localStorage", {
      value: undefined,
      writable: true,
      configurable: true,
    });
  });

  it("round-trips a record via write then read", () => {
    const record = {
      clientTurnId: "uuid-abc-123",
      answerText: "My answer",
      inputMode: "text" as const,
    };
    writePendingTurn("sess-1", record);
    expect(readPendingTurn("sess-1")).toEqual(record);
  });

  it("stores under exactly aq_pending_turn_<sessionId> key", () => {
    const record = {
      clientTurnId: "uuid-xyz",
      answerText: "Answer",
      inputMode: "voice" as const,
      audioDurationMs: 5000,
    };
    writePendingTurn("my-session-id", record);
    expect(stub.getItem("aq_pending_turn_my-session-id")).not.toBeNull();
  });

  it("clearPendingTurn removes the record; subsequent read returns null", () => {
    const record = {
      clientTurnId: "uuid-1",
      answerText: "A",
      inputMode: "text" as const,
    };
    writePendingTurn("s1", record);
    clearPendingTurn("s1");
    expect(readPendingTurn("s1")).toBeNull();
  });

  it("readPendingTurn returns null when no record exists", () => {
    expect(readPendingTurn("nonexistent")).toBeNull();
  });

  it("readPendingTurn returns null when stored JSON is malformed", () => {
    stub.setItem("aq_pending_turn_bad", "not-json{{");
    expect(readPendingTurn("bad")).toBeNull();
  });

  it("per-session keying: record for session A is not returned for session B", () => {
    const record = {
      clientTurnId: "uuid-a",
      answerText: "A",
      inputMode: "text" as const,
    };
    writePendingTurn("session-a", record);
    expect(readPendingTurn("session-b")).toBeNull();
  });

  it("preserves caller-supplied clientTurnId verbatim (no ID generation)", () => {
    const myId = "custom-caller-generated-id-42";
    const record = {
      clientTurnId: myId,
      answerText: "Test",
      inputMode: "voice" as const,
      audioDurationMs: 1200,
    };
    writePendingTurn("s1", record);
    const read = readPendingTurn("s1");
    expect(read?.clientTurnId).toBe(myId);
  });
});
