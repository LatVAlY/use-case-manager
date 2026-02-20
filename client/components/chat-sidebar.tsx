"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageSquare, X, Upload, Send, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const getWsUrl = () => {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
  const clean = base.replace(/\/$/, "");
  return clean.startsWith("https") ? clean.replace(/^https/, "wss") : clean.replace(/^http/, "ws");
};
const WS_BASE = getWsUrl();

const markdownComponents: React.ComponentProps<typeof ReactMarkdown>["components"] = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-2 list-disc pl-4 space-y-1">{children}</ul>,
  ol: ({ children }) => <ol className="my-2 list-decimal pl-4 space-y-1">{children}</ol>,
  li: ({ children }) => <li className="leading-relaxed">{children}</li>,
  code: ({ className, children, ...props }) =>
    className ? (
      <code className={cn("rounded px-1 py-0.5 text-xs font-mono bg-foreground/10", className)} {...props}>
        {children}
      </code>
    ) : (
      <code className="rounded px-1 py-0.5 text-xs font-mono bg-foreground/10" {...props}>
        {children}
      </code>
    ),
  pre: ({ children }) => (
    <pre className="my-2 overflow-x-auto rounded-lg bg-foreground/10 p-3 text-xs font-mono">
      {children}
    </pre>
  ),
  h1: ({ children }) => <h1 className="text-base font-bold mt-3 mb-1 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-sm font-bold mt-3 mb-1 first:mt-0">{children}</h2>,
  h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 first:mt-0">{children}</h3>,
  strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
  a: ({ href, children, ...props }) => (
    <a
      href={href ?? "#"}
      target="_blank"
      rel="noopener noreferrer"
      className="text-primary underline hover:no-underline"
      {...props}
    >
      {children}
    </a>
  ),
  blockquote: ({ children }) => (
    <blockquote className="border-l-2 border-foreground/20 pl-3 my-2 text-muted-foreground italic">
      {children}
    </blockquote>
  ),
};

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
}

interface ChatSidebarProps {
  companyId?: string;
  className?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  /** When true, chat pushes layout instead of overlaying */
  inline?: boolean;
  /** When true, don't render the trigger button (e.g. when it's in the header) */
  hideTrigger?: boolean;
}

export function ChatSidebar({ companyId, className, open: controlledOpen, onOpenChange, inline, hideTrigger }: ChatSidebarProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen ?? internalOpen;
  const setOpen = onOpenChange ?? setInternalOpen;
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState("");
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const streamAccumulatorRef = useRef("");

  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const wsUrl = token ? `${WS_BASE}/chat/ws?token=${encodeURIComponent(token)}` : null;

  const connect = useCallback(() => {
    if (!wsUrl) return;
    const ws = new WebSocket(wsUrl);
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type === "message") {
          setMessages((prev) => [
            ...prev,
            { id: crypto.randomUUID(), role: data.role || "assistant", content: data.content },
          ]);
        } else if (data.type === "chunk") {
          streamAccumulatorRef.current += data.content || "";
          setStreamContent(streamAccumulatorRef.current);
        } else if (data.type === "done") {
          const full = streamAccumulatorRef.current;
          streamAccumulatorRef.current = "";
          setStreamContent("");
          setStreaming(false);
          if (full) {
            setMessages((prev) => [
              ...prev,
              { id: crypto.randomUUID(), role: "assistant", content: full },
            ]);
          }
        } else if (data.type === "error") {
          streamAccumulatorRef.current = "";
          setStreaming(false);
          setStreamContent("");
          setMessages((prev) => [
            ...prev,
            { id: crypto.randomUUID(), role: "assistant", content: `Error: ${data.message}` },
          ]);
        }
      } catch {
        // ignore
      }
    };
    wsRef.current = ws;
    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [wsUrl]);

  useEffect(() => {
    if (wsUrl) {
      const cleanup = connect();
      return cleanup;
    }
  }, [wsUrl, connect]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamContent]);

  const send = (content: string) => {
    if (!content.trim() || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    setStreaming(true);
    setStreamContent("");
    wsRef.current.send(JSON.stringify({ type: "message", content: content.trim() }));
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: "user", content: content.trim() }]);
    setInput("");
  };

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN || !companyId) return;
    const reader = new FileReader();
    reader.onload = () => {
      const b64 = (reader.result as string).split(",")[1] || reader.result;
      wsRef.current?.send(
        JSON.stringify({
          type: "upload",
          filename: file.name,
          content: b64,
          company_id: companyId,
        })
      );
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "user", content: `Uploaded ${file.name}` },
      ]);
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <>
      {!inline && !hideTrigger && (
        <Button
          variant="outline"
          size="icon"
          onClick={() => setOpen(true)}
          className={cn("fixed bottom-6 right-6 z-40 h-12 w-12 rounded-full border-foreground/20", className)}
          title="Open chat"
        >
          <MessageSquare className="h-5 w-5" />
        </Button>
      )}

      {inline ? (
        <>
          {!open && !hideTrigger && (
            <Button
              variant="outline"
              size="icon"
              onClick={() => setOpen(true)}
              className={cn("fixed bottom-6 right-6 z-40 h-12 w-12 rounded-full border-foreground/20 shrink-0", className)}
              title="Open chat"
            >
              <MessageSquare className="h-5 w-5" />
            </Button>
          )}
          {open && (
            <div className="flex w-[420px] shrink-0 flex-col min-h-0 overflow-hidden border-l border-foreground/10 bg-background">
              <div className="flex h-14 items-center justify-between border-b border-foreground/10 px-4">
                <h3 className="font-semibold">Assistant</h3>
                <Button variant="ghost" size="icon" onClick={() => setOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <ScrollArea className="flex-1 min-h-0 p-4">
                <div className="space-y-4">
                  {messages.length === 0 && !streaming && (
                    <div className="rounded-lg border border-dashed border-foreground/20 bg-foreground/5 p-6 text-center text-sm text-muted-foreground">
                      <p className="mb-2">Chat with the transcript assistant.</p>
                      <p>Ask about transcripts, use cases, or upload a transcript directly here.</p>
                    </div>
                  )}
                  {messages.map((m) => (
                    <div
                      key={m.id}
                      className={cn(
                        "rounded-lg px-3 py-2 text-sm",
                        m.role === "user" ? "ml-8 bg-foreground/10" : "mr-8 bg-muted"
                      )}
                    >
                      {m.role === "user" ? (
                        <div className="whitespace-pre-wrap">{m.content}</div>
                      ) : (
                        <div className="[&>*:last-child]:mb-0">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                            {m.content}
                          </ReactMarkdown>
                        </div>
                      )}
                    </div>
                  ))}
                  {streaming && streamContent && (
                    <div className="mr-8 rounded-lg bg-muted px-3 py-2 text-sm">
                      <div className="[&>*:last-child]:mb-0">
                        <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                          {streamContent}
                        </ReactMarkdown>
                      </div>
                      <Loader2 className="mt-1 h-4 w-4 animate-spin text-muted-foreground" />
                    </div>
                  )}
                  <div ref={scrollRef} />
                </div>
              </ScrollArea>
              <div className="border-t border-foreground/10 p-4">
                <div className="flex gap-2">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".txt,.md,.pdf,.doc,.docx"
                    onChange={handleUpload}
                    className="hidden"
                  />
                  {companyId && (
                    <Button
                      variant="outline"
                      size="icon"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={!connected || streaming}
                      title="Upload transcript"
                      className="shrink-0 border-foreground/20"
                    >
                      <Upload className="h-4 w-4" />
                    </Button>
                  )}
                  <Input
                    placeholder="Ask about transcripts or use cases..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
                    disabled={!connected || streaming}
                    className="flex-1 border-foreground/20"
                  />
                  <Button
                    size="icon"
                    onClick={() => send(input)}
                    disabled={!connected || streaming || !input.trim()}
                    className="shrink-0"
                  >
                    {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                  </Button>
                </div>
                {!connected && open && (
                  <p className="mt-2 text-xs text-muted-foreground">Connecting...</p>
                )}
              </div>
            </div>
          )}
        </>
      ) : (
      <div
        className={cn(
          "fixed right-0 top-0 z-50 flex h-full w-full flex-col border-l border-foreground/10 bg-background shadow-xl transition-transform duration-200 md:w-[420px]",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex h-14 items-center justify-between border-b border-foreground/10 px-4">
          <h3 className="font-semibold">Assistant</h3>
          <Button variant="ghost" size="icon" onClick={() => setOpen(false)}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.length === 0 && !streaming && (
              <div className="rounded-lg border border-dashed border-foreground/20 bg-foreground/5 p-6 text-center text-sm text-muted-foreground">
                <p className="mb-2">Chat with the transcript assistant.</p>
                <p>Ask about transcripts, use cases, or upload a transcript directly here.</p>
              </div>
            )}
            {messages.map((m) => (
              <div
                key={m.id}
                className={cn(
                  "rounded-lg px-3 py-2 text-sm",
                  m.role === "user"
                    ? "ml-8 bg-foreground/10"
                    : "mr-8 bg-muted"
                )}
              >
                {m.role === "user" ? (
                  <div className="whitespace-pre-wrap">{m.content}</div>
                ) : (
                  <div className="[&>*:last-child]:mb-0">
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                      {m.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            ))}
            {streaming && streamContent && (
              <div className="mr-8 rounded-lg bg-muted px-3 py-2 text-sm">
                <div className="[&>*:last-child]:mb-0">
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                    {streamContent}
                  </ReactMarkdown>
                </div>
                <Loader2 className="mt-1 h-4 w-4 animate-spin text-muted-foreground" />
              </div>
            )}
            <div ref={scrollRef} />
          </div>
        </ScrollArea>

        <div className="border-t border-foreground/10 p-4">
          <div className="flex gap-2">
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.pdf,.doc,.docx"
              onChange={handleUpload}
              className="hidden"
            />
            {companyId && (
              <Button
                variant="outline"
                size="icon"
                onClick={() => fileInputRef.current?.click()}
                disabled={!connected || streaming}
                title="Upload transcript"
                className="shrink-0 border-foreground/20"
              >
                <Upload className="h-4 w-4" />
              </Button>
            )}
            <Input
              placeholder="Ask about transcripts or use cases..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && send(input)}
              disabled={!connected || streaming}
              className="flex-1 border-foreground/20"
            />
            <Button
              size="icon"
              onClick={() => send(input)}
              disabled={!connected || streaming || !input.trim()}
              className="shrink-0"
            >
              {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
            </Button>
          </div>
          {!connected && open && (
            <p className="mt-2 text-xs text-muted-foreground">Connecting...</p>
          )}
        </div>
      </div>
      )}
    </>
  );
}
