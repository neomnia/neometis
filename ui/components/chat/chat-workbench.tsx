"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";
import { AgentTimeline } from "@/components/chat/agent-timeline";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { AgentEvent } from "@/lib/api";
import { fetchHealth, streamChat } from "@/lib/api";

export function ChatWorkbench() {
  const [message, setMessage] = useState("");
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [useRag, setUseRag] = useState(false);
  const [health, setHealth] = useState<Record<string, string> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  const loadHealth = useCallback(async () => {
    try {
      setHealth(await fetchHealth());
    } catch {
      setHealth(null);
    }
  }, []);

  useEffect(() => {
    loadHealth();
  }, [loadHealth]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events, streaming]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || streaming) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStreaming(true);
    setEvents([]);
    setMessage("");

    try {
      await streamChat(trimmed, {
        useRag,
        signal: controller.signal,
        onEvent: (event) => {
          setEvents((prev) => {
            if (event.type === "token" && prev.length > 0 && prev[prev.length - 1].type === "token") {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: updated[updated.length - 1].content + event.content,
              };
              return updated;
            }
            return [...prev, event];
          });
        },
      });
      await loadHealth();
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        setEvents((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            type: "error",
            content: (err as Error).message,
            metadata: {},
            timestamp: Date.now() / 1000,
          },
        ]);
      }
    } finally {
      setStreaming(false);
    }
  };

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-6xl flex-col gap-4 p-4 md:p-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">NéoMêtis</h1>
          <p className="text-sm text-muted-foreground">Hermes Agent workbench — live reasoning timeline</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {health ? (
            <>
              <Badge variant="secondary">v{health.version}</Badge>
              <Badge variant={health.hermes_engine === "upstream" ? "default" : "outline"}>
                engine: {health.hermes_engine}
              </Badge>
              {health.hermes_vendored_ref ? (
                <Badge variant="outline">hermes@{health.hermes_vendored_ref}</Badge>
              ) : null}
            </>
          ) : (
            <Badge variant="destructive">API offline</Badge>
          )}
        </div>
      </header>

      <div className="grid flex-1 gap-4 lg:grid-cols-[1fr_320px]">
        <Card className="flex min-h-[70vh] flex-col">
          <CardHeader className="border-b border-border/60">
            <CardTitle className="flex items-center gap-2 text-base">
              <Sparkles className="h-4 w-4 text-primary" />
              Agent timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <ScrollArea className="h-[calc(70vh-5rem)] p-4">
              <AgentTimeline events={events} />
              <div ref={bottomRef} />
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={useRag}
                onChange={(e) => setUseRag(e.target.checked)}
                className="rounded border-border"
              />
              Advanced RAG context
            </label>
            <p className="text-xs text-muted-foreground">
              Streams SSE events from <code className="rounded bg-muted px-1">/api/chat/stream</code>: thoughts, tool
              calls, results, and final answer.
            </p>
          </CardContent>
        </Card>
      </div>

      <form onSubmit={handleSubmit} className="sticky bottom-4 flex gap-2 rounded-xl border bg-card/95 p-3 shadow-lg backdrop-blur">
        <Input
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask Hermes anything about your workspace..."
          disabled={streaming}
          className="flex-1"
        />
        <Button type="submit" disabled={streaming || !message.trim()}>
          {streaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          Send
        </Button>
      </form>
    </div>
  );
}
