import Link from "next/link";

export default function NotFound() {
  return (
    <div className="container-lz flex flex-col items-center py-20 text-center sm:py-28">
      <div className="nature-bg flex h-40 w-full max-w-md items-center justify-center rounded-[1.5rem]">
        <span className="font-display text-7xl font-extrabold text-white/90">404</span>
      </div>
      <h1 className="mt-8 text-3xl">Sahifa topilmadi</h1>
      <p className="mt-2 max-w-md text-ink-soft">Bu so&apos;qmoq hech qayerga olib bormaydi — lekin oldinda hali ko&apos;p yo&apos;llar bor.</p>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        <Link href="/" className="btn-primary">
          Bosh sahifa
        </Link>
        <Link href="/tours" className="btn-ghost">
          Turlarni ko&apos;rish
        </Link>
      </div>
    </div>
  );
}
