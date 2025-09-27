"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Calculator, ArrowLeft, Zap, RefreshCw } from "lucide-react"
import Link from "next/link"

const calculationMethods = {
  "sum-formula": {
    name: "สูตรรวมเลข",
    calculate: (input: string) => {
      const digits = input.slice(-2).split("").map(Number)
      const sum = digits.reduce((a, b) => a + b, 0)
      const result = sum > 9 ? sum.toString().slice(-2) : sum.toString().padStart(2, "0")
      return [`${result}`, `${(Number.parseInt(result) + 22).toString().slice(-2)}`]
    },
  },
  "mirror-formula": {
    name: "สูตรเลขกลับ",
    calculate: (input: string) => {
      const lastTwo = input.slice(-2)
      const reversed = lastTwo.split("").reverse().join("")
      const base = Number.parseInt(reversed)
      return [`${reversed}`, `${(base + 11).toString().slice(-2)}`]
    },
  },
  "fibonacci-formula": {
    name: "สูตรฟีโบนัชชี",
    calculate: (input: string) => {
      const fibonacci = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
      const lastTwo = Number.parseInt(input.slice(-2))
      const index = fibonacci.findIndex((f) => f >= lastTwo)
      const next1 = fibonacci[Math.min(index + 1, fibonacci.length - 1)]
      const next2 = fibonacci[Math.min(index + 2, fibonacci.length - 1)]
      return [`${next1.toString().padStart(2, "0")}`, `${next2.toString().padStart(2, "0")}`]
    },
  },
  "pattern-formula": {
    name: "สูตรวิเคราะห์รูปแบบ",
    calculate: (input: string) => {
      const lastTwo = Number.parseInt(input.slice(-2))
      const pattern1 = (lastTwo * 1.5).toString().slice(-2)
      const pattern2 = (lastTwo * 2.1).toString().slice(-2)
      return [pattern1.padStart(2, "0"), pattern2.padStart(2, "0")]
    },
  },
  "date-formula": {
    name: "สูตรคำนวณจากวันที่",
    calculate: (input: string) => {
      const today = new Date()
      const dateSum = today.getDate() + today.getMonth() + 1 + today.getFullYear()
      const result1 = (dateSum % 100).toString().padStart(2, "0")
      const result2 = ((dateSum + Number.parseInt(input.slice(-2))) % 100).toString().padStart(2, "0")
      return [result1, result2]
    },
  },
  "lucky-number": {
    name: "สูตรเลขมงคล",
    calculate: (input: string) => {
      const luckyNumbers = [9, 18, 27, 36, 45, 54, 63, 72, 81, 90]
      const base = Number.parseInt(input.slice(-2))
      const lucky1 = luckyNumbers.find((n) => n > base) || luckyNumbers[0]
      const lucky2 = luckyNumbers.find((n) => n > lucky1) || luckyNumbers[1]
      return [`${lucky1.toString().padStart(2, "0")}`, `${lucky2.toString().padStart(2, "0")}`]
    },
  },
}

const recentDraws = [
  { date: "16/12/2024", first: "123456", twoDigit: "56", threeDigit: "456" },
  { date: "01/12/2024", first: "789012", twoDigit: "12", threeDigit: "012" },
  { date: "16/11/2024", first: "345678", twoDigit: "78", threeDigit: "678" },
  { date: "01/11/2024", first: "901234", twoDigit: "34", threeDigit: "234" },
  { date: "16/10/2024", first: "567890", twoDigit: "90", threeDigit: "890" },
]

export default function CalculatorPage() {
  const [selectedMethod, setSelectedMethod] = useState<string>("")
  const [inputNumber, setInputNumber] = useState<string>("")
  const [results, setResults] = useState<string[]>([])
  const [isCalculating, setIsCalculating] = useState(false)

  const handleCalculate = async () => {
    if (!selectedMethod || !inputNumber) return

    setIsCalculating(true)

    // Simulate calculation delay for better UX
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const method = calculationMethods[selectedMethod as keyof typeof calculationMethods]
    const calculatedResults = method.calculate(inputNumber)
    setResults(calculatedResults)
    setIsCalculating(false)
  }

  const handleReset = () => {
    setInputNumber("")
    setResults([])
    setSelectedMethod("")
  }

  const handleQuickFill = (drawNumber: string) => {
    setInputNumber(drawNumber)
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/">
                <ArrowLeft className="w-4 h-4 mr-2" />
                กลับหน้าแรก
              </Link>
            </Button>
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <Calculator className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">เครื่องคำนวณหวย</h1>
                <p className="text-sm text-muted-foreground">คำนวณเลขด้วยสูตรต่างๆ</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Calculator Section */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="w-5 h-5 text-primary" />
                  เครื่องคำนวณหวย
                </CardTitle>
                <CardDescription>เลือกสูตรและใส่เลขที่ต้องการคำนวณ</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Method Selection */}
                <div className="space-y-2">
                  <Label htmlFor="method">เลือกสูตรคำนวณ</Label>
                  <Select value={selectedMethod} onValueChange={setSelectedMethod}>
                    <SelectTrigger>
                      <SelectValue placeholder="เลือกสูตรที่ต้องการใช้" />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(calculationMethods).map(([key, method]) => (
                        <SelectItem key={key} value={key}>
                          {method.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Number Input */}
                <div className="space-y-2">
                  <Label htmlFor="number">ใส่เลขที่ต้องการคำนวณ</Label>
                  <Input
                    id="number"
                    type="text"
                    placeholder="เช่น 123456"
                    value={inputNumber}
                    onChange={(e) => setInputNumber(e.target.value.replace(/\D/g, "").slice(0, 6))}
                    className="text-center text-lg font-mono"
                  />
                  <p className="text-sm text-muted-foreground">ใส่เลขรางวัลที่ 1 หรือเลขที่ต้องการคำนวณ (สูงสุด 6 หลัก)</p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <Button
                    onClick={handleCalculate}
                    disabled={!selectedMethod || !inputNumber || isCalculating}
                    className="flex-1"
                    size="lg"
                  >
                    {isCalculating ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        กำลังคำนวณ...
                      </>
                    ) : (
                      <>
                        <Calculator className="w-4 h-4 mr-2" />
                        คำนวณเลข
                      </>
                    )}
                  </Button>
                  <Button variant="outline" onClick={handleReset} size="lg">
                    รีเซ็ต
                  </Button>
                </div>

                {/* Results */}
                {results.length > 0 && (
                  <div className="space-y-4 p-6 bg-gradient-to-r from-primary/5 to-accent/5 rounded-lg border">
                    <h3 className="text-lg font-semibold text-foreground">ผลการคำนวณ</h3>
                    <div className="grid grid-cols-2 gap-4">
                      {results.map((result, index) => (
                        <div key={index} className="text-center p-4 bg-card rounded-lg border">
                          <div className="text-sm text-muted-foreground mb-2">เลขที่ {index + 1}</div>
                          <div className="text-3xl font-mono font-bold text-primary">{result}</div>
                        </div>
                      ))}
                    </div>
                    <div className="text-center">
                      <Badge variant="secondary">
                        คำนวณด้วย: {calculationMethods[selectedMethod as keyof typeof calculationMethods]?.name}
                      </Badge>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Draws Section */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>ผลหวยย้อนหลัง</CardTitle>
                <CardDescription>งวดล่าสุด 5 งวด</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {recentDraws.map((draw, index) => (
                  <div key={index} className="p-4 border rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-muted-foreground">{draw.date}</span>
                      <Button variant="ghost" size="sm" onClick={() => handleQuickFill(draw.first)} className="text-xs">
                        ใช้เลขนี้
                      </Button>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">รางวัลที่ 1</span>
                        <span className="font-mono font-bold text-sm">{draw.first}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">2 ตัวท้าย</span>
                        <span className="font-mono font-bold text-sm text-primary">{draw.twoDigit}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-muted-foreground">3 ตัวท้าย</span>
                        <span className="font-mono font-bold text-sm text-accent">{draw.threeDigit}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Card>
              <CardHeader>
                <CardTitle>เคล็ดลับการใช้งาน</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
                  <p>ใช้เลขรางวัลที่ 1 งวดที่แล้วเป็นข้อมูลในการคำนวณ</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
                  <p>แต่ละสูตรมีวิธีการคำนวณที่แตกต่างกัน</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
                  <p>สามารถใช้เลขจากผลหวยย้อนหลังได้โดยกดปุ่ม "ใช้เลขนี้"</p>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0"></div>
                  <p>ผลการคำนวณเป็นเพียงการทำนาย ไม่รับประกันความแม่นยำ</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
