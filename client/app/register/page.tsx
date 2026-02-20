"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { RegisterForm } from "@/components/register-form";

export default function RegisterPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) return null;

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-4">
      <RegisterForm />
    </main>
  );
}
