export type Verdict = "trash" | "valid" | "mid";

export interface TakeAnalysis {
  verdict: Verdict;
  confidence: number;
  roast: string;
  reasoning: string;
  stats_used: string[];
  take_id: number;
  chart_url?: string;
}

export interface Take {
  id: number;
  take_text: string;
  verdict: Verdict;
  confidence: number;
  roast: string;
  reasoning: string;
  stats_used: string[];
  created_at: string;
}

export interface TakeDetail {
  id: number;
  take_text: string;
  verdict: Verdict;
  confidence: number;
  roast: string;
  reasoning: string;
  stats_used: string[];
  chart_url: string | null;
  created_at: string;
}

export interface BotStatus {
  running: boolean;
  tweets_this_month: number;
  monthly_budget: number;
  dry_run: boolean;
  proactive_enabled: boolean;
}

export interface AnalyzeRequest {
  take: string;
}
