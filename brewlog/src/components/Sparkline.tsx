/**
 * Sparkline — bucketed bar chart of recent action counts.
 *
 * Bucket semantics: each entry in `buckets` is a 1-minute window; the value is
 * the count of audit_log rows that fell inside that window. `max` is provided
 * so you can scale (linear vs log vs sqrt — your call). 50 buckets = last hour.
 */

type Action = { action: string; status: string; created_at: string };

type Props = {
  actions: Action[];
  bucketCount?: number;
  bucketMs?: number;
};

export function Sparkline({ actions, bucketCount = 50, bucketMs = 60_000 }: Props) {
  const now = Date.now();
  const buckets = new Array<number>(bucketCount).fill(0);

  for (const a of actions) {
    const t = new Date(a.created_at).getTime();
    const idx = bucketCount - 1 - Math.floor((now - t) / bucketMs);
    if (idx >= 0 && idx < bucketCount) buckets[idx] += 1;
  }
  const max = Math.max(1, ...buckets);

  return (
    <div
      role="img"
      aria-label={`Sparkline: ${actions.length} actions in last ${bucketCount} minutes`}
      className="flex h-6 w-32 items-end gap-px"
    >
      {buckets.map((count, i) => {
        const heightPct = (count / max) * 100;
        // Linear ramp from amber-200 (low) to amber-800 (high) using inline styles
        // so we don't need to enumerate Tailwind classes that JIT can't tree-shake.
        const intensity = count === 0 ? 0 : 0.3 + 0.7 * (count / max);
        return (
          <span
            key={i}
            title={`${count} action${count === 1 ? "" : "s"} in window ${i + 1}/${bucketCount}`}
            className="block w-[2px] rounded-sm bg-amber-700"
            style={{
              height: count === 0 ? "1px" : `${Math.max(2, heightPct)}%`,
              opacity: count === 0 ? 0.15 : intensity,
            }}
          />
        );
      })}
    </div>
  );
}
