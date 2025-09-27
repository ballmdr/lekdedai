"use client"

import { useState, useEffect } from "react"

const FormulaDetail = ({ formulaId }) => {
  const [formula, setFormula] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (formulaId) {
      fetchFormulaDetail()
    }
  }, [formulaId])

  const fetchFormulaDetail = async () => {
    try {
      const response = await fetch(`/api/formula/${formulaId}/`)
      const data = await response.json()
      setFormula(data.formula)
      setPredictions(data.predictions)
    } catch (error) {
      console.error("Error fetching formula detail:", error)
    }
    setLoading(false)
  }

  if (loading) {
    return <div className="text-center py-8">กำลังโหลด...</div>
  }

  if (!formula) {
    return <div className="text-center py-8">ไม่พบข้อมูลสูตร</div>
  }

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">{formula.name}</h2>
        <p className="text-gray-600 mb-4">{formula.description}</p>

        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-blue-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{formula.accuracy_rate}%</div>
            <div className="text-sm text-gray-600">ความแม่นยำ</div>
          </div>
          <div className="text-center p-3 bg-green-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{formula.correct_predictions}</div>
            <div className="text-sm text-gray-600">ทำนายถูก</div>
          </div>
          <div className="text-center p-3 bg-orange-50 rounded-lg">
            <div className="text-2xl font-bold text-orange-600">{formula.total_predictions}</div>
            <div className="text-sm text-gray-600">ทำนายทั้งหมด</div>
          </div>
        </div>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-3">วิธีการคำนวณ</h3>
        <div className="bg-gray-50 p-4 rounded-lg">
          <pre className="whitespace-pre-wrap text-sm">{formula.method}</pre>
        </div>
      </div>

      {predictions.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">ประวัติการทำนาย</h3>
          <div className="space-y-2">
            {predictions.map((prediction, index) => (
              <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                <div>
                  <span className="font-medium">{prediction.predicted_numbers}</span>
                  <span className="text-sm text-gray-500 ml-2">({prediction.draw_date})</span>
                </div>
                <span
                  className={`px-2 py-1 rounded text-xs ${
                    prediction.is_correct ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"
                  }`}
                >
                  {prediction.is_correct ? "ถูก" : "ผิด"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default FormulaDetail
