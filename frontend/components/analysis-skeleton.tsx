import { Skeleton } from "@/components/ui/skeleton";

export function AnalysisSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Skeleton className="h-8 w-32 rounded-full bg-fire/5" />
        <div className="flex gap-1.5">
          <Skeleton className="h-5 w-14 rounded-md bg-amber/5" />
          <Skeleton className="h-5 w-16 rounded-md bg-amber/5" />
        </div>
      </div>
      <div className="rounded-2xl bg-card border border-border px-5 py-4 space-y-3">
        <Skeleton className="h-3 w-12 bg-fire/5" />
        <Skeleton className="h-5 w-full bg-amber/5" />
        <Skeleton className="h-5 w-3/4 bg-amber/5" />
      </div>
      <div className="space-y-2 px-1">
        <Skeleton className="h-3 w-20 bg-amber/5" />
        <Skeleton className="h-4 w-full bg-amber/5" />
        <Skeleton className="h-4 w-5/6 bg-amber/5" />
        <Skeleton className="h-4 w-2/3 bg-amber/5" />
      </div>
    </div>
  );
}
