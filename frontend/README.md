# AI Software Architect — Frontend (Auth Module)

Next.js (App Router) + TypeScript + Tailwind + Shadcn-style UI for the auth flows.

## Stack
Next.js 14 · React 18 · TypeScript · Tailwind CSS · react-hook-form + Zod ·
axios (auto token refresh) · @react-oauth/google · sonner (toasts).

## Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local   # cp on *nix
# Set NEXT_PUBLIC_API_URL and NEXT_PUBLIC_GOOGLE_CLIENT_ID
npm run dev
```

App runs at http://localhost:3000 and talks to the FastAPI backend at
`NEXT_PUBLIC_API_URL` (default http://localhost:8000/api).

## Structure

```
src/
  app/
    (auth)/        login, register, forgot-password, reset-password, verify-email
    (dashboard)/   dashboard, projects, settings, profile  (protected)
    layout.tsx     root layout -> Providers
    page.tsx       landing
  components/
    ui/            button, input, label, card (Shadcn-style primitives)
    providers.tsx  GoogleOAuthProvider + AuthProvider + Toaster
  features/auth/
    api/           auth.api.ts, profile.api.ts
    components/     PasswordInput, GoogleButton, FieldError
    context/        AuthProvider (session bootstrap + login/logout)
    hooks/          useAuth
    validators/     auth.schema.ts (Zod; mirrors backend rules)
  lib/
    axios.ts        instance + 401 refresh interceptor; in-memory access token
    utils.ts        cn() helper
  middleware.ts     edge route protection via aisa_auth flag cookie
```

## Auth flow

- Access token kept **in memory** (not localStorage) to limit XSS exposure.
- Refresh token is an HTTP-only cookie managed by the backend.
- On 401, axios silently calls `/auth/refresh` once and retries.
- `middleware.ts` redirects unauthenticated users away from protected routes and
  authenticated users away from the auth pages; the dashboard layout guards again
  client-side.

## UI features
Continue with Google · Remember Me · Show/Hide password · loading states ·
success/error toasts · inline Zod validation · responsive layout.
