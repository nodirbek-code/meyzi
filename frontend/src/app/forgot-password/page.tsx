import type { Metadata } from "next";

import { AuthCard } from "@/components/AuthCard";
import { ForgotPasswordForm } from "@/components/ForgotPasswordForm";

export const metadata: Metadata = { title: "Parolni tiklash" };

export default function ForgotPasswordPage() {
  return (
    <AuthCard title="Parolni tiklash">
      <ForgotPasswordForm />
    </AuthCard>
  );
}
