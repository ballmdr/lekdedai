import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import "./globals.css"
import { Suspense } from "react"
import Navigation from "../components/navigation"

export const metadata: Metadata = {
  title: "หวยคำนวณ - ระบบคำนวณหวยอัจฉริยะ",
  description: "ระบบคำนวณหวยอัจฉริยะ ที่ช่วยให้คุณวิเคราะห์และทำนายเลขหวยได้อย่างแม่นยำ",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <Suspense>
          <Navigation />
          <main className="min-h-screen bg-gray-50">{children}</main>
          <Analytics />
        </Suspense>
      </body>
    </html>
  )
}
