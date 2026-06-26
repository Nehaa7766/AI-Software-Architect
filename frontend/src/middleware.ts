import { NextResponse, type NextRequest } from "next/server";

/**
 * Edge route protection (defense in depth; the dashboard layout also guards
 * client-side). Uses a readable `aisa_auth` flag cookie set by AuthProvider.
 *
 * Note: the real auth proof is the HTTP-only refresh cookie, which the browser
 * sends only to the API. The flag cookie just lets the edge redirect early.
 */
const PROTECTED_PREFIXES = ["/dashboard", "/projects", "/settings", "/profile"];
const AUTH_PAGES = ["/login", "/register", "/forgot-password"];

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  const isAuthed = req.cookies.get("aisa_auth")?.value === "1";

  const isProtected = PROTECTED_PREFIXES.some(
    (p) => pathname === p || pathname.startsWith(`${p}/`),
  );
  const isAuthPage = AUTH_PAGES.some((p) => pathname === p);

  if (isProtected && !isAuthed) {
    const url = req.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("from", pathname);
    return NextResponse.redirect(url);
  }

  if (isAuthPage && isAuthed) {
    const url = req.nextUrl.clone();
    url.pathname = "/dashboard";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/projects/:path*",
    "/settings/:path*",
    "/profile/:path*",
    "/login",
    "/register",
    "/forgot-password",
  ],
};
