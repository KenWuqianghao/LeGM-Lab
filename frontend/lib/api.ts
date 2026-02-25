import type {
  TakeAnalysis,
  Take,
  TakeDetail,
  BotStatus,
  AnalyzeRequest,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text().catch(() => "Unknown error");
    throw new Error(`API ${res.status}: ${body}`);
  }

  return res.json() as Promise<T>;
}

export function analyzeTake(take: string): Promise<TakeAnalysis> {
  const body: AnalyzeRequest = { take };
  return request<TakeAnalysis>("/api/v1/takes/analyze", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getTake(id: number): Promise<TakeDetail> {
  return request<TakeDetail>(`/api/v1/takes/${id}`);
}

export function getRecentTakes(limit = 50, offset = 0): Promise<Take[]> {
  return request<Take[]>(`/api/v1/takes?limit=${limit}&offset=${offset}`);
}

export function getBotStatus(): Promise<BotStatus> {
  return request<BotStatus>("/api/v1/bot/status");
}

export function startBot(): Promise<{ status: string }> {
  return request<{ status: string }>("/api/v1/bot/start", { method: "POST" });
}

export function stopBot(): Promise<{ status: string }> {
  return request<{ status: string }>("/api/v1/bot/stop", { method: "POST" });
}

export function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/health");
}
