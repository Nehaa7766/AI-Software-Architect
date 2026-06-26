import { api } from "@/lib/axios";

export type AuthProvider = "LOCAL" | "GOOGLE";

export interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  provider: AuthProvider;
  profile_image: string | null;
  email_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  token_type: string;
}

export interface MessageResponse {
  message: string;
}

export const authApi = {
  register: (data: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
    confirm_password: string;
  }) => api.post<AuthResponse>("/auth/register", data).then((r) => r.data),

  login: (data: { email: string; password: string; remember_me?: boolean }) =>
    api.post<AuthResponse>("/auth/login", data).then((r) => r.data),

  google: (idToken: string) =>
    api.post<AuthResponse>("/auth/google", { id_token: idToken }).then((r) => r.data),

  refresh: () => api.post<AuthResponse>("/auth/refresh", {}).then((r) => r.data),

  logout: () => api.post<MessageResponse>("/auth/logout", {}).then((r) => r.data),

  me: () => api.get<User>("/auth/me").then((r) => r.data),

  forgotPassword: (email: string) =>
    api.post<MessageResponse>("/auth/forgot-password", { email }).then((r) => r.data),

  resetPassword: (data: { token: string; password: string; confirm_password: string }) =>
    api.post<MessageResponse>("/auth/reset-password", data).then((r) => r.data),
};
