"use client";

import { GoogleLogin } from "@react-oauth/google";
import { toast } from "sonner";
import { useRouter } from "next/navigation";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getErrorMessage } from "@/lib/axios";

/**
 * "Continue with Google" button. Renders the official Google widget; on success
 * it sends the ID token to the backend for verification.
 *
 * Requires <GoogleOAuthProvider> (added in the root layout) and
 * NEXT_PUBLIC_GOOGLE_CLIENT_ID to be set.
 */
export function GoogleButton({ redirectTo = "/dashboard" }: { redirectTo?: string }) {
  const { loginWithGoogle } = useAuth();
  const router = useRouter();

  const enabled = !!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
  if (!enabled) {
    return (
      <button
        type="button"
        disabled
        className="flex h-10 w-full items-center justify-center rounded-md border border-input bg-background text-sm text-muted-foreground"
        title="Set NEXT_PUBLIC_GOOGLE_CLIENT_ID to enable Google login"
      >
        Continue with Google (not configured)
      </button>
    );
  }

  return (
    <div className="flex w-full justify-center">
      <GoogleLogin
        onSuccess={async (cred) => {
          try {
            if (!cred.credential) throw new Error("No Google credential");
            await loginWithGoogle(cred.credential);
            toast.success("Signed in with Google");
            router.push(redirectTo);
          } catch (err) {
            toast.error(getErrorMessage(err, "Google sign-in failed"));
          }
        }}
        onError={() => toast.error("Google sign-in failed")}
        width="320"
      />
    </div>
  );
}
