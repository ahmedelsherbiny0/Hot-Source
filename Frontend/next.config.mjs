/** @type {import('next').NextConfig} */
const backendUrl =
  process.env.NEXT_PUBLIC_API_URL || "https://hot-source-backend.vercel.app";

const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
