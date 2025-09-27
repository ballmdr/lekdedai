import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Calculator, TrendingUp, History, Target, ArrowLeft, CheckCircle, XCircle } from "lucide-react"
import Link from "next/link"
import { notFound } from "next/navigation"

// Mock data for lottery formulas
const formulaData = {
  "sum-formula": {
    name: "สูตรรวมเลข",
    description: "คำนวณจากการรวมเลขงวดที่แล้ว แล้วนำมาหาเลขที่มีโอกาสออกในงวดถัดไป",
    category: "พื้นฐาน",
    accuracy: "75%",
    difficulty: "ง่าย",
    howItWorks: [
      "นำเลข 2 ตัวท้ายของรางวัลที่ 1 งวดที่แล้วมารวมกัน",
      "หากผลรวมเกิน 2 หลัก ให้นำเลขหลักสุดท้าย 2 ตัวมาใช้",
      "นำผลลัพธ์ที่ได้มาคำนวณต่อด้วยสูตรเฉพาะ",
      "ได้เลขทำนายสำหรับงวดถัดไป",
    ],
    example: {
      lastDraw: "123456",
      calculation: "5 + 6 = 11 → ใช้ 11",
      result: "23, 45",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "23, 45", actual: "23, 67", correct: true },
      { date: "01/12/2024", predicted: "12, 34", actual: "15, 34", correct: false },
      { date: "16/11/2024", predicted: "67, 89", actual: "67, 91", correct: true },
      { date: "01/11/2024", predicted: "45, 78", actual: "45, 78", correct: true },
      { date: "16/10/2024", predicted: "34, 56", actual: "29, 56", correct: false },
    ],
    nextPrediction: {
      numbers: "67, 89",
      confidence: "สูง",
      basedOn: "งวดวันที่ 16/12/2024",
    },
  },
  "mirror-formula": {
    name: "สูตรเลขกลับ",
    description: "คำนวณจากการกลับเลขงวดที่แล้ว โดยใช้หลักการสะท้อนตัวเลข",
    category: "พื้นฐาน",
    accuracy: "68%",
    difficulty: "ง่าย",
    howItWorks: [
      "นำเลข 2 ตัวท้ายของรางวัลที่ 1 มากลับหลังเป็นหน้า",
      "เช่น 56 จะกลายเป็น 65",
      "นำเลขที่กลับแล้วมาคำนวณด้วยสูตรพิเศษ",
      "ได้เลขทำนายที่มีโอกาสออกสูง",
    ],
    example: {
      lastDraw: "123456",
      calculation: "56 → กลับเป็น 65",
      result: "21, 43",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "21, 43", actual: "21, 48", correct: true },
      { date: "01/12/2024", predicted: "87, 65", actual: "82, 65", correct: false },
      { date: "16/11/2024", predicted: "32, 14", actual: "32, 19", correct: true },
      { date: "01/11/2024", predicted: "76, 54", actual: "71, 54", correct: false },
      { date: "16/10/2024", predicted: "98, 21", actual: "98, 27", correct: true },
    ],
    nextPrediction: {
      numbers: "21, 43",
      confidence: "ปานกลาง",
      basedOn: "งวดวันที่ 16/12/2024",
    },
  },
  "fibonacci-formula": {
    name: "สูตรฟีโบนัชชี",
    description: "ใช้หลักคณิตศาสตร์ฟีโบนัชชี ในการคำนวณเลขที่มีโอกาสออกรางวัล",
    category: "ขั้นสูง",
    accuracy: "82%",
    difficulty: "ยาก",
    howItWorks: [
      "ใช้ลำดับฟีโบนัชชี (1, 1, 2, 3, 5, 8, 13, 21, 34, 55...)",
      "นำเลขงวดที่แล้วมาเทียบกับลำดับฟีโบนัชชี",
      "คำนวณตำแหน่งในลำดับและหาเลขถัดไป",
      "ปรับแต่งด้วยอัลกอริทึมพิเศษเพื่อความแม่นยำ",
    ],
    example: {
      lastDraw: "123413",
      calculation: "13 → ตำแหน่งที่ 7 → ถัดไป 21, 34",
      result: "34, 55",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "34, 55", actual: "34, 52", correct: true },
      { date: "01/12/2024", predicted: "21, 34", actual: "21, 34", correct: true },
      { date: "16/11/2024", predicted: "13, 21", actual: "13, 26", correct: true },
      { date: "01/11/2024", predicted: "08, 13", actual: "08, 13", correct: true },
      { date: "16/10/2024", predicted: "05, 08", actual: "07, 08", correct: false },
    ],
    nextPrediction: {
      numbers: "34, 55",
      confidence: "สูงมาก",
      basedOn: "งวดวันที่ 16/12/2024",
    },
  },
  "pattern-formula": {
    name: "สูตรวิเคราะห์รูปแบบ",
    description: "วิเคราะห์รูปแบบการออกรางวัลจากข้อมูลย้อนหลัง เพื่อหาแนวโน้มการออกรางวัล",
    category: "ขั้นสูง",
    accuracy: "79%",
    difficulty: "ปานกลาง",
    howItWorks: [
      "วิเคราะห์รูปแบบการออกรางวัลย้อนหลัง 50 งวด",
      "หาความถี่ของเลขแต่ละตัวที่ออกรางวัล",
      "คำนวณแนวโน้มและรอบการออกของแต่ละเลข",
      "สร้างการทำนายจากรูปแบบที่พบ",
    ],
    example: {
      lastDraw: "Pattern Analysis",
      calculation: "เลข 16, 28 มีแนวโน้มออกสูง",
      result: "39, 51",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "39, 51", actual: "39, 47", correct: true },
      { date: "01/12/2024", predicted: "16, 28", actual: "16, 28", correct: true },
      { date: "16/11/2024", predicted: "72, 84", actual: "75, 84", correct: false },
      { date: "01/11/2024", predicted: "63, 91", actual: "63, 95", correct: true },
      { date: "16/10/2024", predicted: "47, 59", actual: "42, 59", correct: false },
    ],
    nextPrediction: {
      numbers: "39, 51",
      confidence: "สูง",
      basedOn: "การวิเคราะห์รูปแบบ 50 งวด",
    },
  },
  "date-formula": {
    name: "สูตรคำนวณจากวันที่",
    description: "คำนวณจากวันที่ออกรางวัลและปฏิทินจันทรคติ เพื่อหาเลขมงคล",
    category: "พิเศษ",
    accuracy: "71%",
    difficulty: "ปานกลาง",
    howItWorks: [
      "ใช้วันที่ออกรางวัลเป็นฐานในการคำนวณ",
      "นำปฏิทินจันทรคติมาประกอบการคำนวณ",
      "คำนวณเลขมงคลจากวันเดือนปี",
      "ปรับแต่งด้วยตัวเลขฤกษ์ยาม",
    ],
    example: {
      lastDraw: "16/12/2024",
      calculation: "1+6+1+2+2+0+2+4 = 18 → 1+8 = 9",
      result: "22, 30",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "22, 30", actual: "22, 35", correct: true },
      { date: "01/12/2024", predicted: "07, 15", actual: "09, 15", correct: false },
      { date: "16/11/2024", predicted: "44, 52", actual: "44, 58", correct: true },
      { date: "01/11/2024", predicted: "33, 41", actual: "33, 41", correct: true },
      { date: "16/10/2024", predicted: "66, 74", actual: "61, 74", correct: false },
    ],
    nextPrediction: {
      numbers: "22, 30",
      confidence: "ปานกลาง",
      basedOn: "วันที่ 01/01/2025",
    },
  },
  "lucky-number": {
    name: "สูตรเลขมงคล",
    description: "คำนวณจากเลขมงคลและฤกษ์ยาม ตามหลักโหราศาสตร์ไทย",
    category: "พิเศษ",
    accuracy: "65%",
    difficulty: "ง่าย",
    howItWorks: [
      "ใช้เลขมงคลตามวันเกิดและราศี",
      "คำนวณจากฤกษ์ยามที่เป็นมงคล",
      "นำตัวเลขจากคำทำนายโหราศาสตร์มาประกอบ",
      "สร้างเลขที่เป็นมงคลสำหรับแต่ละบุคคล",
    ],
    example: {
      lastDraw: "Lucky Numbers",
      calculation: "ราศีมีน + ฤกษ์ยามดี = เลขมงคล",
      result: "27, 36",
    },
    historicalData: [
      { date: "16/12/2024", predicted: "27, 36", actual: "27, 31", correct: true },
      { date: "01/12/2024", predicted: "09, 18", actual: "12, 18", correct: false },
      { date: "16/11/2024", predicted: "54, 63", actual: "54, 68", correct: true },
      { date: "01/11/2024", predicted: "81, 90", actual: "85, 90", correct: false },
      { date: "16/10/2024", predicted: "72, 81", actual: "72, 86", correct: true },
    ],
    nextPrediction: {
      numbers: "27, 36",
      confidence: "ปานกลาง",
      basedOn: "ฤกษ์ยามมงคล",
    },
  },
}

interface FormulaPageProps {
  params: {
    id: string
  }
}

export default function FormulaPage({ params }: FormulaPageProps) {
  const formula = formulaData[params.id as keyof typeof formulaData]

  if (!formula) {
    notFound()
  }

  const correctPredictions = formula.historicalData.filter((item) => item.correct).length
  const totalPredictions = formula.historicalData.length
  const accuracyRate = Math.round((correctPredictions / totalPredictions) * 100)

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
                <h1 className="text-lg font-bold text-foreground">{formula.name}</h1>
                <p className="text-sm text-muted-foreground">รายละเอียดสูตรคำนวณ</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Formula Overview */}
        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h2 className="text-3xl font-bold text-foreground mb-2">{formula.name}</h2>
              <p className="text-lg text-muted-foreground max-w-3xl">{formula.description}</p>
            </div>
            <div className="flex gap-2">
              <Badge
                variant={
                  formula.category === "ขั้นสูง" ? "default" : formula.category === "พิเศษ" ? "secondary" : "outline"
                }
              >
                {formula.category}
              </Badge>
              <Badge variant="outline">{formula.difficulty}</Badge>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid md:grid-cols-3 gap-4 mb-8">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                    <Target className="w-5 h-5 text-accent" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-foreground">{formula.accuracy}</div>
                    <div className="text-sm text-muted-foreground">ความแม่นยำ</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-foreground">{accuracyRate}%</div>
                    <div className="text-sm text-muted-foreground">อัตราความสำเร็จ</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-secondary/10 rounded-lg flex items-center justify-center">
                    <History className="w-5 h-5 text-secondary-foreground" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-foreground">{totalPredictions}</div>
                    <div className="text-sm text-muted-foreground">งวดที่ทำนาย</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Tabs Content */}
        <Tabs defaultValue="how-it-works" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="how-it-works">วิธีการคำนวณ</TabsTrigger>
            <TabsTrigger value="example">ตัวอย่างการใช้งาน</TabsTrigger>
            <TabsTrigger value="history">ผลย้อนหลัง</TabsTrigger>
            <TabsTrigger value="prediction">ทำนายงวดหน้า</TabsTrigger>
          </TabsList>

          <TabsContent value="how-it-works">
            <Card>
              <CardHeader>
                <CardTitle>วิธีการคำนวณ</CardTitle>
                <CardDescription>ขั้นตอนการคำนวณของสูตรนี้</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {formula.howItWorks.map((step, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-semibold text-sm">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <p className="text-foreground">{step}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="example">
            <Card>
              <CardHeader>
                <CardTitle>ตัวอย่างการใช้งาน</CardTitle>
                <CardDescription>ดูตัวอย่างการคำนวณจริง</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  <div className="grid md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-2">งวดที่แล้ว</div>
                      <div className="text-xl font-mono font-bold text-foreground">{formula.example.lastDraw}</div>
                    </div>
                    <div className="text-center p-4 bg-primary/5 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-2">การคำนวณ</div>
                      <div className="text-lg font-semibold text-primary">{formula.example.calculation}</div>
                    </div>
                    <div className="text-center p-4 bg-accent/5 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-2">ผลลัพธ์</div>
                      <div className="text-xl font-mono font-bold text-accent">{formula.example.result}</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="history">
            <Card>
              <CardHeader>
                <CardTitle>ผลการทำนายย้อนหลัง</CardTitle>
                <CardDescription>ประวัติการทำนายและความแม่นยำ</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {formula.historicalData.map((item, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="text-sm text-muted-foreground w-20">{item.date}</div>
                        <div className="flex items-center gap-4">
                          <div>
                            <div className="text-sm text-muted-foreground">ทำนาย</div>
                            <div className="font-mono font-semibold">{item.predicted}</div>
                          </div>
                          <div>
                            <div className="text-sm text-muted-foreground">ออกจริง</div>
                            <div className="font-mono font-semibold">{item.actual}</div>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        {item.correct ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : (
                          <XCircle className="w-5 h-5 text-red-500" />
                        )}
                        <span className={`text-sm font-medium ${item.correct ? "text-green-600" : "text-red-600"}`}>
                          {item.correct ? "ถูก" : "ผิด"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="prediction">
            <Card>
              <CardHeader>
                <CardTitle>ทำนายงวดหน้า</CardTitle>
                <CardDescription>เลขที่คาดว่าจะออกในงวดถัดไป</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center space-y-6">
                  <div className="inline-flex items-center gap-4 p-6 bg-gradient-to-r from-primary/10 to-accent/10 rounded-xl">
                    <div>
                      <div className="text-sm text-muted-foreground mb-2">เลขทำนาย</div>
                      <div className="text-4xl font-mono font-bold text-primary">{formula.nextPrediction.numbers}</div>
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4 max-w-md mx-auto">
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-1">ความมั่นใจ</div>
                      <div className="font-semibold text-foreground">{formula.nextPrediction.confidence}</div>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-1">อิงจาก</div>
                      <div className="font-semibold text-foreground">{formula.nextPrediction.basedOn}</div>
                    </div>
                  </div>

                  <div className="max-w-md mx-auto">
                    <Button className="w-full" size="lg">
                      บันทึกเลขทำนาย
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
