import { MediaImport, type MediaJob } from "@/components/control/MediaImport";
import { controlGet, requireStaff } from "@/lib/control-server";

/** Media (ZIP): turlar, mehmonxonalar, joylar, gidlar, agentliklar va yo'nalishlar rasmlarini bir arxivda yuklash. */
export default async function MediaPage() {
  await requireStaff();
  const jobs = await controlGet<MediaJob[]>("/media-import/"); // moderatorga 403 → 404 sahifa
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl">Media (ZIP orqali)</h2>
        <p className="mt-1 text-sm text-ink-soft">
          Rasm va videolarni har bir yozuvga qo&apos;lda qo&apos;shish shart emas: papkalarni yozuv nomi yoki slug&apos;i bilan nomlang,
          bitta ZIP qilib yuklang — fayllar o&apos;zi biriktiriladi.
        </p>
      </div>

      <div className="card space-y-3 p-5 text-sm">
        <h3 className="font-semibold">Arxiv tuzilishi</h3>
        <pre className="overflow-x-auto rounded-xl bg-sand-100 p-4 text-xs leading-6">{`turlar/samarqand-bir-kunda-afrosiyob-poyezdida/1.jpg, 2.jpg, video.mp4
mehmonxonalar/Registan Royal Palace/1.jpg, 2.jpg      ← nomi bilan ham bo'ladi
joylar/gori-amir-maqbarasi/muqova.jpg, ichki.jpg, audio.mp3
gidlar/jasur-toshmatov.jpg
agentliklar/zarafshan-travel.png
yonalishlar/termiz.jpg`}</pre>
        <ul className="list-disc space-y-1 pl-5 text-ink-soft">
          <li>Tur va mehmonxona: rasm (jpg, png, webp — 6 MB gacha) va video (mp4, mov, webm — 20 MB gacha); 20 rasm, 4 video.</li>
          <li>Birinchi rasm muqova bo&apos;ladi (agar muqova hali yo&apos;q bo&apos;lsa). Tartib — fayl nomi bo&apos;yicha: 1.jpg, 2.jpg…</li>
          <li>Gid surati, agentlik logotipi, yo&apos;nalish muqovasi — bitta rasm, yangisi eskisini almashtiradi.</li>
          <li>Joy: birinchi rasm muqova, qolganlari galereya, .mp3/.m4a/.ogg — audio-gid.</li>
          <li>Arxivni qayta yuklash xavfsiz: bir xil fayl ikkinchi marta qo&apos;shilmaydi. Arxiv — 100 MB gacha, kattasini bo&apos;ling.</li>
        </ul>
      </div>

      <MediaImport initial={jobs} />
    </div>
  );
}
