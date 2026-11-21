import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone", // prod Docker image uchun
  poweredByHeader: false,
};

export default nextConfig;
