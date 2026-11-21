import Link from "next/link";

export function Pagination({
  page,
  count,
  pageSize,
  basePath,
  params,
}: {
  page: number;
  count: number;
  pageSize: number;
  basePath: string;
  params: Record<string, string>;
}) {
  const pages = Math.ceil(count / pageSize);
  if (pages <= 1) return null;
  const href = (p: number) => {
    const q = new URLSearchParams({ ...params, page: String(p) });
    return `${basePath}?${q}`;
  };
  const nums = Array.from({ length: pages }, (_, i) => i + 1).filter((p) => p === 1 || p === pages || Math.abs(p - page) <= 1);
  const box = "flex h-10 min-w-10 items-center justify-center rounded-xl px-3 text-sm font-semibold transition";
  return (
    <nav className="mt-10 flex items-center justify-center gap-1.5" aria-label="Sahifalar">
      {page > 1 ? (
        <Link href={href(page - 1)} className={`${box} border border-sand-300 bg-white hover:border-forest-400`} aria-label="Oldingi">
          ←
        </Link>
      ) : (
        <span className={`${box} border border-sand-200 text-ink-mute`}>←</span>
      )}
      {nums.map((p, i) => (
        <span key={p} className="flex items-center gap-1.5">
          {i > 0 && p - nums[i - 1] > 1 && <span className="px-1 text-ink-mute">…</span>}
          <Link
            href={href(p)}
            aria-current={p === page ? "page" : undefined}
            className={`${box} ${p === page ? "bg-forest-600 text-white" : "border border-sand-300 bg-white hover:border-forest-400"}`}
          >
            {p}
          </Link>
        </span>
      ))}
      {page < pages ? (
        <Link href={href(page + 1)} className={`${box} border border-sand-300 bg-white hover:border-forest-400`} aria-label="Keyingi">
          →
        </Link>
      ) : (
        <span className={`${box} border border-sand-200 text-ink-mute`}>→</span>
      )}
    </nav>
  );
}
