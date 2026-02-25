"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { Verdict } from "@/lib/types";

const verdictConfig: Record<
  Verdict,
  { label: string; color: string; bg: string; border: string }
> = {
  trash: {
    label: "TRASH",
    color: "text-trash",
    bg: "bg-trash/10",
    border: "border-trash/20",
  },
  valid: {
    label: "VALID",
    color: "text-valid",
    bg: "bg-valid/10",
    border: "border-valid/20",
  },
  mid: {
    label: "MID",
    color: "text-mid",
    bg: "bg-mid/10",
    border: "border-mid/20",
  },
};

interface VerdictBadgeProps {
  verdict: Verdict;
  confidence: number;
  size?: "sm" | "lg";
}

export function VerdictBadge({
  verdict,
  confidence,
  size = "sm",
}: VerdictBadgeProps) {
  const config = verdictConfig[verdict];
  const pct = Math.round(confidence * 100);

  return (
    <motion.span
      initial={{ scale: 0.85, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={cn(
        "inline-flex items-center gap-2 rounded-full border font-display font-bold tracking-widest",
        config.bg,
        config.color,
        config.border,
        size === "lg" ? "px-5 py-2 text-sm" : "px-3 py-1 text-xs",
      )}
    >
      {config.label}
      <span className="font-mono opacity-50 font-normal text-[0.85em]">
        {pct}%
      </span>
    </motion.span>
  );
}
