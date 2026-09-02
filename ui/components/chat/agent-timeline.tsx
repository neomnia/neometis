"use client";

import { Brain, Hammer, MessageSquare, Sparkles, Wrench, AlertCircle } from "lucide-react";
import type { AgentEvent } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const ICONS = {
  thought: Brain,
  tool_call: Wrench,
  tool_result: Hammer,
  token: Sparkles,
  final_answer: MessageSquare,
  error: AlertCircle,
} as const;

const LABELS = {
  thought: "Thinking",
  tool_call: "Tool call",
  tool_result: "Tool result",
  token: "Token",
  final_answer: "Answer",
  error: "Error",
} as const;

const COLORS = {
  thought: "border-violet-500/30 bg-violet-500/10",
  tool_call: "border-amber-500/30 bg-amber-500/10",
  tool_result: "border-emerald-500/30 bg-emerald-500/10",
  token: "border-sky-500/30 bg-sky-500/10",
  final_answer: "border-primary/40 bg-primary/10",
  error: "border-destructive/40 bg-destructive/10",
} as const;

function formatTime(ts: number) {
  return new Date(ts * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export function AgentTimeline({ events }: { events: AgentEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Send a message to watch Hermes think, call tools, and respond in real time.
      </div>
    );
  }

  return (
    <ol className="relative space-y-4 border-l border-border/60 pl-6">
      {events.map((event, index) => {
        const Icon = ICONS[event.type];
        const isStreamingToken = event.type === "token";

        return (
          <li key={`${event.id}-${index}`} className="relative">
            <span
              className={cn(
                "absolute -left-[1.85rem] flex h-7 w-7 items-center justify-center rounded-full border bg-background",
                COLORS[event.type]
              )}
            >
              <Icon className="h-3.5 w-3.5" />
            </span>

            <div className={cn("rounded-lg border p-3", COLORS[event.type])}>
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <Badge variant="outline">{LABELS[event.type]}</Badge>
                <span className="text-xs text-muted-foreground">{formatTime(event.timestamp)}</span>
              </div>

              {event.type === "tool_call" && event.metadata.arguments ? (
                <pre className="mb-2 overflow-x-auto rounded-md bg-background/60 p-2 text-xs">
                  {JSON.stringify(event.metadata.arguments, null, 2)}
                </pre>
              ) : null}

              <p className={cn("whitespace-pre-wrap text-sm leading-relaxed", isStreamingToken && "font-mono")}>{event.content}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
