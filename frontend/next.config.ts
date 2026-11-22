import type { NextConfig } from "next";

const API = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");

const nextConfig: NextConfig = {
  output: "standalone", // prod Docker image uchun
  poweredByHeader: false,
  // /control — saytdagi admin paneli; /control/admin — Django admin (backend). Oddiy /admin manzili yo'q.
  async redirects() {
    return [
      // Hamkorlik arizalari bitta sahifada: /hamkorlik?turi=agentlik|gid|mehmonxona
      { source: "/agencies", destination: "/hamkorlik?turi=agentlik", permanent: true },
      { source: "/guides/become", destination: "/hamkorlik?turi=gid", permanent: true },
      { source: "/hotels/join", destination: "/hamkorlik?turi=mehmonxona", permanent: true },
      { source: "/control/admin", destination: `${API}/control/admin/`, permanent: false },
      { source: "/control/admin/:path*", destination: `${API}/control/admin/:path*`, permanent: false },
    ];
  },
};

export default nextConfig;
