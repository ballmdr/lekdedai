import type React from "react"
import type { Metadata } from "next"
import { Work_Sans, Open_Sans } from "next/font/google"
import "./globals.css"

const workSans = Work_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-work-sans",
  weight: ["400", "600", "700"],
})

const openSans = Open_Sans({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-open-sans",
  weight: ["400", "500", "600"],
})

export const metadata: Metadata = {
  title: "เลขเด็ดเอไอ - ทำนายหวยด้วย AI",
  description: "เว็บไซต์ทำนายเลขเด็ดด้วย AI พร้อมสถิติหวยย้อนหลัง แปลความฝัน และตรวจผลสลาก",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="th" className={`${workSans.variable} ${openSans.variable} antialiased`}>
      <body className="font-sans">{children}</body>
    </html>
  )
}
