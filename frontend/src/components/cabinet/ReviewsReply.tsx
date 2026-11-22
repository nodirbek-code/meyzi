"use client";

import { useState } from "react";

import { api } from "@/lib/client";
import { dateLong } from "@/lib/format";
import type { Paginated } from "@/lib/types";

import { ErrorText, Loading } from "./Bits";
import { useAction, useData } from "./useData";

type Row = { id: number; author: string; rating: number; text: string; tour_title?: string; created_at: string } & Record<string, unknown>;

/** Sharhlar va javob (agentlik: replyField="agency_reply", mehmonxona: "hotel_reply") */
export function ReviewsReply({ listPath, replyPath, replyField }: { listPath: string; replyPath: (id: number) => string; replyField: string }) {
  const { data, error, loading, reload } = useData<Paginated<Row>>(listPath);
  const act = useAction();
  const [drafts, setDrafts] = useState<Record<number, string>>({});

  return (
    <div className="space-y-4">
      <ErrorText text={error || act.error} />
      {loading && <Loading />}
      {data && !data.results.length && <p className="card p-8 text-center text-sm text-ink-soft">Hali sharhlar yo&apos;q.</p>}
      {data?.results.map((r) => {
        const reply = (r[replyField] as string) || "";
        return (
          <div key={r.id} className="card space-y-3 p-5">
            <div className="flex flex-wrap justify-between gap-2 text-sm">
              <span><b>{r.author}</b>{r.tour_title && <span className="text-ink-mute"> · {r.tour_title}</span>}</span>
              <span><span className="text-sun-500">{"★".repeat(r.rating)}</span> <span className="text-xs text-ink-mute">{dateLong(r.created_at, true)}</span></span>
            </div>
            {r.text && <p className="text-sm text-ink-soft">{r.text}</p>}
            <div className="flex gap-2">
              <input className="input" placeholder="Javobingiz…" value={drafts[r.id] ?? reply} onChange={(e) => setDrafts({ ...drafts, [r.id]: e.target.value })} />
              <button className="btn-primary shrink-0" disabled={act.busy} onClick={() => act.run(async () => { await api.post(replyPath(r.id), { text: drafts[r.id] ?? reply }); reload(); })}>
                {reply ? "Yangilash" : "Javob berish"}
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Agentlik turlari sharhlari */
export function AgencyReviews() {
  return <ReviewsReply listPath="/cabinet/reviews?page_size=100" replyPath={(id) => `/cabinet/reviews/${id}/reply`} replyField="agency_reply" />;
}

/** Gid sharhlari */
export function GuideReviews() {
  return <ReviewsReply listPath="/cabinet/guide/reviews?page_size=100" replyPath={(id) => `/cabinet/guide/reviews/${id}/reply`} replyField="guide_reply" />;
}
