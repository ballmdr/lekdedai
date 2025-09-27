"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ArrowLeft, TrendingUp, CheckCircle, XCircle, Calendar, Target } from "lucide-react"
import Link from "next/link"

const predictionResults = [
  {
    date: "16/12/2024",
    formula: "สูตรฟีโบนัชชี",
    predicted: ["34", "55"],
    actual: ["34", "52"],
    status: "partial", // correct, incorrect, partial
    accuracy: 50,
  },
  {
    date: "01/12/2024",
    formula: "สูตรรวมเลข",
    predicted: ["23", "45"],
    actual: ["23", "67"],
    status: "partial",
    accuracy: 50,
  },
  {
    date: "16/11/2024",
    formula: "สูตรวิเคราะห์รูปแบบ",
    predicted: ["39", "51"],
    actual: ["39", "47"],
    status: "partial",
    accuracy: 50,
  },
  {
    date: "01/11/2024",
    formula: "สูตรเลขกลับ",
    predicted: ["21", "43"],
    actual: ["21", "43"],
    status: "correct",
    accuracy: 100,
  },
  {
    date: "16/10/2024",
    formula: "สูตรคำนวณจากวันที่",
    predicted: ["22", "30"],
    actual: ["18", "25"],
    status: "incorrect",
    accuracy: 0,
  },
  {
    date: "01/10/2024",
    formula: "สูตรเลขมงคล",
    predicted: ["27", "36"],
    actual: ["27", "31"],
    status: "partial",
    accuracy: 50,
  },
]

const formulaStats = [
  { name: "สูตรฟีโบนัชชี", accuracy: 82, predictions: 15, correct: 12 },
  { name: "สูตรวิเคราะห์รูปแบบ", accuracy: 79, predictions: 18, correct: 14 },
  { name: "สูตรรวมเลข", accuracy: 75, predictions: 20, correct: 15 },
  { name: "สูตรคำนวณจากวันที่", accuracy: 71, predictions: 12, correct: 8 },
  { name: "สูตรเลขกลับ", accuracy: 68, predictions: 16, correct: 11 },
  { name: "สูตรเลขมงคล", accuracy: 65, predictions: 10, correct: 6 },
]

export default function ResultsPage() {
  const [selectedFormula, setSelectedFormula] = useState<string>("all")
  const [selectedPeriod, setSelectedPeriod] = useState<string>("3months")

  const filteredResults = predictionResults.filter(
    (result) => selectedFormula === "all" || result.formula === selectedFormula,
  )

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "correct":
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case "incorrect":
        return <XCircle className="w-5 h-5 text-red-500" />
      case "partial":
        return <Target className="w-5 h-5 text-yellow-500" />
      default:
        return null
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case "correct":
        return "ถูกทั้งหมด"
      case "incorrect":
        return "ผิดทั้งหมด"
      case "partial":
        return "ถูกบางส่วน"
      default:
        return ""
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "correct":
        return "text-green-600"
      case "incorrect":
        return "text-red-600"
      case "partial":
        return "text-yellow-600"
      default:
        return ""
    }
  }

  const overallStats = {
    totalPredictions: predictionResults.length,
    correctPredictions: predictionResults.filter((r) => r.status === "correct").length,
    partialPredictions: predictionResults.filter((r) => r.status === "partial").length,
    averageAccuracy: Math.round(predictionResults.reduce((sum, r) => sum + r.accuracy, 0) / predictionResults.length),
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
                <TrendingUp className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">ผลการทำนาย</h1>
                <p className="text-sm text-muted-foreground">สถิติและผลลัพธ์การทำนาย</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Overall Stats */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.totalPredictions}</div>
                  <div className="text-sm text-muted-foreground">งวดที่ทำนาย</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.correctPredictions}</div>
                  <div className="text-sm text-muted-foreground">ถูกทั้งหมด</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-yellow-500/10 rounded-lg flex items-center justify-center">
                  <Target className="w-5 h-5 text-yellow-500" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.partialPredictions}</div>
                  <div className="text-sm text-muted-foreground">ถูกบางส่วน</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.averageAccuracy}%</div>
                  <div className="text-sm text-muted-foreground">ความแม่นยำเฉลี่ย</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="results" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="results">ผลการทำนาย</TabsTrigger>
            <TabsTrigger value="statistics">สถิติสูตร</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="space-y-6">
            {/* Filters */}
            <Card>
              <CardHeader>
                <CardTitle>กรองข้อมูล</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">เลือกสูตร</label>
                    <Select value={selectedFormula} onValueChange={setSelectedFormula}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">ทุกสูตร</SelectItem>
                        <SelectItem value="สูตรฟีโบนัชชี">สูตรฟีโบนัชชี</SelectItem>
                        <SelectItem value="สูตรรวมเลข">สูตรรวมเลข</SelectItem>
                        <SelectItem value="สูตรเลขกลับ">สูตรเลขกลับ</SelectItem>
                        <SelectItem value="สูตรวิเคราะห์รูปแบบ">สูตรวิเคราะห์รูปแบบ</SelectItem>
                        <SelectItem value="สูตรคำนวณจากวันที่">สูตรคำนวณจากวันที่</SelectItem>
                        <SelectItem value="สูตรเลขมงคล">สูตรเลขมงคล</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">ช่วงเวลา</label>
                    <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1month">1 เดือนที่ผ่านมา</SelectItem>
                        <SelectItem value="3months">3 เดือนที่ผ่านมา</SelectItem>
                        <SelectItem value="6months">6 เดือนที่ผ่านมา</SelectItem>
                        <SelectItem value="1year">1 ปีที่ผ่านมา</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Results List */}
            <div className="space-y-4">
              {filteredResults.map((result, index) => (
                <Card key={index}>
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-sm text-muted-foreground">{result.date}</div>
                        <Badge variant="outline">{result.formula}</Badge>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(result.status)}
                        <span className={`text-sm font-medium ${getStatusColor(result.status)}`}>
                          {getStatusText(result.status)}
                        </span>
                      </div>
                    </div>

                    <div className="grid md:grid-cols-3 gap-4">
                      <div className="text-center p-4 bg-muted/50 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-2">เลขทำนาย</div>
                        <div className="text-lg font-mono font-bold text-foreground">{result.predicted.join(", ")}</div>
                      </div>
                      <div className="text-center p-4 bg-primary/5 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-2">เลขที่ออก</div>
                        <div className="text-lg font-mono font-bold text-primary">{result.actual.join(", ")}</div>
                      </div>
                      <div className="text-center p-4 bg-accent/5 rounded-lg">
                        <div className="text-sm text-muted-foreground mb-2">ความแม่นยำ</div>
                        <div className="text-lg font-bold text-accent">{result.accuracy}%</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="statistics" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>สถิติความแม่นยำของแต่ละสูตร</CardTitle>
                <CardDescription>เปรียบเทียบประสิทธิภาพของสูตรต่างๆ</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {formulaStats.map((stat, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-medium text-foreground mb-1">{stat.name}</div>
                        <div className="text-sm text-muted-foreground">
                          ทำนาย {stat.predictions} งวด | ถูก {stat.correct} งวด
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-primary">{stat.accuracy}%</div>
                        <div className="text-sm text-muted-foreground">ความแม่นยำ</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
