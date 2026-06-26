"use client";

import Link from "next/link";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, XCircle } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api, getErrorMessage } from "@/lib/axios";

function VerifyEmailInner() {
  const params = useSearchParams();
  const token = params.get("token");
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setState("error");
      setMessage("This verification link is missing its token.");
      return;
    }
    api
      .get("/auth/verify-email", { params: { token } })
      .then(() => {
        setState("ok");
        setMessage("Your email has been verified.");
      })
      .catch((err) => {
        setState("error");
        setMessage(getErrorMessage(err, "Verification link is invalid or expired."));
      });
  }, [token]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Email verification</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4 py-6 text-center">
        {state === "loading" && <Loader2 className="h-10 w-10 animate-spin text-muted-foreground" />}
        {state === "ok" && <CheckCircle2 className="h-10 w-10 text-green-600" />}
        {state === "error" && <XCircle className="h-10 w-10 text-destructive" />}
        <p className="text-sm text-muted-foreground">{message}</p>
        <Button asChild>
          <Link href="/login">Continue to login</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={null}>
      <VerifyEmailInner />
    </Suspense>
  );
}
