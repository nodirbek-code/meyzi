import type { NextConfig } from "next";

const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone", // prod Docker image uchun
  poweredByHeader: false,
  // Admin panel backend'da (Django admin) — saytdagi /admin unga yo'naltiriladi
  async redirects() {
    return [
      { source: "/admin", destination: `${API}/admin/`, permanent: false },
      { source: "/admin/:path*", destination: `${API}/admin/:path*`, permanent: false },
    ];
  },
};

export default nextConfig;
