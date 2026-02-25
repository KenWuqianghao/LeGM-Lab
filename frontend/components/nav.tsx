"use client";

import Image from "next/image";
import Link from "next/link";

export function Nav() {
  return (
    <header className="sticky top-0 z-40 bg-background/70 backdrop-blur-xl border-b border-border/50">
      <nav className="mx-auto flex max-w-[720px] items-center justify-between px-6 py-3.5">
        <Link href="/" className="flex items-center gap-3 group cursor-pointer">
          <Image
            src="/logo.svg"
            alt="LeGM"
            width={36}
            height={36}
            className="rounded-full transition-transform duration-200 group-hover:scale-[0.96] group-active:scale-[0.92]"
          />
          <span className="font-display text-xl font-semibold tracking-tight">
            LeGM
          </span>
        </Link>
        <span className="font-mono text-[11px] tracking-wider text-muted-foreground/40 uppercase">
          Take Analyzer
        </span>
      </nav>
    </header>
  );
}
