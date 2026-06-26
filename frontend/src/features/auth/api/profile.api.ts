import { api } from "@/lib/axios";
import type { User } from "@/features/auth/api/auth.api";

export const profileApi = {
  get: () => api.get<User>("/profile").then((r) => r.data),

  update: (data: { first_name?: string; last_name?: string }) =>
    api.patch<User>("/profile", data).then((r) => r.data),

  changePassword: (data: {
    current_password: string;
    new_password: string;
    confirm_password: string;
  }) => api.post("/profile/change-password", data).then((r) => r.data),

  uploadAvatar: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api
      .post<User>("/profile/avatar", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
};
