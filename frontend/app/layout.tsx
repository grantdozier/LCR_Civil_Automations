import type { Metadata } from "next"
import "./globals.css"
import { Navigation } from "@/components/navigation"

export const metadata: Metadata = {
  title: "LCR Civil Drainage Automation",
  description: "Production-ready civil engineering automation platform for drainage analysis, regulatory compliance, and document generation",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans">
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
          <Navigation />
          {children}
        </div>
      </body>
    </html>
  )
}
