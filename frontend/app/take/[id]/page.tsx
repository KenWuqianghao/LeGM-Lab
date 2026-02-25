import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { TakeView } from "@/components/take-view";

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

async function fetchTake(id: string): Promise<TakeData | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/takes/${id}`, {
      next: { revalidate: 60 },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  const { id } = await params;
  const take = await fetchTake(id);

  if (!take) {
    return { title: "Take not found - LeGM" };
  }

  const verdict = take.verdict.toUpperCase();
  const confidence = Math.round(take.confidence * 100);
  const title = `${verdict} (${confidence}%) - LeGM`;
  const description = `"${take.take_text}" — ${take.roast}`;

  const metadata: Metadata = {
    title,
    description,
    openGraph: {
      title,
      description,
      siteName: "LeGM - NBA Take Analyzer",
      type: "article",
    },
    twitter: {
      card: take.chart_url ? "summary_large_image" : "summary",
      title,
      description,
      site: "@LeGMLab",
    },
  };

  if (take.chart_url) {
    const imageUrl = take.chart_url.startsWith("http")
      ? take.chart_url
      : `${API_BASE}${take.chart_url}`;

    metadata.openGraph!.images = [{ url: imageUrl, width: 1200, height: 675 }];
    metadata.twitter!.images = [imageUrl];
  }

  return metadata;
}

export default async function TakePage({ params }: PageProps) {
  const { id } = await params;
  const take = await fetchTake(id);

  if (!take) {
    notFound();
  }

  return (
    <div className="mx-auto max-w-[720px] px-6 py-10">
      <TakeView take={take} />
    </div>
  );
}
