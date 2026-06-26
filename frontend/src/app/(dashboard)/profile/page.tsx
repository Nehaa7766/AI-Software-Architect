"use client";

import { useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, Upload } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { PasswordInput } from "@/features/auth/components/PasswordInput";
import { FieldError } from "@/features/auth/components/FieldError";
import { resetPasswordSchema } from "@/features/auth/validators/auth.schema";
import { profileApi } from "@/features/auth/api/profile.api";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getErrorMessage } from "@/lib/axios";
import { z } from "zod";

const API_ORIGIN = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/api\/?$/, "");

const profileSchema = z.object({
  first_name: z.string().min(1, "Required").max(100),
  last_name: z.string().min(1, "Required").max(100),
});
type ProfileValues = z.infer<typeof profileSchema>;

const changePasswordSchema = resetPasswordSchema.and(
  z.object({ currentPassword: z.string().min(1, "Required") }),
);
type ChangePasswordValues = z.infer<typeof changePasswordSchema>;

export default function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: { first_name: user?.first_name ?? "", last_name: user?.last_name ?? "" },
  });

  const passwordForm = useForm<ChangePasswordValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { currentPassword: "", password: "", confirmPassword: "" },
  });

  const onSaveProfile = async (values: ProfileValues) => {
    try {
      await profileApi.update(values);
      await refreshUser();
      toast.success("Profile updated");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const onChangePassword = async (values: ChangePasswordValues) => {
    try {
      await profileApi.changePassword({
        current_password: values.currentPassword,
        new_password: values.password,
        confirm_password: values.confirmPassword,
      });
      passwordForm.reset();
      toast.success("Password changed");
    } catch (err) {
      toast.error(getErrorMessage(err));
    }
  };

  const onPickAvatar = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      await profileApi.uploadAvatar(file);
      await refreshUser();
      toast.success("Avatar updated");
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const avatarUrl = user?.profile_image
    ? user.profile_image.startsWith("http")
      ? user.profile_image
      : `${API_ORIGIN}${user.profile_image}`
    : null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">Profile</h1>

      {/* Avatar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Profile image</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          <div className="flex h-16 w-16 items-center justify-center overflow-hidden rounded-full bg-secondary text-lg font-medium">
            {avatarUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={avatarUrl} alt="Avatar" className="h-full w-full object-cover" />
            ) : (
              <span>{user?.first_name?.[0] ?? user?.email?.[0]?.toUpperCase()}</span>
            )}
          </div>
          <div>
            <input
              ref={fileRef}
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={onPickAvatar}
            />
            <Button
              variant="outline"
              onClick={() => fileRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Upload className="h-4 w-4" />
              )}
              Upload new image
            </Button>
            <p className="mt-1 text-xs text-muted-foreground">JPEG, PNG, or WebP, max 2MB.</p>
          </div>
        </CardContent>
      </Card>

      {/* Details */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Account details</CardTitle>
          <CardDescription>{user?.email}</CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={profileForm.handleSubmit(onSaveProfile)}
            className="space-y-4"
            noValidate
          >
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="first_name">First name</Label>
                <Input id="first_name" {...profileForm.register("first_name")} />
                <FieldError message={profileForm.formState.errors.first_name?.message} />
              </div>
              <div>
                <Label htmlFor="last_name">Last name</Label>
                <Input id="last_name" {...profileForm.register("last_name")} />
                <FieldError message={profileForm.formState.errors.last_name?.message} />
              </div>
            </div>
            <Button type="submit" disabled={profileForm.formState.isSubmitting}>
              {profileForm.formState.isSubmitting && (
                <Loader2 className="h-4 w-4 animate-spin" />
              )}
              Save changes
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Change password (local accounts only) */}
      {user?.provider === "LOCAL" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Change password</CardTitle>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={passwordForm.handleSubmit(onChangePassword)}
              className="space-y-4"
              noValidate
            >
              <div>
                <Label htmlFor="currentPassword">Current password</Label>
                <PasswordInput
                  id="currentPassword"
                  autoComplete="current-password"
                  {...passwordForm.register("currentPassword")}
                />
                <FieldError
                  message={passwordForm.formState.errors.currentPassword?.message}
                />
              </div>
              <div>
                <Label htmlFor="newPassword">New password</Label>
                <PasswordInput
                  id="newPassword"
                  autoComplete="new-password"
                  {...passwordForm.register("password")}
                />
                <FieldError message={passwordForm.formState.errors.password?.message} />
              </div>
              <div>
                <Label htmlFor="confirmNewPassword">Confirm new password</Label>
                <PasswordInput
                  id="confirmNewPassword"
                  autoComplete="new-password"
                  {...passwordForm.register("confirmPassword")}
                />
                <FieldError
                  message={passwordForm.formState.errors.confirmPassword?.message}
                />
              </div>
              <Button type="submit" disabled={passwordForm.formState.isSubmitting}>
                {passwordForm.formState.isSubmitting && (
                  <Loader2 className="h-4 w-4 animate-spin" />
                )}
                Update password
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
