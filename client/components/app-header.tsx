"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut } from "lucide-react";
import { cn } from "@/lib/utils";

/** VSCode/Cursor-style chat bubble icon: rounded rect outline with filled bottom half */
function ChatIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <rect x="3" y="3" width="18" height="18" rx="3" />
      <rect x="5" y="13" width="14" height="6" rx="1" fill="currentColor" fillOpacity="0.5" />
    </svg>
  );
}

interface AppHeaderProps {
  chatOpen?: boolean;
  onChatOpenChange?: (open: boolean) => void;
}

export function AppHeader({ chatOpen, onChatOpenChange }: AppHeaderProps) {
  const { user, logout } = useAuth();
  const router = useRouter();

  async function handleLogout() {
    await logout();
    router.push("/login");
  }

  return (
    <header className="sticky top-0 z-50 border-b border-foreground/10 bg-background">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-foreground">
            <span className="text-sm font-bold text-background">UC</span>
          </div>
          <span className="text-lg font-semibold tracking-tight">
            UseCase Manager
          </span>
        </div>
        {user && (
          <div className="flex items-center gap-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-9 w-9 rounded-full p-0"
                  aria-label="Account menu"
                >
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-foreground/10 text-foreground text-sm font-medium">
                      {(user.full_name || user.email || "U").charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="min-w-[12rem] border-foreground/10">
                <DropdownMenuLabel className="font-normal">
                  <span className="text-muted-foreground text-xs truncate block">
                    {user.email}
                  </span>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            {typeof onChatOpenChange === "function" && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => onChatOpenChange(!chatOpen)}
                className={cn(
                  "h-10 w-10 text-muted-foreground hover:text-foreground",
                  chatOpen && "bg-foreground/10 text-foreground"
                )}
                title={chatOpen ? "Close chat" : "Open chat"}
              >
                <ChatIcon className="h-5 w-5" />
              </Button>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
