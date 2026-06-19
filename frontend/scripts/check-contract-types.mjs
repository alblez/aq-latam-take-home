/**
 * Drift gate + nullability guard for generated contract types.
 *
 * Regenerates types from shared/contract.yaml to a temp file, compares
 * against the committed frontend/types/api/contract.ts, and asserts that
 * critical nullable patterns survive in the output.
 *
 * Exit 0: in sync + nullability intact.
 * Exit 1: drift detected OR nullability guard failed.
 */

import { execSync } from "node:child_process";
import { readFileSync, unlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const COMMITTED = "types/api/contract.ts";
const TEMP = join(tmpdir(), `contract-types-check-${Date.now()}.ts`);

try {
  // Regenerate to temp
  execSync(`npx openapi-typescript ../shared/contract.yaml -o ${TEMP}`, {
    stdio: "pipe",
  });

  // Compare committed vs fresh
  const committed = readFileSync(COMMITTED, "utf8");
  const fresh = readFileSync(TEMP, "utf8");

  if (committed !== fresh) {
    console.error("ERROR: frontend/types/api/contract.ts is out of sync with shared/contract.yaml");
    console.error("Run: just frontend-contract-types");
    process.exit(1);
  }

  // Nullability guards (CGEN-04)
  const guards = [
    {
      pattern: /terminalPanelState.*\| null/,
      label: "TerminalPanelState nullable",
    },
    { pattern: /reasoning\?:.*\| null/, label: "Turn.reasoning nullable" },
    {
      pattern: /JobDetail:\s*components\["schemas"\]\["Job"\]/,
      label: "JobDetail allOf resolves",
    },
  ];

  for (const { pattern, label } of guards) {
    if (!pattern.test(committed)) {
      console.error(`NULLABILITY GUARD FAILED: ${label} not found in generated output`);
      process.exit(1);
    }
  }

  console.log("contract types drift check passed");
} finally {
  try {
    unlinkSync(TEMP);
  } catch {}
}
