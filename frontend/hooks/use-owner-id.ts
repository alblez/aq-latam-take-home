"use client";

import { useEffect } from "react";
import { getOrCreateOwnerId } from "@/lib/owner-id";

/**
 * Side-effect-only hook: ensures an owner ID exists in localStorage on mount.
 * Use when the component needs the ID to exist but doesn't read it.
 */
export function useEnsureOwnerId(): void {
  useEffect(() => {
    getOrCreateOwnerId();
  }, []);
}
