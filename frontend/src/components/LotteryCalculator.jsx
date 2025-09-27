"use client"

import { useState } from "react"

const LotteryCalculator = () => {
  const [selectedFormula, setSelectedFormula] = useState("")
  const [inputNumbers, setInputNumbers] = useState("")
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleCalculate = async () => {
    if (!selectedFormula || !inputNumbers) return

    setLoading(true)
    try {
      const response = await fetch("/api/calculate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": window.LOTTERY_DATA.csrfToken,
        },
        body: JSON.stringify({
          formula_id: selectedFormula,
          input_numbers: inputNumbers,
        }),
      })

      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error("Error calculating:", error)
    }
    setLoading(false)
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-2xl font-bold mb-6">เครื่องคำนวณหวย</h2>

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium mb-2">เลือกสูตร</label>
          <select
            value={selectedFormula}
            onChange={(e) => setSelectedFormula(e.target.value)}
            className="w-full p-3 border rounded-lg"
          >
            <option value="">-- เลือกสูตร --</option>
            {window.LOTTERY_DATA?.formulas?.map((formula) => (
              <option key={formula.id} value={formula.id}>
                {formula.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">ใส่เลขอ้างอิง</label>
          <input
            type="text"
            value={inputNumbers}
            onChange={(e) => setInputNumbers(e.target.value)}
            placeholder="เช่น 123456"
            className="w-full p-3 border rounded-lg"
          />
        </div>
      </div>

      <button
        onClick={handleCalculate}
        disabled={loading || !selectedFormula || !inputNumbers}
        className="w-full mt-6 bg-orange-500 hover:bg-orange-600 disabled:bg-gray-300 text-white py-3 rounded-lg font-semibold"
      >
        {loading ? "กำลังคำนวณ..." : "คำนวณเลขเด็ด"}
      </button>

      {results && (
        <div className="mt-6 p-4 bg-green-50 rounded-lg">
          <h3 className="font-bold text-green-800 mb-2">ผลการคำนวณ</h3>
          <div className="grid grid-cols-3 gap-4">
            {results.calculated_numbers?.map((number, index) => (
              <div key={index} className="text-center p-3 bg-white rounded border-2 border-green-200">
                <div className="text-2xl font-bold text-green-600">{number}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default LotteryCalculator
