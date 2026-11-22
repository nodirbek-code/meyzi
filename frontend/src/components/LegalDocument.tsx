/**
 * Yuridik hujjat (foydalanish shartlari, maxfiylik siyosati) — oddiy belgilashdan chiroyli ko'rinishga:
 *   birinchi qator          — hujjat nomi
 *   "## 1. Sarlavha"         — bo'lim
 *   "1.1. Matn"              — band (raqami alohida ustunda)
 *   "- matn"                 — ro'yxat
 *   boshqa qatorlar          — xatboshi
 * Belgilashsiz eski matn ham buzilmaydi — oddiy xatboshilar bo'lib chiqadi.
 */

type Block =
  | { kind: "title"; text: string }
  | { kind: "section"; text: string; id: string }
  | { kind: "clause"; num: string; text: string }
  | { kind: "list"; items: string[] }
  | { kind: "para"; text: string };

const CLAUSE = /^(\d+(?:\.\d+)+\.)\s+(.*)$/;

export function parseLegal(body: string): Block[] {
  const lines = body.replace(/\r/g, "").split("\n");
  const blocks: Block[] = [];
  let section = 0;
  let first = true;
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) continue;
    if (line.startsWith("## ")) {
      section += 1;
      blocks.push({ kind: "section", text: line.slice(3).trim(), id: `bolim-${section}` });
    } else if (line.startsWith("- ")) {
      const last = blocks[blocks.length - 1];
      if (last?.kind === "list") last.items.push(line.slice(2).trim());
      else blocks.push({ kind: "list", items: [line.slice(2).trim()] });
    } else {
      const m = line.match(CLAUSE);
      if (m) blocks.push({ kind: "clause", num: m[1], text: m[2] });
      else if (first && !body.trimStart().startsWith("##") && lines.length > 1) blocks.push({ kind: "title", text: line });
      else blocks.push({ kind: "para", text: line });
    }
    first = false;
  }
  return blocks;
}

export function LegalDocument({ body }: { body: string }) {
  const blocks = parseLegal(body);
  const sections = blocks.filter((b): b is Extract<Block, { kind: "section" }> => b.kind === "section");

  return (
    <div className="grid gap-8 lg:grid-cols-[15rem_1fr]">
      {sections.length > 2 && (
        <aside className="lg:sticky lg:top-24 lg:self-start">
          <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-ink-mute">Mundarija</p>
          <ol className="grid gap-1 text-sm sm:grid-cols-2 lg:grid-cols-1">
            {sections.map((s) => (
              <li key={s.id}>
                <a href={`#${s.id}`} className="block rounded-lg px-2 py-1 text-ink-soft transition hover:bg-sand-100 hover:text-forest-700">
                  {s.text}
                </a>
              </li>
            ))}
          </ol>
        </aside>
      )}

      <article className="card min-w-0 p-6 sm:p-10">
        {blocks.map((b, i) => {
          switch (b.kind) {
            case "title":
              return (
                <p key={i} className="mb-5 border-b border-sand-200 pb-5 text-center font-display text-lg font-bold uppercase tracking-wide text-ink">
                  {b.text}
                </p>
              );
            case "section":
              return (
                <h2 key={i} id={b.id} className="mb-3 mt-9 scroll-mt-24 border-b border-sand-200 pb-2 text-lg font-bold text-ink first:mt-0 sm:text-xl">
                  {b.text}
                </h2>
              );
            case "clause":
              return (
                <p key={i} className="mb-2.5 flex gap-3 text-[15px] leading-relaxed text-ink-soft">
                  <span className="w-11 shrink-0 font-semibold tabular-nums text-forest-700">{b.num}</span>
                  <span className="min-w-0">{b.text}</span>
                </p>
              );
            case "list":
              return (
                <ul key={i} className="mb-3 ml-14 list-disc space-y-1.5 text-[15px] leading-relaxed text-ink-soft marker:text-forest-500">
                  {b.items.map((item, j) => (
                    <li key={j}>{item}</li>
                  ))}
                </ul>
              );
            default:
              return (
                <p key={i} className="mb-4 text-[15px] leading-relaxed text-ink-soft">
                  {b.text}
                </p>
              );
          }
        })}
      </article>
    </div>
  );
}
