import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Calculator, TrendingUp, History, Target } from "lucide-react"
import Link from "next/link"

const lotteryFormulas = [
  {
    id: "sum-formula",
    name: "สูตรรวมเลข",
    description: "คำนวณจากการรวมเลขงวดที่แล้ว",
    accuracy: "75%",
    lastResult: "23, 45",
    nextPrediction: "67, 89",
    category: "พื้นฐาน",
  },
  {
    id: "mirror-formula",
    name: "สูตรเลขกลับ",
    description: "คำนวณจากการกลับเลขงวดที่แล้ว",
    accuracy: "68%",
    lastResult: "12, 34",
    nextPrediction: "21, 43",
    category: "พื้นฐาน",
  },
  {
    id: "fibonacci-formula",
    name: "สูตรฟีโบนัชชี",
    description: "ใช้หลักคณิตศาสตร์ฟีโบนัชชี",
    accuracy: "82%",
    lastResult: "13, 21",
    nextPrediction: "34, 55",
    category: "ขั้นสูง",
  },
  {
    id: "pattern-formula",
    name: "สูตรวิเคราะห์รูปแบบ",
    description: "วิเคราะห์รูปแบบการออกรางวัล",
    accuracy: "79%",
    lastResult: "16, 28",
    nextPrediction: "39, 51",
    category: "ขั้นสูง",
  },
  {
    id: "date-formula",
    name: "สูตรคำนวณจากวันที่",
    description: "คำนวณจากวันที่ออกรางวัล",
    accuracy: "71%",
    lastResult: "07, 15",
    nextPrediction: "22, 30",
    category: "พิเศษ",
  },
  {
    id: "lucky-number",
    name: "สูตรเลขมงคล",
    description: "คำนวณจากเลขมงคลและฤกษ์ยาม",
    accuracy: "65%",
    lastResult: "09, 18",
    nextPrediction: "27, 36",
    category: "พิเศษ",
  },
]

const stats = [
  { label: "สูตรทั้งหมด", value: "12", icon: Calculator },
  { label: "ความแม่นยำเฉลี่ย", value: "73%", icon: Target },
  { label: "งวดที่วิเคราะห์", value: "500+", icon: History },
  { label: "ผู้ใช้งาน", value: "25K+", icon: TrendingUp },
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                <Calculator className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">หวยคำนวณ</h1>
                <p className="text-sm text-muted-foreground">ระบบคำนวณหวยอัจฉริยะ</p>
              </div>
            </div>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/" className="text-foreground hover:text-primary transition-colors">
                หน้าแรก
              </Link>
              <Link href="/calculator" className="text-muted-foreground hover:text-primary transition-colors">
                เครื่องคำนวณ
              </Link>
              <Link href="/results" className="text-muted-foreground hover:text-primary transition-colors">
                ผลการทำนาย
              </Link>
              <Link href="/statistics" className="text-muted-foreground hover:text-primary transition-colors">
                สถิติ
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 bg-gradient-to-br from-primary/5 via-background to-accent/5">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-3xl mx-auto">
            <h2 className="text-4xl md:text-5xl font-bold text-balance mb-6">
              ระบบคำนวณหวย
              <span className="text-primary"> อัจฉริยะ</span>
            </h2>
            <p className="text-xl text-muted-foreground text-pretty mb-8">
              ใช้เทคโนโลยีการวิเคราะห์ข้อมูลขั้นสูง เพื่อคำนวณและทำนายเลขหวยด้วยความแม่นยำสูง พร้อมสูตรคำนวณหลากหลายรูปแบบ
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="text-lg px-8" asChild>
                <Link href="/calculator">เริ่มคำนวณเลย</Link>
              </Button>
              <Button variant="outline" size="lg" className="text-lg px-8 bg-transparent" asChild>
                <Link href="#formulas">ดูสูตรทั้งหมด</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-12 bg-card/30">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-3">
                  <stat.icon className="w-6 h-6 text-primary" />
                </div>
                <div className="text-2xl font-bold text-foreground mb-1">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Formulas Section */}
      <section id="formulas" className="py-16">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12">
            <h3 className="text-3xl font-bold text-foreground mb-4">สูตรคำนวณยอดนิยม</h3>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              เลือกสูตรที่เหมาะสมกับคุณ แต่ละสูตรมีวิธีการคำนวณและความแม่นยำที่แตกต่างกัน
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {lotteryFormulas.map((formula) => (
              <Card key={formula.id} className="hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-lg mb-2">{formula.name}</CardTitle>
                      <CardDescription className="text-sm">{formula.description}</CardDescription>
                    </div>
                    <Badge
                      variant={
                        formula.category === "ขั้นสูง" ? "default" : formula.category === "พิเศษ" ? "secondary" : "outline"
                      }
                    >
                      {formula.category}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">ความแม่นยำ</span>
                      <span className="font-semibold text-accent">{formula.accuracy}</span>
                    </div>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">งวดที่แล้ว</span>
                        <span className="font-mono font-semibold">{formula.lastResult}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">ทำนายงวดหน้า</span>
                        <span className="font-mono font-semibold text-primary">{formula.nextPrediction}</span>
                      </div>
                    </div>

                    <Button asChild className="w-full">
                      <Link href={`/formula/${formula.id}`}>ดูรายละเอียด</Link>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 bg-primary/5">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-2xl mx-auto">
            <h3 className="text-3xl font-bold text-foreground mb-4">พร้อมเริ่มคำนวณหวยแล้วหรือยัง?</h3>
            <p className="text-lg text-muted-foreground mb-8">
              เลือกสูตรที่ใช่สำหรับคุณ และเริ่มต้นการคำนวณเลขหวยด้วยระบบอัจฉริยะของเรา
            </p>
            <Button size="lg" className="text-lg px-8" asChild>
              <Link href="/calculator">เริ่มคำนวณตอนนี้</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-card border-t py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                  <Calculator className="w-5 h-5 text-primary-foreground" />
                </div>
                <span className="font-bold text-foreground">หวยคำนวณ</span>
              </div>
              <p className="text-sm text-muted-foreground">
                ระบบคำนวณหวยอัจฉริยะ ที่ช่วยให้คุณวิเคราะห์และทำนายเลขหวยได้อย่างแม่นยำ
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-4">สูตรคำนวณ</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/formula/sum-formula" className="hover:text-primary transition-colors">
                    สูตรรวมเลข
                  </Link>
                </li>
                <li>
                  <Link href="/formula/mirror-formula" className="hover:text-primary transition-colors">
                    สูตรเลขกลับ
                  </Link>
                </li>
                <li>
                  <Link href="/formula/fibonacci-formula" className="hover:text-primary transition-colors">
                    สูตรฟีโบนัชชี
                  </Link>
                </li>
                <li>
                  <Link href="/formula/pattern-formula" className="hover:text-primary transition-colors">
                    สูตรวิเคราะห์รูปแบบ
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-4">เครื่องมือ</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/calculator" className="hover:text-primary transition-colors">
                    เครื่องคำนวณ
                  </Link>
                </li>
                <li>
                  <Link href="/results" className="hover:text-primary transition-colors">
                    ผลการทำนาย
                  </Link>
                </li>
                <li>
                  <Link href="/statistics" className="hover:text-primary transition-colors">
                    สถิติความแม่นยำ
                  </Link>
                </li>
                <li>
                  <Link href="/history" className="hover:text-primary transition-colors">
                    ประวัติการออกรางวัล
                  </Link>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-foreground mb-4">ข้อมูล</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li>
                  <Link href="/about" className="hover:text-primary transition-colors">
                    เกี่ยวกับเรา
                  </Link>
                </li>
                <li>
                  <Link href="/contact" className="hover:text-primary transition-colors">
                    ติดต่อเรา
                  </Link>
                </li>
                <li>
                  <Link href="/privacy" className="hover:text-primary transition-colors">
                    นโยบายความเป็นส่วนตัว
                  </Link>
                </li>
                <li>
                  <Link href="/terms" className="hover:text-primary transition-colors">
                    ข้อกำหนดการใช้งาน
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t mt-8 pt-8 text-center text-sm text-muted-foreground">
            <p>&copy; 2025 หวยคำนวณ. สงวนลิขสิทธิ์ทุกประการ</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
