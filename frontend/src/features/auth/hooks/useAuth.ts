"use client";

import { useAuthContext } from "@/features/auth/context/AuthProvider";

/** Convenience hook re-exporting the auth context. */
export function useAuth() {
  return useAuthContext();
}
