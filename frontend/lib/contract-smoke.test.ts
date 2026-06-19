import { describe, expect, it } from "vitest";
import type { components } from "@/types/api/contract";

describe("generated contract types", () => {
  it("expose the error code enum", () => {
    type Code = components["schemas"]["ErrorResponse"]["error"]["code"];
    const known: Code[] = [
      "invalid_owner_id",
      "job_not_found",
      "session_not_found",
      "session_not_in_progress",
      "session_in_progress",
      "turn_already_submitted",
      "validation_error",
      "model_unavailable",
      "catalog_setup_error",
    ];
    expect(known).toContain("invalid_owner_id");
  });
});
