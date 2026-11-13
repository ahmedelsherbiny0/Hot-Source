import type { Metadata } from "next";
import "./globals.css";
import "leaflet/dist/leaflet.css";

export const metadata: Metadata = {
  title: "Trend Detective | NASA Earth Observation Analytics",
  description:
    "AI-augmented statistical trend detection, autocorrelation correction, and physical driver attribution for NASA Earth science datasets.",
  keywords: [
    "NASA",
    "Earth Science",
    "GLDAS",
    "Mann-Kendall",
    "Hamed-Rao",
    "Theil-Sen",
    "Climate Trends",
    "MODIS",
    "NOAA",
  ],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        {children}
      </body>
    </html>
  );
}
