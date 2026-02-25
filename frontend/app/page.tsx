import { TakeAnalyzer } from "@/components/take-analyzer";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-[720px] px-6 py-10">
      <div className="mb-8">
        <h1 className="font-display text-4xl font-bold tracking-tight leading-none md:text-5xl">
          Drop your hottest
          <br />
          <span className="text-fire">NBA take.</span>
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-muted-foreground/60 max-w-[42ch]">
          Get fact-checked with real stats and roasted by an AI that watches
          more basketball than you do.
        </p>
      </div>
      <TakeAnalyzer />
    </div>
  );
}
