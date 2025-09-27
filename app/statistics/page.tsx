"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ArrowLeft, TrendingUp, BarChart3, Calendar, Target, Award, Users } from "lucide-react"
import Link from "next/link"

const monthlyStats = [
  { month: "ธ.ค. 2024", predictions: 8, correct: 6, accuracy: 75 },
  { month: "พ.ย. 2024", predictions: 8, correct: 5, accuracy: 63 },
  { month: "ต.ค. 2024", predictions: 8, correct: 7, accuracy: 88 },
  { month: "ก.ย. 2024", predictions: 8, correct: 6, accuracy: 75 },
  { month: "ส.ค. 2024", predictions: 8, correct: 4, accuracy: 50 },
  { month: "ก.ค. 2024", predictions: 8, correct: 6, accuracy: 75 },
]

const formulaPerformance = [
  {
    name: "สูตรฟีโบนัชชี",
    accuracy: 82,
    predictions: 24,
    correct: 20,
    trend: "up",
    bestMonth: "ต.ค. 2024",
    worstMonth: "ส.ค. 2024",
  },
  {
    name: "สูตรวิเคราะห์รูปแบบ",
    accuracy: 79,
    predictions: 24,
    correct: 19,
    trend: "up",
    bestMonth: "ต.ค. 2024",
    worstMonth: "ส.ค. 2024",
  },
  {
    name: "สูตรรวมเลข",
    accuracy: 75,
    predictions: 24,
    correct: 18,
    trend: "stable",
    bestMonth: "ธ.ค. 2024",
    worstMonth: "ส.ค. 2024",
  },
  {
    name: "สูตรคำนวณจากวันที่",
    accuracy: 71,
    predictions: 24,
    correct: 17,
    trend: "down",
    bestMonth: "ก.ย. 2024",
    worstMonth: "พ.ย. 2024",
  },
  {
    name: "สูตรเลขกลับ",
    accuracy: 68,
    predictions: 24,
    correct: 16,
    trend: "stable",
    bestMonth: "ต.ค. 2024",
    worstMonth: "ส.ค. 2024",
  },
  {
    name: "สูตรเลขมงคล",
    accuracy: 65,
    predictions: 24,
    correct: 16,
    trend: "up",
    bestMonth: "ธ.ค. 2024",
    worstMonth: "ส.ค. 2024",
  },
]

const numberFrequency = [
  { number: "01", frequency: 12, percentage: 8.5 },
  { number: "23", frequency: 11, percentage: 7.8 },
  { number: "45", frequency: 10, percentage: 7.1 },
  { number: "67", frequency: 9, percentage: 6.4 },
  { number: "89", frequency: 9, percentage: 6.4 },
  { number: "12", frequency: 8, percentage: 5.7 },
  { number: "34", frequency: 8, percentage: 5.7 },
  { number: "56", frequency: 7, percentage: 5.0 },
  { number: "78", frequency: 7, percentage: 5.0 },
  { number: "90", frequency: 6, percentage: 4.3 },
]

const overallStats = {
  totalPredictions: 144,
  correctPredictions: 106,
  partialPredictions: 28,
  incorrectPredictions: 10,
  averageAccuracy: 74,
  bestFormula: "สูตรฟีโบนัชชี",
  totalUsers: 25420,
  activeUsers: 8750,
}

export default function StatisticsPage() {
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
                <BarChart3 className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">สถิติและการวิเคราะห์</h1>
                <p className="text-sm text-muted-foreground">ข้อมูลเชิงลึกและประสิทธิภาพระบบ</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Overview Stats */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                  <Target className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.averageAccuracy}%</div>
                  <div className="text-sm text-muted-foreground">ความแม่นยำเฉลี่ย</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                  <Award className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.correctPredictions}</div>
                  <div className="text-sm text-muted-foreground">การทำนายที่ถูก</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                  <Calendar className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.totalPredictions}</div>
                  <div className="text-sm text-muted-foreground">งวดที่ทำนายทั้งหมด</div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-secondary/10 rounded-lg flex items-center justify-center">
                  <Users className="w-5 h-5 text-secondary-foreground" />
                </div>
                <div>
                  <div className="text-2xl font-bold text-foreground">{overallStats.totalUsers.toLocaleString()}</div>
                  <div className="text-sm text-muted-foreground">ผู้ใช้งานทั้งหมด</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="performance" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="performance">ประสิทธิภาพสูตร</TabsTrigger>
            <TabsTrigger value="monthly">สถิติรายเดือน</TabsTrigger>
            <TabsTrigger value="frequency">ความถี่เลข</TabsTrigger>
            <TabsTrigger value="trends">แนวโน้ม</TabsTrigger>
          </TabsList>

          <TabsContent value="performance" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>ประสิทธิภาพของแต่ละสูตร</CardTitle>
                <CardDescription>เปรียบเทียบความแม่นยำและประสิทธิภาพของสูตรต่างๆ</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {formulaPerformance.map((formula, index) => (
                    <div key={index} className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <h3 className="font-medium text-foreground">{formula.name}</h3>
                          <Badge
                            variant={
                              formula.trend === "up"
                                ? "default"
                                : formula.trend === "down"
                                  ? "destructive"
                                  : "secondary"
                            }
                          >
                            {formula.trend === "up" ? "เพิ่มขึ้น" : formula.trend === "down" ? "ลดลง" : "คงที่"}
                          </Badge>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-primary">{formula.accuracy}%</div>
                          <div className="text-sm text-muted-foreground">
                            {formula.correct}/{formula.predictions} งวด
                          </div>
                        </div>
                      </div>

                      <Progress value={formula.accuracy} className="h-2" />

                      <div className="grid md:grid-cols-2 gap-4 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">เดือนที่ดีที่สุด:</span>
                          <span className="font-medium">{formula.bestMonth}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">เดือนที่แย่ที่สุด:</span>
                          <span className="font-medium">{formula.worstMonth}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="monthly" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>สถิติรายเดือน</CardTitle>
                <CardDescription>ประสิทธิภาพการทำนายในแต่ละเดือน</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {monthlyStats.map((stat, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center">
                          <Calendar className="w-6 h-6 text-primary" />
                        </div>
                        <div>
                          <div className="font-medium text-foreground">{stat.month}</div>
                          <div className="text-sm text-muted-foreground">
                            ทำนาย {stat.predictions} งวด | ถูก {stat.correct} งวด
                          </div>
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

          <TabsContent value="frequency" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>ความถี่ของเลขที่ออกรางวัล</CardTitle>
                <CardDescription>เลขที่ออกบ่อยที่สุดในการทำนาย</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {numberFrequency.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-accent/10 rounded-lg flex items-center justify-center">
                            <span className="font-mono font-bold text-accent">{item.number}</span>
                          </div>
                          <div>
                            <div className="font-medium text-foreground">เลข {item.number}</div>
                            <div className="text-sm text-muted-foreground">ออก {item.frequency} ครั้ง</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-primary">{item.percentage}%</div>
                          <div className="text-sm text-muted-foreground">ของทั้งหมด</div>
                        </div>
                      </div>
                      <Progress value={item.percentage * 10} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="trends" className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>แนวโน้มความแม่นยำ</CardTitle>
                  <CardDescription>การเปลี่ยนแปลงประสิทธิภาพตลอดเวลา</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                      <div className="flex items-center gap-3">
                        <TrendingUp className="w-5 h-5 text-green-600" />
                        <div>
                          <div className="font-medium text-green-800 dark:text-green-200">แนวโน้มเพิ่มขึ้น</div>
                          <div className="text-sm text-green-600 dark:text-green-400">3 เดือนที่ผ่านมา</div>
                        </div>
                      </div>
                      <div className="text-2xl font-bold text-green-600">+5%</div>
                    </div>

                    <div className="space-y-3">
                      <h4 className="font-medium text-foreground">สูตรที่มีแนวโน้มดี</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรฟีโบนัชชี</span>
                          <Badge variant="default">+8%</Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรเลขมงคล</span>
                          <Badge variant="default">+6%</Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรวิเคราะห์รูปแบบ</span>
                          <Badge variant="default">+4%</Badge>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>การใช้งานระบบ</CardTitle>
                  <CardDescription>สถิติการใช้งานของผู้ใช้</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">ผู้ใช้งานทั้งหมด</span>
                      <span className="font-semibold">{overallStats.totalUsers.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">ผู้ใช้งานที่ใช้งานอยู่</span>
                      <span className="font-semibold text-primary">{overallStats.activeUsers.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">อัตราการใช้งาน</span>
                      <span className="font-semibold text-accent">34.4%</span>
                    </div>

                    <div className="pt-4 border-t">
                      <h4 className="font-medium text-foreground mb-3">สูตรยอดนิยม</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรฟีโบนัชชี</span>
                          <span className="font-medium">28%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรรวมเลข</span>
                          <span className="font-medium">22%</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span>สูตรวิเคราะห์รูปแบบ</span>
                          <span className="font-medium">18%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>

        {/* Summary Card */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>สรุปประสิทธิภาพระบบ</CardTitle>
            <CardDescription>ภาพรวมการทำงานของระบบคำนวณหวย</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-primary/5 rounded-lg">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Award className="w-6 h-6 text-primary" />
                </div>
                <div className="text-2xl font-bold text-primary mb-1">{overallStats.bestFormula}</div>
                <div className="text-sm text-muted-foreground">สูตรที่มีประสิทธิภาพสูงสุด</div>
              </div>

              <div className="text-center p-6 bg-accent/5 rounded-lg">
                <div className="w-12 h-12 bg-accent/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <Target className="w-6 h-6 text-accent" />
                </div>
                <div className="text-2xl font-bold text-accent mb-1">{overallStats.averageAccuracy}%</div>
                <div className="text-sm text-muted-foreground">ความแม่นยำโดยรวม</div>
              </div>

              <div className="text-center p-6 bg-secondary/5 rounded-lg">
                <div className="w-12 h-12 bg-secondary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <TrendingUp className="w-6 h-6 text-secondary-foreground" />
                </div>
                <div className="text-2xl font-bold text-secondary-foreground mb-1">+5%</div>
                <div className="text-sm text-muted-foreground">การปรับปรุงใน 3 เดือน</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
