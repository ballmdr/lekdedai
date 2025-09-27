"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Calculator, BarChart3, History, Home, TrendingUp } from "lucide-react"

const navItems = [
  { href: "/", label: "หน้าแรก", icon: Home },
  { href: "/calculator", label: "คำนวณ", icon: Calculator },
  { href: "/results", label: "ผลการทำนาย", icon: TrendingUp },
  { href: "/statistics", label: "สถิติ", icon: BarChart3 },
  { href: "/history", label: "ประวัติ", icon: History },
]

export default function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-amber-500 to-orange-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">หวย</span>
              </div>
              <span className="font-bold text-xl text-gray-900">สูตรคำนวณหวย</span>
            </Link>
          </div>

          <div className="hidden md:flex items-center space-x-8">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? "text-amber-600 bg-amber-50" : "text-gray-600 hover:text-amber-600 hover:bg-amber-50"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              )
            })}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button className="text-gray-600 hover:text-gray-900 p-2">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
