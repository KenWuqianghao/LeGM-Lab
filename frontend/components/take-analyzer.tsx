"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { analyzeTake } from "@/lib/api";
import { VerdictBadge } from "@/components/verdict-badge";
import { AnalysisSkeleton } from "@/components/analysis-skeleton";
import type { TakeAnalysis } from "@/lib/types";

interface HistoryEntry {
  take: string;
  result: TakeAnalysis;
}

const placeholders = [
  "Jokic is the best center of all time",
  "Steph Curry is the greatest shooter ever",
  "LeBron would average 40 in the 90s",
  "Luka is better than Bird already",
  "Wemby will be the GOAT by 2030",
  "KD has no rings that count",
];

function getRandomPlaceholder(): string {
  return placeholders[Math.floor(Math.random() * placeholders.length)];
}

function StatLine({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5 px-1">
      <div className="flex items-center gap-2">
        <div className="h-px flex-1 bg-amber/8" />
        <p className="font-mono text-[10px] font-medium uppercase tracking-[0.15em] text-amber/40 shrink-0">
          {label}
        </p>
        <div className="h-px flex-1 bg-amber/8" />
      </div>
      {children}
    </div>
  );
}

function XIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function buildShareUrl(entry: HistoryEntry): string {
  const verdict = entry.result.verdict.toUpperCase();
  const confidence = Math.round(entry.result.confidence * 100);

  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const takeUrl = `${origin}/take/${entry.result.take_id}`;

  const header = `"${entry.take}" - ${verdict} (${confidence}%)`;
  const tag = `Fact-checked by @LeGMLab`;
  const text = [header, ``, entry.result.roast, ``, tag].join("\n");

  const params = new URLSearchParams({ text, url: takeUrl });
  return `https://x.com/intent/post?${params.toString()}`;
}

function AnalysisResult({ entry }: { entry: HistoryEntry }) {
  return (
    <div className="space-y-4">
      <div className="rounded-2xl bg-card border border-border px-5 py-4">
        <p className="text-[15px] leading-relaxed font-medium text-foreground/80">
          &ldquo;{entry.take}&rdquo;
        </p>
      </div>

      <div className="space-y-4 ml-4 pl-5 border-l-2 border-fire/20">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <VerdictBadge
            verdict={entry.result.verdict}
            confidence={entry.result.confidence}
            size="lg"
          />
          {entry.result.stats_used.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {entry.result.stats_used.map((stat) => (
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
            {entry.result.roast}
          </p>
        </div>

        <StatLine label="Reasoning">
          <p className="text-sm leading-relaxed text-muted-foreground/70">
            {entry.result.reasoning}
          </p>
        </StatLine>

        {entry.result.chart_url && (
          <div className="overflow-hidden rounded-2xl border border-border">
            <img
              src={
                entry.result.chart_url.startsWith("http")
                  ? entry.result.chart_url
                  : `${
                      process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
                    }${entry.result.chart_url}`
              }
              alt="Statistical comparison chart"
              className="w-full"
            />
          </div>
        )}

        <div className="pt-1">
          <a
            href={buildShareUrl(entry)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-secondary border border-border px-4 py-2 text-[13px] font-medium text-muted-foreground cursor-pointer transition-all duration-200 hover:text-foreground hover:border-fire/20 hover:bg-fire/5 active:scale-[0.97]"
          >
            <XIcon />
            Share to X
          </a>
        </div>
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="relative mb-8">
        {/* Basketball SVG */}
        <svg
          width="80"
          height="80"
          viewBox="0 0 80 80"
          fill="none"
          className="text-fire/20"
        >
          <circle
            cx="40"
            cy="40"
            r="38"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            d="M40 2c-12 14-18 24-18 38s6 24 18 38"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <path
            d="M40 2c12 14 18 24 18 38s-6 24-18 38"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <line
            x1="2"
            y1="40"
            x2="78"
            y2="40"
            stroke="currentColor"
            strokeWidth="1.5"
          />
        </svg>
        {/* Subtle pulse behind the ball */}
        <div className="absolute inset-0 rounded-full bg-fire/5 animate-pulse-warm" />
      </div>
      <p className="font-display text-xl font-semibold text-foreground/50 mb-2">
        The court is empty
      </p>
      <p className="text-sm text-muted-foreground/50 max-w-[300px] leading-relaxed">
        Drop an NBA take below and watch it get fact-checked with real stats. No
        opinion is safe.
      </p>
      <div className="mt-6 flex items-center gap-3 text-[11px] font-mono text-muted-foreground/30 uppercase tracking-wider">
        <span className="size-1.5 rounded-full bg-valid/40" />
        Valid
        <span className="size-1.5 rounded-full bg-mid/40" />
        Mid
        <span className="size-1.5 rounded-full bg-trash/40" />
        Trash
      </div>

      <div className="mt-8 pt-6 border-t border-border/50">
        <p className="text-xs text-muted-foreground/40 leading-relaxed">
          You can also mention{" "}
          <a
            href="https://x.com/LeGMLab"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-fire/60 cursor-pointer transition-colors duration-200 hover:text-fire"
          >
            <XIcon />
            @LeGMLab
          </a>{" "}
          on X with any NBA take and get roasted directly in your replies.
        </p>
      </div>
    </div>
  );
}

export function TakeAnalyzer() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentTake, setCurrentTake] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [placeholder] = useState(getRandomPlaceholder);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (history.length > 0 || loading) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [history.length, loading]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const text = input.trim();
      if (!text || loading) return;

      setInput("");
      setCurrentTake(text);
      setLoading(true);
      setError(null);

      try {
        const analysis = await analyzeTake(text);
        setHistory((prev) => [...prev, { take: text, result: analysis }]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Analysis failed");
      } finally {
        setLoading(false);
        setCurrentTake(null);
      }
    },
    [input, loading],
  );

  const isEmpty = history.length === 0 && !loading && !error;

  return (
    <div className="flex flex-col gap-6 pb-32">
      {isEmpty && <EmptyState />}

      <AnimatePresence initial={false}>
        {history.map((entry, i) => (
          <motion.div
            key={`${entry.result.take_id}-${i}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              type: "spring",
              stiffness: 200,
              damping: 25,
              delay: 0.05,
            }}
          >
            <AnalysisResult entry={entry} />
          </motion.div>
        ))}
      </AnimatePresence>

      <AnimatePresence mode="wait">
        {loading && currentTake && (
          <motion.div
            key="loading"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="space-y-4"
          >
            <div className="rounded-2xl bg-card border border-border px-5 py-4">
              <p className="text-[15px] leading-relaxed font-medium text-foreground/80">
                &ldquo;{currentTake}&rdquo;
              </p>
            </div>
            <div className="ml-4 pl-5 border-l-2 border-fire/20">
              <AnalysisSkeleton />
            </div>
          </motion.div>
        )}

        {error && !loading && (
          <motion.div
            key="error"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="rounded-2xl bg-trash/5 border border-trash/15 px-5 py-4"
          >
            <p className="text-sm text-trash">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      <div ref={bottomRef} />

      {/* Input — fixed to bottom, no gradient overlay */}
      <div className="fixed bottom-0 left-0 right-0 z-30">
        <div className="mx-auto max-w-[720px] px-6 pb-5 pt-3">
          <form onSubmit={handleSubmit}>
            <div className="rounded-2xl bg-card/90 backdrop-blur-xl border border-border shadow-[0_-8px_32px_rgba(0,0,0,0.3)] transition-all duration-200 focus-within:border-fire/25 focus-within:shadow-[0_-8px_32px_rgba(0,0,0,0.3),0_0_0_3px_rgba(232,97,45,0.06)]">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={placeholder}
                rows={2}
                className="w-full resize-none bg-transparent px-5 pt-4 pb-12 text-[15px] leading-relaxed text-foreground placeholder:text-muted-foreground/30 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                    handleSubmit(e);
                  }
                }}
              />
              <div className="absolute bottom-3 right-3 flex items-center gap-2.5">
                <kbd className="hidden sm:inline-block rounded-md bg-secondary border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground/30">
                  {typeof navigator !== "undefined" &&
                  navigator.platform?.includes("Mac")
                    ? "Cmd"
                    : "Ctrl"}
                  +Enter
                </kbd>
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="flex size-9 items-center justify-center rounded-xl bg-fire text-white cursor-pointer transition-all duration-200 hover:bg-fire/90 hover:shadow-[0_0_20px_rgba(232,97,45,0.25)] active:scale-[0.96] active:-translate-y-px disabled:opacity-20 disabled:cursor-not-allowed disabled:hover:shadow-none"
                >
                  {loading ? (
                    <svg
                      className="animate-spin size-[18px]"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <circle
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeDasharray="31.4 31.4"
                      />
                    </svg>
                  ) : (
                    <svg
                      width="18"
                      height="18"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                    >
                      <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                    </svg>
                  )}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
