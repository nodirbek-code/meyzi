import Link from "next/link";
import type { ReactNode } from "react";

export function Stars({ rating, count }: { rating: string | number; count?: number }) {
  const r = Number(rating) || 0;
  if (!count) return null;
  return (
    <span className="inline-flex items-center gap-1 text-xs text-ink-soft">
      <span className="text-sun-500">★</span>
      <b className="text-ink">{r.toFixed(1)}</b>
      <span>({count})</span>
    </span>
  );
}

const TONES = {
  gold: "bg-sun-100 text-sun-700",
  green: "bg-forest-50 text-forest-700",
  gray: "bg-sand-200 text-ink-soft",
  red: "bg-clay-50 text-clay-700",
  blue: "bg-sky-50 text-sky-700",
  turquoise: "bg-sky-100 text-sky-700",
} as const;

export function Badge({ tone = "green", children }: { tone?: keyof typeof TONES; children: ReactNode }) {
  return <span className={`chip ${TONES[tone]}`}>{children}</span>;
}

export function SectionTitle({
  eyebrow,
  title,
  text,
  action,
  center = false,
}: {
  eyebrow?: string;
  title: string;
  text?: string;
  action?: ReactNode;
  center?: boolean;
}) {
  return (
    <div className={`mb-8 flex flex-wrap items-end gap-3 ${center ? "flex-col items-center text-center" : "justify-between"}`}>
      <div className={center ? "max-w-2xl" : ""}>
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h2 className="text-2xl sm:text-3xl">{title}</h2>
        {text && <p className="mt-2 text-ink-soft">{text}</p>}
      </div>
      {action}
    </div>
  );
}

export function MoreLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="inline-flex items-center gap-1 text-sm font-semibold text-forest-600 hover:text-forest-800">
      {children}
      <span aria-hidden>›</span>
    </Link>
  );
}

export function EmptyState({ title, text, action }: { title: string; text?: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
      <div className="nature-bg h-14 w-14 rounded-full" aria-hidden />
      <h3 className="text-lg">{title}</h3>
      {text && <p className="max-w-md text-sm text-ink-soft">{text}</p>}
      {action}
    </div>
  );
}

/** Rasm bo'lmasa — tog' silueti tushirilgan tabiat foni */
export function Cover({ src, alt, className = "" }: { src: string | null | undefined; alt: string; className?: string }) {
  if (!src) {
    let h = 0;
    for (const ch of alt) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
    return <div className={`nature-bg nature-${h % 4} ${className}`} role="img" aria-label={alt} />;
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img src={src} alt={alt} className={`object-cover ${className}`} loading="lazy" />;
}

export function Icon({ name, size = 16, className = "" }: { name: keyof typeof ICONS; size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      {ICONS[name]}
    </svg>
  );
}

const ICONS = {
  pin: (
    <>
      <path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21Z" />
      <circle cx="12" cy="9.5" r="2.5" />
    </>
  ),
  calendar: (
    <>
      <rect x="3.5" y="5" width="17" height="15" rx="2.5" />
      <path d="M3.5 10h17M8 3v4M16 3v4" />
    </>
  ),
  clock: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </>
  ),
  shield: <path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.4 7.5 9.5 4.3-1.1 7.5-4.9 7.5-9.5V6L12 3Zm-3 9 2 2 4-4" />,
  leaf: <path d="M5 19c0-8 5-13 15-14-1 10-6 15-14 15M5 19l7-7" />,
  lock: (
    <>
      <rect x="5" y="10.5" width="14" height="10" rx="2.5" />
      <path d="M8 10.5V8a4 4 0 0 1 8 0v2.5" />
    </>
  ),
  users: (
    <>
      <circle cx="9" cy="8" r="3.5" />
      <path d="M2.5 20c.6-3.6 3.2-5.5 6.5-5.5s5.9 1.9 6.5 5.5M16 4.8a3.5 3.5 0 0 1 0 6.4M18 14.8c2 .7 3.2 2.4 3.5 5.2" />
    </>
  ),
  heart: <path d="M12 20s-7.5-4.4-7.5-10A4.3 4.3 0 0 1 12 7.4 4.3 4.3 0 0 1 19.5 10c0 5.6-7.5 10-7.5 10Z" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  check: <path d="m5 12.5 4.5 4.5L19 7.5" />,
  star: <path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.3-4.1 5.9-.9L12 3.5Z" />,
  telegram: <path d="M21 4 3 11l6 2 2 6 3-4 5 4 2-15ZM9 13l9-6-7 8" />,
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2.5" />
      <path d="m4 7 8 6 8-6" />
    </>
  ),
  phone: <path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z" />,
};
