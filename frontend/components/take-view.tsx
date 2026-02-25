"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { VerdictBadge } from "@/components/verdict-badge";
import type { Verdict } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface TakeData {
  id: number;
  take_text: string;
  verdict: string;
  confidence: number;
  roast: string;
  reasoning: string;
  stats_used: string[];
  chart_url: string | null;
  created_at: string;
}

function XIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function buildShareUrl(take: TakeData, pageUrl: string): string {
  const verdict = take.verdict.toUpperCase();
  const confidence = Math.round(take.confidence * 100);

  const header = `"${take.take_text}" - ${verdict} (${confidence}%)`;
  const tag = `Fact-checked by @LeGMLab`;
  const text = [header, ``, take.roast, ``, tag].join("\n");

  const params = new URLSearchParams({ text, url: pageUrl });
  return `https://x.com/intent/post?${params.toString()}`;
}

export function TakeView({ take }: { take: TakeData }) {
  const pageUrl =
    typeof window !== "undefined"
      ? window.location.href
      : `${API_BASE}/take/${take.id}`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 200, damping: 25 }}
      className="space-y-6"
    >
      <div>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs text-muted-foreground/50 cursor-pointer transition-colors duration-200 hover:text-fire mb-6"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Analyze your own take
        </Link>
      </div>

      <div className="rounded-2xl bg-card border border-border px-5 py-4">
        <p className="text-[15px] leading-relaxed font-medium text-foreground/80">
          &ldquo;{take.take_text}&rdquo;
        </p>
      </div>

      <div className="space-y-4 ml-4 pl-5 border-l-2 border-fire/20">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <VerdictBadge
            verdict={take.verdict as Verdict}
            confidence={take.confidence}
            size="lg"
          />
          {take.stats_used.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {take.stats_used.map((stat) => (
                <span
                  key={stat}
                  className="rounded-md bg-amber/8 border border-amber/10 px-2 py-0.5 font-mono text-[11px] text-amber/60"
                >
                  {stat}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-2xl bg-card border border-border px-5 py-4">
          <p className="mb-1 font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-fire/50">
            Roast
          </p>
          <p className="text-[15px] font-medium leading-relaxed tracking-[-0.01em]">
            {take.roast}
          </p>
        </div>

        <div className="space-y-1.5 px-1">
          <div className="flex items-center gap-2">
            <div className="h-px flex-1 bg-amber/8" />
            <p className="font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-amber/40 shrink-0">
              Reasoning
            </p>
            <div className="h-px flex-1 bg-amber/8" />
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground/70">
            {take.reasoning}
          </p>
        </div>

        {take.chart_url && (
          <div className="overflow-hidden rounded-2xl border border-border">
            <img
              src={
                take.chart_url.startsWith("http")
                  ? take.chart_url
                  : `${API_BASE}${take.chart_url}`
              }
              alt="Statistical comparison chart"
              className="w-full"
            />
          </div>
        )}

        <div className="pt-1 flex items-center gap-3">
          <a
            href={buildShareUrl(take, pageUrl)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-secondary border border-border px-4 py-2 text-[13px] font-medium text-muted-foreground cursor-pointer transition-all duration-200 hover:text-foreground hover:border-fire/20 hover:bg-fire/5 active:scale-[0.97]"
          >
            <XIcon />
            Share to X
          </a>
        </div>
      </div>
    </motion.div>
  );
}
