"use client";

import { GoogleOAuthProvider } from "@react-oauth/google";
import { Toaster } from "sonner";
import type { ReactNode } from "react";
import { AuthProvider } from "@/features/auth/context/AuthProvider";

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "";

export function Providers({ children }: { children: ReactNode }) {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <AuthProvider>
        {children}
        <Toaster richColors position="top-center" />
      </AuthProvider>
    </GoogleOAuthProvider>
  );
}
