"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { AppHeader } from "@/components/app-header";
import { ChatSidebar } from "@/components/chat-sidebar";
import { Spinner } from "@/components/ui/spinner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const companyId = pathname?.match(/\/dashboard\/companies\/([^/]+)/)?.[1];
  const [chatOpen, setChatOpen] = useState(true);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push("/login");
    }
  }, [user, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-background">
      <AppHeader chatOpen={chatOpen} onChatOpenChange={setChatOpen} />
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <main className="flex flex-1 min-w-0 min-h-0 flex-col overflow-hidden">
          <div className="flex flex-1 min-h-0 overflow-hidden">
            <div className="mx-auto w-full max-w-6xl flex-1 flex min-h-0 flex-col overflow-auto px-6 py-8">
              {children}
            </div>
          </div>
        </main>
        <ChatSidebar
          companyId={companyId}
          open={chatOpen}
          onOpenChange={setChatOpen}
          inline
          hideTrigger
        />
      </div>
    </div>
  );
}
