"use client"

import { useState, useEffect } from "react"

const LotteryStats = () => {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchStats()
  }, [])

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/stats/")
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error("Error fetching stats:", error)
    }
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6 text-gray-800">สถิติการทำนาย</h2>

      <div className="grid md:grid-cols-3 gap-6">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className="text-3xl font-bold text-blue-600">{stats?.total_predictions || 0}</div>
          <div className="text-sm text-gray-600">การทำนายทั้งหมด</div>
        </div>

        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className="text-3xl font-bold text-green-600">{stats?.correct_predictions || 0}</div>
          <div className="text-sm text-gray-600">การทำนายที่ถูก</div>
        </div>

        <div className="text-center p-4 bg-orange-50 rounded-lg">
          <div className="text-3xl font-bold text-orange-600">
            {stats?.accuracy_rate ? `${stats.accuracy_rate.toFixed(1)}%` : "0%"}
          </div>
          <div className="text-sm text-gray-600">อัตราความแม่นยำ</div>
        </div>
      </div>

      {stats?.formula_stats && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-4">สถิติแต่ละสูตร</h3>
          <div className="space-y-3">
            {stats.formula_stats.map((formula, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <span className="font-medium">{formula.name}</span>
                <div className="flex space-x-4 text-sm">
                  <span className="text-blue-600">{formula.total} ครั้ง</span>
                  <span className="text-green-600">{formula.correct} ถูก</span>
                  <span className="text-orange-600">{formula.accuracy}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LotteryStats
