import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Search, Calendar, Trophy } from "lucide-react"
import Link from "next/link"

const lotteryHistory = [
  {
    date: "16/12/2024",
    first: "123456",
    firstNear: ["123455", "123457"],
    twoDigit: "56",
    threeDigit: "456",
    threeDigitFront: "123",
    threeDigitBack: "456",
  },
  {
    date: "01/12/2024",
    first: "789012",
    firstNear: ["789011", "789013"],
    twoDigit: "12",
    threeDigit: "012",
    threeDigitFront: "789",
    threeDigitBack: "012",
  },
  {
    date: "16/11/2024",
    first: "345678",
    firstNear: ["345677", "345679"],
    twoDigit: "78",
    threeDigit: "678",
    threeDigitFront: "345",
    threeDigitBack: "678",
  },
  {
    date: "01/11/2024",
    first: "901234",
    firstNear: ["901233", "901235"],
    twoDigit: "34",
    threeDigit: "234",
    threeDigitFront: "901",
    threeDigitBack: "234",
  },
  {
    date: "16/10/2024",
    first: "567890",
    firstNear: ["567889", "567891"],
    twoDigit: "90",
    threeDigit: "890",
    threeDigitFront: "567",
    threeDigitBack: "890",
  },
  {
    date: "01/10/2024",
    first: "246810",
    firstNear: ["246809", "246811"],
    twoDigit: "10",
    threeDigit: "810",
    threeDigitFront: "246",
    threeDigitBack: "810",
  },
  {
    date: "16/09/2024",
    first: "135792",
    firstNear: ["135791", "135793"],
    twoDigit: "92",
    threeDigit: "792",
    threeDigitFront: "135",
    threeDigitBack: "792",
  },
  {
    date: "01/09/2024",
    first: "864209",
    firstNear: ["864208", "864210"],
    twoDigit: "09",
    threeDigit: "209",
    threeDigitFront: "864",
    threeDigitBack: "209",
  },
]

export default function HistoryPage() {
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
                <Calendar className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-foreground">ประวัติการออกรางวัล</h1>
                <p className="text-sm text-muted-foreground">ผลหวยย้อนหลังทุกงวด</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Search Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="w-5 h-5" />
              ค้นหาผลหวย
            </CardTitle>
            <CardDescription>ค้นหาผลรางวัลตามวันที่หรือเลขรางวัล</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Input placeholder="ค้นหาตามวันที่ เช่น 16/12/2024" className="flex-1" />
              <Input placeholder="ค้นหาตามเลขรางวัล" className="flex-1" />
              <Button>
                <Search className="w-4 h-4 mr-2" />
                ค้นหา
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* History List */}
        <div className="space-y-6">
          {lotteryHistory.map((draw, index) => (
            <Card key={index} className="overflow-hidden">
              <CardHeader className="bg-gradient-to-r from-primary/5 to-accent/5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
                      <Trophy className="w-5 h-5 text-primary-foreground" />
                    </div>
                    <div>
                      <CardTitle className="text-lg">งวดวันที่ {draw.date}</CardTitle>
                      <CardDescription>ผลการออกรางวัลสลากกินแบ่งรัฐบาล</CardDescription>
                    </div>
                  </div>
                  <Badge variant="outline" className="bg-background">
                    งวดที่ {index + 1}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {/* รางวัลที่ 1 */}
                  <div className="text-center p-6 bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg border border-primary/20">
                    <div className="text-sm text-muted-foreground mb-2">รางวัลที่ 1</div>
                    <div className="text-3xl font-mono font-bold text-primary mb-2">{draw.first}</div>
                    <div className="text-xs text-muted-foreground">รางวัล 6,000,000 บาท</div>
                  </div>

                  {/* เลขหน้า-ท้าย 3 ตัว */}
                  <div className="space-y-4">
                    <div className="text-center p-4 bg-accent/5 rounded-lg border border-accent/20">
                      <div className="text-sm text-muted-foreground mb-2">3 ตัวหน้า</div>
                      <div className="text-2xl font-mono font-bold text-accent">{draw.threeDigitFront}</div>
                      <div className="text-xs text-muted-foreground">รางวัล 4,000 บาท</div>
                    </div>
                    <div className="text-center p-4 bg-accent/5 rounded-lg border border-accent/20">
                      <div className="text-sm text-muted-foreground mb-2">3 ตัวท้าย</div>
                      <div className="text-2xl font-mono font-bold text-accent">{draw.threeDigitBack}</div>
                      <div className="text-xs text-muted-foreground">รางวัล 4,000 บาท</div>
                    </div>
                  </div>

                  {/* เลข 2 ตัว */}
                  <div className="space-y-4">
                    <div className="text-center p-4 bg-secondary/5 rounded-lg border border-secondary/20">
                      <div className="text-sm text-muted-foreground mb-2">2 ตัวท้าย</div>
                      <div className="text-2xl font-mono font-bold text-secondary-foreground">{draw.twoDigit}</div>
                      <div className="text-xs text-muted-foreground">รางวัล 2,000 บาท</div>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-sm text-muted-foreground mb-2">เลขข้างเคียงรางวัลที่ 1</div>
                      <div className="text-lg font-mono font-bold text-foreground">{draw.firstNear.join(", ")}</div>
                      <div className="text-xs text-muted-foreground">รางวัล 100,000 บาท</div>
                    </div>
                  </div>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-3 mt-6 pt-6 border-t">
                  <Button variant="outline" size="sm">
                    ใช้เลขนี้คำนวณ
                  </Button>
                  <Button variant="outline" size="sm">
                    ดูรายละเอียดเพิ่มเติม
                  </Button>
                  <Button variant="outline" size="sm">
                    เปรียบเทียบกับการทำนาย
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Load More */}
        <div className="text-center mt-8">
          <Button variant="outline" size="lg">
            โหลดข้อมูลเพิ่มเติม
          </Button>
        </div>
      </div>
    </div>
  )
}
