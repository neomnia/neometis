export type AgentEventType =
  | "thought"
  | "tool_call"
  | "tool_result"
  | "token"
  | "final_answer"
  | "error";

export interface AgentEvent {
  id: string;
  type: AgentEventType;
  content: string;
  metadata: Record<string, unknown>;
  timestamp: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function streamChat(
  message: string,
  options: { useRag?: boolean; onEvent: (event: AgentEvent) => void; signal?: AbortSignal }
): Promise<void> {
  const response = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, use_rag: options.useRag ?? false }),
    signal: options.signal,
  });

  if (!response.ok || !response.body) {
    throw new Error(`Stream failed (${response.status})`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const dataLine = chunk.split("\n").find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      try {
        const payload = JSON.parse(dataLine.slice(6)) as AgentEvent;
        options.onEvent(payload);
      } catch {
        // ignore malformed frames
      }
    }
  }
}

export async function fetchHealth(): Promise<Record<string, string>> {
  const res = await fetch(`${API_URL}/health`, { cache: "no-store" });
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}
