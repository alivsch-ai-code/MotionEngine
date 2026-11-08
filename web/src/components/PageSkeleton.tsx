import { Skeleton } from "./EmptyState";

export function PageSkeleton() {
  return (
    <div className="stack stack--lg" aria-busy="true">
      <Skeleton height={28} width="40%" />
      <div className="grid grid--4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} height={84} />)}</div>
      <Skeleton height={280} />
    </div>
  );
}
